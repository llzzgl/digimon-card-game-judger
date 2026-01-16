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
    
    all_docs = []
    seen_contents = set()  # 用于去重
    
    # 1. 提取卡牌编号并精确检索
    card_numbers = query_processor.extract_card_numbers(request.question)
    if card_numbers:
        print(f"[检索] 发现卡牌编号: {card_numbers}")
        for card_no in card_numbers:
            # 使用精确文本匹配搜索卡牌
            card_docs = vector_store.search_by_card_number(card_no, translate_result=True)
            print(f"[检索] {card_no} 找到 {len(card_docs)} 条结果")
            for doc in card_docs:
                content_hash = hash(doc["content"][:100])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_docs.append(doc)
    
    # 2. 对原始问题进行语义检索（规则相关）
    rule_docs = vector_store.search(
        query=request.question,
        doc_types=request.doc_types,
        top_k=request.top_k,
        translate_result=True
    )
    for doc in rule_docs:
        content_hash = hash(doc["content"][:100])
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            all_docs.append(doc)
    
    # 限制总数，但确保卡牌信息优先
    max_docs = request.top_k + len(card_numbers) * 2
    all_docs = all_docs[:max_docs]
    
    if not all_docs:
        return QueryResponse(
            answer="抱歉，我在知识库中没有找到与您问题相关的信息。请确保已上传相关规则文档。",
            sources=[]
        )
    
    # 生成回答
    answer = llm_service.generate_answer(request.question, all_docs)
    
    # 整理来源信息 - 显示实际搜索到的内容
    sources = [
        {
            "title": doc["metadata"].get("title", ""),
            "doc_type": doc.get("doc_type", ""),
            "excerpt": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"]
        }
        for doc in all_docs
    ]
    
    return QueryResponse(answer=answer, sources=sources)


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
