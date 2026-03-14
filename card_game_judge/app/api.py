from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, List
import json
import os

from app.models import (
    DocumentType, DocumentMetadata, DocumentUpload,
    QueryRequest, QueryResponse, DocumentInfo
)
from app.vector_store import vector_store
from app.pdf_processor import extract_text_from_bytes
from app.llm_service import llm_service
from app.memory_manager import memory_manager
from app.memory_summarizer import memory_summarizer
from app.memory_config import MemoryType, MemoryImportance

app = FastAPI(
    title="卡牌游戏智能裁判",
    description="基于规则手册、官方裁定和判例的问答系统",
    version="1.0.0"
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
    """返回前端页面 (增强版，支持图片识别)"""
    # 优先使用增强版页面
    enhanced_page = os.path.join(STATIC_DIR, "index_with_image.html")
    if os.path.exists(enhanced_page):
        return FileResponse(enhanced_page)
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
    - tags: 用逗号分隔的标签，如 "战斗,召唤,效果"
    
    JSON 格式支持：
    - 术语对照表格式: {"category": {"日文": "中文", ...}}
    - 简单键值对: {"原文": "翻译", ...}
    - 数组格式: [{"field": "value"}, ...]
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
            "title": "关于XXX卡牌效果的裁定",
            "effective_date": "2024-01-15",
            "tags": ["效果", "连锁"]
        },
        "content": "问：当XXX效果发动时...答：根据规则..."
    }
    ```
    """
    if not doc.content:
        raise HTTPException(status_code=400, detail="content 不能为空")
    
    result = vector_store.add_document(doc.content, doc.metadata)
    return {"status": "success", "data": result}


@app.post("/query", response_model=QueryResponse, summary="提问")
async def query(request: QueryRequest):
    """
    向智能裁判提问
    
    - question: 你的问题
    - doc_types: 可选，限定搜索范围 ["rule", "ruling", "case"]
    - top_k: 检索的参考文档数量
    """
    from app.query_processor import query_processor
    
    # 1. 首先搜索记忆
    memory_results = []
    if memory_manager.config.enable_memory_search:
        print("[记忆] 🧠 搜索相关记忆...")
        memory_results = memory_manager.search_memories(
            query=request.question,
            top_k=3
        )
        if memory_results:
            print(f"[记忆] ✅ 找到 {len(memory_results)} 条相关记忆")
    
    card_docs = []  # 卡牌数据（直接显示）
    rule_docs_list = []  # 规则数据（给LLM分析）
    seen_contents = set()
    
    # 1. 优先提取卡牌编号并精确检索
    card_numbers = query_processor.extract_card_numbers(request.question)
    if card_numbers:
        print(f"[检索] 🎴 发现卡牌编号: {card_numbers}")
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
    print(f"[检索] 🔍 语义搜索: {request.question[:50]}...")
    rule_results = vector_store.search(
        query=request.question,
        doc_types=request.doc_types,
        top_k=request.top_k,
        translate_result=True
    )
    print(f"[检索] 📚 找到 {len(rule_results)} 条规则文档")
    for doc in rule_results:
        content_hash = hash(doc["content"][:100])
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            rule_docs_list.append(doc)
    
    # 3. 构建给LLM的上下文（包含记忆、卡牌效果和规则）
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
            cards=[]
        )
    
    # LLM 只做规则分析（不传卡牌数据，避免它编造效果）
    if all_docs_for_llm:
        answer = llm_service.generate_answer(request.question, all_docs_for_llm)
    else:
        answer = "已找到相关卡牌数据（见上方）。如需规则裁定分析，请确保已导入规则文档。"
    
    # 卡牌数据直接返回（前端直接显示，不依赖LLM）
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
    
    # 返回结果，包含记忆信息
    response = QueryResponse(answer=answer, sources=sources, cards=cards)
    
    # 添加记忆相关信息（用于前端显示反馈选项）
    if hasattr(response, '__dict__'):
        response.__dict__['memories_used'] = len(memory_results)
        response.__dict__['can_save_memory'] = True  # 标记可以保存为记忆
    
    return response


@app.get("/documents", summary="列出所有文档")
async def list_documents(doc_type: Optional[DocumentType] = None):
    """获取知识库中的所有文档列表"""
    docs = vector_store.list_documents(doc_type)
    return {"status": "success", "data": docs, "total": len(docs)}


@app.delete("/documents/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str, doc_type: DocumentType):
    """
    删除指定文档
    
    - doc_id: 文档ID（上传时返回）
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
    - importance: 重要性 (1=低, 2=中, 3=高, 4=关键)
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
        raise HTTPException(status_code=500, detail=f"保存记忆失败: {str(e)}")


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


# ==================== 图片识别 API ====================

@app.post("/image/recognize", summary="识别卡牌图片")
async def recognize_card_image(
    file: UploadFile = File(...),
    detailed: bool = Form(False)
):
    """
    识别上传的卡牌图片
    
    - file: 卡牌图片文件 (JPG/PNG)
    - detailed: 是否返回详细分析
    
    返回:
    - card_number: 卡牌编号
    - card_name: 卡牌名称
    - confidence: 置信度
    - analysis: 分析结果
    """
    try:
        from judge_integration import CardImageRecognizer
        
        # 读取图片
        image_data = await file.read()
        
        # 创建识别器并识别
        recognizer = CardImageRecognizer()
        result = recognizer.recognize_card(image_data)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"识别失败：{str(e)}\n{traceback.format_exc()}"
        )


@app.post("/image/query", summary="图片 + 文字混合询问")
async def image_query(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    top_k: int = Form(5)
):
    """
    上传卡牌图片并进行询问
    
    - file: 卡牌图片文件
    - question: 文字问题 (可选，如不提供则自动分析)
    - top_k: 检索的参考文档数量
    
    返回:
    - recognition: 图片识别结果
    - answer: 裁定回答
    - sources: 参考来源
    """
    try:
        from judge_integration import JudgeIntegrationService
        
        # 读取图片
        image_data = await file.read()
        
        # 创建集成服务并处理
        service = JudgeIntegrationService()
        result = service.process_image_query(image_data, question)
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "status": "success",
            "data": {
                "recognition": result["recognition"],
                "answer": result["answer"],
                "sources": result["sources"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"处理失败：{str(e)}\n{traceback.format_exc()}"
        )


@app.post("/image/batch-recognize", summary="批量识别多张卡牌图片")
async def batch_recognize_cards(
    files: List[UploadFile] = File(...),
):
    """
    批量识别多张卡牌图片
    
    - files: 多张卡牌图片文件
    
    返回:
    - results: 每张卡牌的识别结果列表
    """
    try:
        from judge_integration import CardImageRecognizer
        
        recognizer = CardImageRecognizer()
        results = []
        
        for file in files:
            image_data = await file.read()
            result = recognizer.recognize_card(image_data)
            results.append({
                "filename": file.filename,
                "recognition": result
            })
        
        return {
            "status": "success",
            "data": {
                "total": len(results),
                "results": results
            }
        }
        
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"批量识别失败：{str(e)}\n{traceback.format_exc()}"
        )

