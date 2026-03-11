from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
import json
import os
import re
from datetime import datetime

from app.models import (
    DocumentType, DocumentMetadata, DocumentUpload,
    QueryRequest, QueryResponse, DocumentInfo,
    QueryMode, CorrectionRequest
)
from app.vector_store import vector_store
from app.pdf_processor import extract_text_from_bytes
from app.llm_service import llm_service
from app.memory_manager import memory_manager
from app.memory_summarizer import memory_summarizer
from app.memory_config import MemoryType, MemoryImportance

# 导入模式处理模块
from judger.api.modes import (
    QueryMode as ModeEnum,
    detect_mode_from_query,
    parse_correction_query,
    CorrectionRecord
)

app = FastAPI(
    title="卡牌游戏智能裁判",
    description="基于规则手册、官方裁定和判例的问答系统（支持提问/纠错双模式）",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/", include_in_schema=False)
async def index():
    """返回前端页面"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/documents/upload", summary="上传文档（PDF/TXT/JSON）")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocumentType = Form(...),
    title: str = Form(...),
    version: Optional[str] = Form(None),
    effective_date: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    tags: Optional[str] = Form("")  # 逗号分隔
):
    """
    上传文档到知识库，支持 PDF、TXT、JSON 格式
    
    - doc_type: rule(规则), ruling(官方裁定), case(判例)
    - tags: 用逗号分隔的标签，如 "战斗，召唤，效果"
    
    JSON 格式支持：
    - 术语对照表格式：{"category": {"日文": "中文", ...}}
    - 简单键值对：{"原文": "翻译", ...}
    - 数组格式：[{"field": "value"}, ...]
    """
    content = await file.read()
    text = extract_text_from_bytes(content, file.filename)
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="无法从文件中提取文本")
    
    metadata = DocumentMetadata(
        doc_type=doc_type,
        title=title,
        version=version,
        effective_date=effective_date,
        source=source,
        tags=[t.strip() for t in tags.split(",") if t.strip()]
    )
    
    result = vector_store.add_document(text, metadata)
    return {"status": "success", "data": result}


@app.post("/documents/text", summary="直接添加文本内容")
async def add_text_document(doc: DocumentUpload):
    """
    直接添加文本内容到知识库，适合添加单条裁定或判例
    
    示例请求体：
    ```json
    {
        "metadata": {
            "doc_type": "ruling",
            "title": "关于 XXX 卡牌效果的裁定",
            "effective_date": "2024-01-15",
            "tags": ["效果", "连锁"]
        },
        "content": "问：当 XXX 效果发动时...答：根据规则..."
    }
    ```
    """
    if not doc.content:
        raise HTTPException(status_code=400, detail="content 不能为空")
    
    result = vector_store.add_document(doc.content, doc.metadata)
    return {"status": "success", "data": result}


# ==================== 模式分离 API ====================

@app.post("/judge", response_model=QueryResponse, summary="统一查询接口（自动检测模式）")
async def judge_auto(request: QueryRequest):
    """
    统一查询接口 - 自动检测模式
    
    - question: 你的问题（可带前缀如 [纠错] xxx）
    - mode: AUTO（自动检测）/ QUESTION / CORRECTION
    - doc_types: 可选，限定搜索范围 ["rule", "ruling", "case"]
    - top_k: 检索的参考文档数量
    
    模式检测优先级：
    1. API 参数 mode（如果明确指定）
    2. 消息前缀检测（[纠错]/[提问] 等）
    3. 默认提问模式
    """
    from app.query_processor import query_processor
    
    # 1. 确定模式
    mode = request.mode
    question = request.question
    
    if mode == QueryMode.AUTO:
        # 自动检测：检查前缀
        detected_mode, cleaned_question = detect_mode_from_query(question)
        mode = detected_mode
        question = cleaned_question
    
    # 2. 根据模式分发处理
    if mode == QueryMode.CORRECTION:
        return await _handle_correction_api(question, request.context)
    else:
        # 提问模式 - 使用原有逻辑
        return await _handle_question_api(question, request.doc_types, request.top_k)


@app.post("/judge/question", response_model=QueryResponse, summary="提问接口")
async def judge_question(request: QueryRequest):
    """
    提问模式接口 - 正常卡牌/规则查询
    
    - question: 你的问题
    - doc_types: 可选，限定搜索范围
    - top_k: 检索的参考文档数量
    - context: 可选，上下文信息
    """
    # 强制使用提问模式（清理可能的前缀）
    _, cleaned_question = detect_mode_from_query(request.question)
    
    return await _handle_question_api(cleaned_question, request.doc_types, request.top_k, request.context)


@app.post("/judge/correction", response_model=QueryResponse, summary="纠错接口")
async def judge_correction(request: CorrectionRequest):
    """
    纠错模式接口 - 对已有裁定/答案进行纠正
    
    - query: 纠错内容
    - original_answer_id: 可选，被纠正的答案 ID
    - reference: 可选，引用依据（规则章节等）
    - corrector_id: 可选，纠正者 ID
    
    返回包含纠错记录和建议
    """
    return await _handle_correction_api(
        request.query,
        {
            "original_answer_id": request.original_answer_id,
            "reference": request.reference,
            "corrector_id": request.corrector_id
        }
    )


async def _handle_question_api(question: str, doc_types: Optional[List[DocumentType]] = None, 
                                top_k: int = 5, context: Optional[dict] = None) -> QueryResponse:
    """处理提问模式请求"""
    from app.query_processor import query_processor
    
    # 1. 首先搜索记忆
    memory_results = []
    if memory_manager.config.enable_memory_search:
        print("[记忆] 🧠 搜索相关记忆...")
        memory_results = memory_manager.search_memories(
            query=question,
            top_k=3
        )
        if memory_results:
            print(f"[记忆] ✅ 找到 {len(memory_results)} 条相关记忆")
    
    card_docs = []  # 卡牌数据（直接显示）
    rule_docs_list = []  # 规则数据（给 LLM 分析）
    seen_contents = set()
    
    # 1. 优先提取卡牌编号并精确检索
    card_numbers = query_processor.extract_card_numbers(question)
    if card_numbers:
        print(f"[检索] 🎴 发现卡牌编号：{card_numbers}")
        for card_no in card_numbers:
            # 精确搜索卡牌数据
            results = vector_store.search_by_card_number(card_no, translate_result=True)
            print(f"[检索] 📋 {card_no} 找到 {len(results)} 条卡牌数据")
            for doc in results:
                content_hash = hash(doc["content"][:100])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    card_docs.append(doc)
            
            # 同时搜索与该卡牌相关的裁定和判例
            card_related_results = vector_store.search(
                query=f"卡牌编号 {card_no}",
                doc_types=[DocumentType.RULING, DocumentType.CASE],
                top_k=3,
                translate_result=True
            )
            print(f"[检索] 📖 {card_no} 找到 {len(card_related_results)} 条相关裁定/判例")
            for doc in card_related_results:
                content_hash = hash(doc["content"][:100])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    rule_docs_list.append(doc)
    
    # 2. 对原始问题进行语义检索（规则相关）
    print(f"[检索] 🔍 语义搜索：{question[:50]}...")
    rule_results = vector_store.search(
        query=question,
        doc_types=doc_types,
        top_k=top_k,
        translate_result=True
    )
    print(f"[检索] 📚 找到 {len(rule_results)} 条规则文档")
    for doc in rule_results:
        content_hash = hash(doc["content"][:100])
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            rule_docs_list.append(doc)
    
    # 3. 构建给 LLM 的上下文（包含记忆、卡牌效果和规则）
    all_docs_for_llm = []
    
    # 优先添加记忆（已验证的知识）
    if memory_results:
        print(f"[上下文] 🧠 添加 {len(memory_results)} 条记忆到上下文")
        for mem in memory_results:
            all_docs_for_llm.append({
                "content": f"【已验证记忆】\n问题：{mem['question']}\n答案：{mem['answer']}\n总结：{mem['summary']}",
                "metadata": {"title": "已验证记忆", "source": "memory"},
                "doc_type": "memory"
            })
    
    # 添加卡牌效果（如果有）
    if card_docs:
        print(f"[上下文] 📝 添加 {len(card_docs)} 张卡牌效果到上下文")
        for card_doc in card_docs:
            all_docs_for_llm.append({
                "content": card_doc["content"],
                "metadata": card_doc["metadata"],
                "doc_type": "card"
            })
    
    # 再添加规则文档
    all_docs_for_llm.extend(rule_docs_list)
    
    if not card_docs and not rule_docs_list:
        return QueryResponse(
            answer="抱歉，我在知识库中没有找到与您问题相关的信息。",
            sources=[],
            cards=[],
            mode="question"
        )
    
    # LLM 只做规则分析（不传卡牌数据，避免它编造效果）
    if all_docs_for_llm:
        answer = llm_service.generate_answer(question, all_docs_for_llm)
    else:
        answer = "已找到相关卡牌数据（见上方）。如需规则裁定分析，请确保已导入规则文档。"
    
    # 卡牌数据直接返回（前端直接显示，不依赖 LLM）
    cards = [
        {
            "card_no": doc["metadata"].get("card_no", doc["metadata"].get("title", "")),
            "title": doc["metadata"].get("title", ""),
            "content": doc["content"]
        }
        for doc in card_docs
    ]
    
    # 规则来源
    sources = [
        {
            "title": doc["metadata"].get("title", ""),
            "doc_type": doc.get("doc_type", ""),
            "excerpt": doc["content"][:300] + "..." if len(doc["content"]) > 300 else doc["content"]
        }
        for doc in rule_docs_list
    ]
    
    # 返回结果
    return QueryResponse(
        answer=answer,
        sources=sources,
        cards=cards,
        mode="question"
    )


async def _handle_correction_api(query: str, context: Optional[dict] = None) -> QueryResponse:
    """处理纠错模式请求"""
    # 解析纠错查询
    parsed = parse_correction_query(query)
    
    # 构建纠错记录
    correction_record = CorrectionRecord(
        original_query=query,
        correction=parsed.get("correction_content", query),
        corrected_by=context.get("corrector_id") if context else None,
        timestamp=datetime.now(),
        status="pending_review",
        reference=context.get("reference") if context else None,
        original_answer_id=context.get("original_answer_id") if context else None
    )
    
    # 与参考数据对比验证
    reference_match = {}
    
    if parsed.get("target_card"):
        # 搜索卡牌数据
        results = vector_store.search_by_card_number(parsed["target_card"], translate_result=True)
        if results:
            reference_match["card_found"] = True
            reference_match["card_info"] = {
                "card_no": results[0]["metadata"].get("card_no"),
                "title": results[0]["metadata"].get("title"),
                "effect_excerpt": results[0]["content"][:200]
            }
    
    if parsed.get("target_rule"):
        # 搜索规则
        rule_results = vector_store.search(
            query=parsed["target_rule"],
            doc_types=[DocumentType.RULE],
            top_k=1,
            translate_result=True
        )
        if rule_results:
            reference_match["rule_found"] = True
            reference_match["rule_content"] = rule_results[0]["content"][:300]
    
    # 生成纠正报告/建议
    suggestion = _generate_correction_suggestion(parsed, reference_match)
    
    # 构建回答
    answer = f"## 纠错报告\n\n"
    answer += f"**纠正内容**: {parsed.get('correction_content', query)}\n\n"
    
    if parsed.get("target_card"):
        answer += f"**涉及卡牌**: {parsed['target_card']}\n"
    if parsed.get("target_rule"):
        answer += f"**涉及规则**: {parsed['target_rule']}\n"
    
    answer += f"\n**状态**: 待审核\n\n"
    answer += f"**建议**: {suggestion}\n"
    
    return QueryResponse(
        answer=answer,
        sources=[],
        cards=[],
        mode="correction",
        correction_record={
            "original_query": query,
            "correction": parsed.get("correction_content", query),
            "target_card": parsed.get("target_card"),
            "target_rule": parsed.get("target_rule"),
            "timestamp": correction_record.timestamp.isoformat(),
            "status": correction_record.status
        }
    )


def _generate_correction_suggestion(parsed: dict, reference_match: dict) -> str:
    """生成纠正建议"""
    suggestions = []
    
    if reference_match:
        suggestions.append("已找到相关参考数据，建议核对后更新裁定")
    else:
        suggestions.append("未找到直接参考数据，建议人工审核")
    
    if parsed.get("target_card"):
        suggestions.append(f"涉及卡牌：{parsed['target_card']}")
    
    if parsed.get("target_rule"):
        suggestions.append(f"涉及规则：{parsed['target_rule']}")
    
    return "；".join(suggestions)


# ==================== 原有 API（保持兼容） ====================

@app.post("/query", response_model=QueryResponse, summary="提问（旧接口，兼容用）")
async def query(request: QueryRequest):
    """
    向智能裁判提问（旧接口，建议使用 /judge/question）
    
    - question: 你的问题
    - doc_types: 可选，限定搜索范围 ["rule", "ruling", "case"]
    - top_k: 检索的参考文档数量
    """
    return await _handle_question_api(request.question, request.doc_types, request.top_k)


@app.get("/documents", summary="列出所有文档")
async def list_documents(doc_type: Optional[DocumentType] = None):
    """获取知识库中的所有文档列表"""
    docs = vector_store.list_documents(doc_type)
    return {"status": "success", "data": docs, "total": len(docs)}


@app.delete("/documents/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str, doc_type: DocumentType):
    """
    删除指定文档
    
    - doc_id: 文档 ID（上传时返回）
    - doc_type: 文档类型
    """
    success = vector_store.delete_document(doc_id, doc_type)
    if success:
        return {"status": "success", "message": f"文档 {doc_id} 已删除"}
    raise HTTPException(status_code=404, detail="文档不存在")


@app.post("/documents/batch", summary="批量添加裁定/判例")
async def batch_add_documents(documents: List[DocumentUpload]):
    """
    批量添加多条裁定或判例
    
    适合一次性导入多条官方裁定
    """
    results = []
    for doc in documents:
        if doc.content:
            result = vector_store.add_document(doc.content, doc.metadata)
            results.append(result)
    
    return {
        "status": "success",
        "added": len(results),
        "data": results
    }


# ==================== 记忆管理 API ====================

@app.post("/memory/save", summary="保存问答为记忆")
async def save_memory(
    question: str = Form(...),
    answer: str = Form(...),
    user_confirmed: bool = Form(True),
    importance: int = Form(2),  # 1-4
    tags: Optional[str] = Form("")
):
    """
    保存问答对为长期记忆
    
    - question: 问题
    - answer: 答案
    - user_confirmed: 用户是否确认正确
    - importance: 重要性 (1=低，2=中，3=高，4=关键)
    - tags: 标签，逗号分隔
    """
    try:
        # 生成总结
        print("🤔 正在生成记忆总结...")
        summary = memory_summarizer.summarize(question, answer)
        
        # 保存记忆
        memory = memory_manager.add_memory(
            question=question,
            answer=answer,
            summary=summary,
            memory_type=MemoryType.LONG_TERM,
            importance=MemoryImportance(importance),
            tags=[t.strip() for t in tags.split(",") if t.strip()],
            user_confirmed=user_confirmed
        )
        
        return {
            "status": "success",
            "message": "记忆已保存",
            "data": {
                "memory_id": memory.id,
                "summary": summary
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存记忆失败：{str(e)}")


@app.get("/memory/search", summary="搜索记忆")
async def search_memory(
    query: str,
    top_k: int = 5
):
    """搜索相关记忆"""
    memories = memory_manager.search_memories(query, top_k=top_k)
    return {
        "status": "success",
        "data": memories,
        "total": len(memories)
    }


@app.get("/memory/{memory_id}", summary="获取记忆详情")
async def get_memory(memory_id: str):
    """获取完整记忆信息"""
    memory = memory_manager.get_memory(memory_id)
    if memory:
        return {"status": "success", "data": memory}
    raise HTTPException(status_code=404, detail="记忆不存在")


@app.post("/memory/{memory_id}/feedback", summary="更新记忆反馈")
async def update_memory_feedback(
    memory_id: str,
    confirmed: bool = Form(...),
    feedback: Optional[str] = Form(None)
):
    """
    更新记忆的用户反馈
    
    - confirmed: 是否确认正确
    - feedback: 反馈意见（可选）
    """
    success = memory_manager.update_memory_feedback(
        memory_id, confirmed, feedback
    )
    if success:
        return {"status": "success", "message": "反馈已更新"}
    raise HTTPException(status_code=500, detail="更新失败")


@app.delete("/memory/{memory_id}", summary="删除记忆")
async def delete_memory(memory_id: str):
    """删除指定记忆"""
    success = memory_manager.delete_memory(memory_id)
    if success:
        return {"status": "success", "message": "记忆已删除"}
    raise HTTPException(status_code=500, detail="删除失败")


@app.get("/memory/stats", summary="获取记忆统计")
async def get_memory_stats():
    """获取记忆系统统计信息"""
    stats = memory_manager.get_statistics()
    return {"status": "success", "data": stats}
