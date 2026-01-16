# 抑制警告
import warnings
import os
import logging
import sys

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*Tried to instantiate class.*")

# 抑制 streamlit 的 torch 警告日志
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
logging.getLogger("streamlit.watcher.path_watcher").setLevel(logging.ERROR)

import streamlit as st

# set_page_config 必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="卡牌游戏智能裁判",
    page_icon="🎴",
    layout="wide"
)

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用 st.cache_resource 缓存重量级资源，避免重复加载
@st.cache_resource
def get_vector_store():
    from app.vector_store import vector_store
    # 预热 embedding 模型
    _ = vector_store.embeddings
    return vector_store

@st.cache_resource
def get_llm_service():
    from app.llm_service import llm_service
    return llm_service

@st.cache_resource
def get_query_processor():
    from app.query_processor import query_processor
    return query_processor

# 显示加载状态
with st.spinner("正在加载模型，首次启动可能需要几分钟..."):
    vector_store = get_vector_store()
    llm_service = get_llm_service()
    query_processor = get_query_processor()

from app.pdf_processor import extract_text_from_bytes
from app.models import DocumentType, DocumentMetadata

st.title("🎴 卡牌游戏智能裁判")
st.caption("上传规则文档，然后向 AI 裁判提问")

# 侧边栏 - 文档管理
with st.sidebar:
    st.header("📚 文档管理")
    
    # 上传文件
    st.subheader("上传文件")
    uploaded_file = st.file_uploader("选择 PDF、TXT 或 JSON 文件", type=["pdf", "txt", "json"])
    file_doc_type = st.selectbox("文档类型", ["rule", "ruling", "case"], 
                                  format_func=lambda x: {"rule": "📘 规则", "ruling": "⚖️ 裁定", "case": "📋 判例"}[x],
                                  key="file_type")
    file_title = st.text_input("文档标题", placeholder="例如：游戏王规则手册 v1.0（JSON可留空自动生成）", key="file_title")
    file_tags = st.text_input("标签（逗号分隔）", placeholder="例如：基础规则,战斗", key="file_tags")
    
    if st.button("📤 上传文件", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.error("请选择文件")
        else:
            try:
                content = uploaded_file.read()
                filename = uploaded_file.name
                
                # JSON 文件特殊处理（卡牌数据）
                if filename.endswith('.json'):
                    import json
                    import time
                    json_data = json.loads(content.decode('utf-8'))
                    
                    # 判断是卡牌数组还是单个对象
                    cards = json_data if isinstance(json_data, list) else [json_data]
                    total = len(cards)
                    
                    # 后台日志
                    print(f"\n{'='*50}")
                    print(f"📤 开始导入 JSON 文件: {filename}")
                    print(f"   共 {total} 条卡牌数据")
                    print(f"{'='*50}")
                    
                    # UI 进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    start_time = time.time()
                    
                    for i, card in enumerate(cards):
                        # 提取卡牌信息生成文本
                        card_text_parts = []
                        card_name = card.get('name', card.get('card_name', ''))
                        card_no = card.get('card_no', card.get('number', ''))
                        
                        for key, value in card.items():
                            if value and str(value).strip():
                                card_text_parts.append(f"{key}: {value}")
                        
                        card_text = "\n".join(card_text_parts)
                        if not card_text.strip():
                            print(f"   ⚠️ [{i+1}/{total}] 跳过空卡牌")
                            continue
                        
                        title = file_title.strip() if file_title.strip() else f"{card_no} {card_name}".strip()
                        metadata = DocumentMetadata(
                            doc_type=DocumentType(file_doc_type),
                            title=title,
                            tags=[t.strip() for t in file_tags.split(",") if t.strip()] + ([card_no] if card_no else [])
                        )
                        result = vector_store.add_document(card_text, metadata)
                        success_count += 1
                        
                        # 更新进度
                        progress = (i + 1) / total
                        progress_bar.progress(progress)
                        status_text.text(f"导入中... {i+1}/{total} - {title}")
                        
                        # 后台日志（每10条或最后一条）
                        if (i + 1) % 10 == 0 or i == total - 1:
                            elapsed = time.time() - start_time
                            print(f"   ✓ [{i+1}/{total}] {title} ({result['chunk_count']} chunks) - {elapsed:.1f}s")
                    
                    elapsed = time.time() - start_time
                    progress_bar.empty()
                    status_text.empty()
                    
                    print(f"{'='*50}")
                    print(f"✅ 导入完成！成功 {success_count}/{total}，耗时 {elapsed:.1f}s")
                    print(f"{'='*50}\n")
                    
                    st.success(f"JSON 导入成功！共导入 {success_count} 条卡牌数据，耗时 {elapsed:.1f}s")
                else:
                    # PDF/TXT 处理
                    if not file_title.strip():
                        st.error("请输入文档标题")
                    else:
                        print(f"\n📤 开始上传文件: {filename}")
                        
                        text = extract_text_from_bytes(content, filename)
                        if not text.strip():
                            st.error("无法从文件中提取文本")
                            print(f"   ❌ 无法提取文本")
                        else:
                            metadata = DocumentMetadata(
                                doc_type=DocumentType(file_doc_type),
                                title=file_title.strip(),
                                tags=[t.strip() for t in file_tags.split(",") if t.strip()]
                            )
                            result = vector_store.add_document(text, metadata)
                            
                            print(f"   ✅ 上传成功: {file_title.strip()}")
                            print(f"      文档ID: {result['doc_id']}, 分块数: {result['chunk_count']}\n")
                            
                            st.success(f"上传成功！文档ID: {result['doc_id']}, 分块数: {result['chunk_count']}")
            except Exception as e:
                import traceback
                print(f"   ❌ 上传失败: {str(e)}")
                st.error(f"上传失败: {str(e)}\n{traceback.format_exc()}")
    
    st.divider()
    
    # 添加文本
    st.subheader("添加文本")
    text_content = st.text_area("内容", placeholder="直接粘贴裁定或判例内容...", height=150)
    text_doc_type = st.selectbox("类型", ["ruling", "case", "rule"],
                                  format_func=lambda x: {"rule": "📘 规则", "ruling": "⚖️ 裁定", "case": "📋 判例"}[x],
                                  key="text_type")
    text_title = st.text_input("标题", placeholder="例如：关于XXX效果的官方裁定", key="text_title")
    text_tags = st.text_input("标签", placeholder="例如：效果,连锁", key="text_tags")
    
    if st.button("➕ 添加文本", use_container_width=True):
        if not text_content.strip():
            st.error("请输入内容")
        elif not text_title.strip():
            st.error("请输入标题")
        else:
            try:
                metadata = DocumentMetadata(
                    doc_type=DocumentType(text_doc_type),
                    title=text_title.strip(),
                    tags=[t.strip() for t in text_tags.split(",") if t.strip()]
                )
                result = vector_store.add_document(text_content.strip(), metadata)
                st.success(f"添加成功！文档ID: {result['doc_id']}")
            except Exception as e:
                st.error(f"添加失败: {str(e)}")

# 主区域 - 问答
tab1, tab2, tab3 = st.tabs(["💬 提问", "📚 文档列表", "🔬 Embedding 测试"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        question = st.text_area("你的问题", placeholder="例如：当两张卡牌同时发动效果时，如何判断优先级？", height=100)
    
    with col2:
        doc_types = st.multiselect("搜索范围（留空搜索全部）", ["rule", "ruling", "case"],
                                    format_func=lambda x: {"rule": "规则", "ruling": "裁定", "case": "判例"}[x])
        top_k = st.slider("参考文档数量", 1, 10, 5)
    
    if st.button("🔍 提问", type="primary"):
        if not question.strip():
            st.warning("请输入问题")
        else:
            # 创建日志容器
            log_container = st.empty()
            logs = []
            
            def log_callback(msg: str):
                logs.append(f"{msg}")
                log_container.info("\n".join(logs))
            
            try:
                import time
                start_time = time.time()
                
                all_docs = []
                seen_contents = set()  # 用于去重
                selected_types = [DocumentType(t) for t in doc_types] if doc_types else None
                
                # 步骤0: 提取卡牌编号并精确检索
                card_numbers = query_processor.extract_card_numbers(question.strip())
                if card_numbers:
                    log_callback(f"🎴 步骤0/4: 发现卡牌编号: {card_numbers}")
                    for card_no in card_numbers:
                        card_docs = vector_store.search_by_card_number(card_no, translate_result=True)
                        log_callback(f"   └─ {card_no}: 找到 {len(card_docs)} 条结果")
                        for doc in card_docs:
                            content_hash = hash(doc["content"][:100])
                            if content_hash not in seen_contents:
                                seen_contents.add(content_hash)
                                all_docs.append(doc)
                else:
                    log_callback("🔍 步骤0/4: 未发现卡牌编号，跳过精确搜索")
                
                # 步骤1: 向量搜索（规则相关）
                log_callback("🔍 步骤1/4: 开始向量搜索...")
                rule_docs = vector_store.search(
                    query=question.strip(), 
                    doc_types=selected_types, 
                    top_k=top_k,
                    translate_result=True
                )
                for doc in rule_docs:
                    content_hash = hash(doc["content"][:100])
                    if content_hash not in seen_contents:
                        seen_contents.add(content_hash)
                        all_docs.append(doc)
                
                # 限制总数，但确保卡牌信息优先
                max_docs = top_k + len(card_numbers) * 2
                docs = all_docs[:max_docs]
                
                log_callback(f"✅ 搜索完成，共 {len(docs)} 个相关文档（卡牌: {len(all_docs) - len(rule_docs)}，规则: {len(rule_docs)}）")
                
                if not docs:
                    log_container.empty()
                    st.warning("知识库中没有找到相关信息，请先上传规则文档。")
                else:
                    # 步骤2-4: 调用 LLM（内部有详细日志）
                    answer = llm_service.generate_answer(question.strip(), docs, log_callback=log_callback)
                    
                    elapsed = time.time() - start_time
                    log_callback(f"🎉 全部完成！总耗时 {elapsed:.1f}s")
                    
                    # 清除日志，显示结果
                    log_container.empty()
                    
                    st.subheader("回答")
                    st.markdown(answer)
                    
                    st.subheader("参考来源")
                    # 先显示卡牌信息，再显示规则
                    card_docs_shown = []
                    rule_docs_shown = []
                    for doc in docs:
                        if doc.get('score', 1) == 0.0:  # 精确匹配的卡牌
                            card_docs_shown.append(doc)
                        else:
                            rule_docs_shown.append(doc)
                    
                    if card_docs_shown:
                        st.markdown("**🎴 卡牌信息**")
                        for doc in card_docs_shown:
                            with st.expander(f"🎴 {doc['metadata'].get('title', '未知')}"):
                                st.write(doc['content'][:800] + "..." if len(doc['content']) > 800 else doc['content'])
                    
                    if rule_docs_shown:
                        st.markdown("**📚 规则参考**")
                        for doc in rule_docs_shown:
                            doc_type_label = {"rule": "📘规则", "ruling": "⚖️裁定", "case": "📋判例"}.get(doc['doc_type'], "📄")
                            with st.expander(f"{doc_type_label} {doc['metadata'].get('title', '未知')}"):
                                st.write(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                            
            except TimeoutError as e:
                log_container.empty()
                st.error(f"⏰ {str(e)}")
            except Exception as e:
                import traceback
                log_container.empty()
                st.error(f"查询失败: {str(e)}")
                st.code(traceback.format_exc())

with tab2:
    if st.button("🔄 刷新列表"):
        st.rerun()
    
    try:
        docs = vector_store.list_documents()
        if not docs:
            st.info("📭 知识库为空，请先上传文档")
        else:
            for doc in docs:
                doc_type_label = {"rule": "📘规则", "ruling": "⚖️裁定", "case": "📋判例"}.get(doc.get("doc_type", ""), "📄")
                
                with st.expander(f"{doc_type_label} {doc.get('title', '未知')} ({doc.get('chunk_count', 0)} 个分块)"):
                    st.markdown(f"""
- **文档ID**: `{doc.get('doc_id', '')}`
- **类型**: {doc.get('doc_type', '')}
- **标签**: {doc.get('tags', '') or '无'}
- **创建时间**: {doc.get('created_at', '')[:19] if doc.get('created_at') else '未知'}
""")
                    
                    # 查看分块按钮
                    if st.button(f"📄 查看分块内容", key=f"view_{doc.get('doc_id')}"):
                        chunks = vector_store.get_document_chunks(doc.get('doc_id'))
                        if chunks:
                            for chunk in chunks:
                                st.markdown(f"**分块 {chunk['chunk_index'] + 1}**")
                                st.text_area(
                                    label=f"chunk_{chunk['chunk_index']}", 
                                    value=chunk['content'], 
                                    height=150,
                                    key=f"chunk_{doc.get('doc_id')}_{chunk['chunk_index']}",
                                    label_visibility="collapsed"
                                )
                        else:
                            st.warning("未找到分块内容")
    except Exception as e:
        import traceback
        st.error(f"获取失败: {str(e)}")
        st.code(traceback.format_exc())

with tab3:
    st.subheader("🔬 Embedding 测试")
    st.caption("测试向量搜索是否正常工作，不调用 LLM")
    
    test_query = st.text_input("测试查询", placeholder="输入关键词测试搜索...")
    test_top_k = st.slider("返回结果数", 1, 10, 3, key="test_top_k")
    
    if st.button("🔍 测试搜索", type="primary"):
        if not test_query.strip():
            st.warning("请输入查询内容")
        else:
            with st.spinner("搜索中..."):
                try:
                    docs = vector_store.search(query=test_query.strip(), top_k=test_top_k)
                    
                    if not docs:
                        st.warning("❌ 未找到相关内容，可能原因：\n1. 知识库为空\n2. 查询与文档内容不相关\n3. Embedding 模型未正确加载")
                    else:
                        st.success(f"✅ 找到 {len(docs)} 个相关结果，Embedding 工作正常！")
                        
                        for i, doc in enumerate(docs, 1):
                            score = doc.get('score', 0)
                            # 分数越低越相似（L2距离）
                            similarity = "高" if score < 0.5 else "中" if score < 1.0 else "低"
                            
                            with st.expander(f"结果 {i} - 相似度: {similarity} (距离: {score:.4f})"):
                                st.markdown(f"**来源**: {doc['metadata'].get('title', '未知')}")
                                st.markdown(f"**类型**: {doc['doc_type']}")
                                st.markdown(f"**分块索引**: {doc['metadata'].get('chunk_index', '?')}")
                                st.divider()
                                st.markdown("**内容**:")
                                st.text(doc['content'])
                                
                except Exception as e:
                    import traceback
                    st.error(f"搜索失败: {str(e)}")
                    st.code(traceback.format_exc())
    
    st.divider()
    st.subheader("📊 知识库统计")
    
    if st.button("查看统计"):
        try:
            docs = vector_store.list_documents()
            if docs:
                total_chunks = sum(d.get('chunk_count', 0) for d in docs)
                by_type = {}
                for d in docs:
                    t = d.get('doc_type', 'unknown')
                    by_type[t] = by_type.get(t, 0) + 1
                
                col1, col2, col3 = st.columns(3)
                col1.metric("文档总数", len(docs))
                col2.metric("分块总数", total_chunks)
                col3.metric("平均分块/文档", f"{total_chunks/len(docs):.1f}" if docs else "0")
                
                st.markdown("**按类型统计**:")
                for t, count in by_type.items():
                    label = {"rule": "📘规则", "ruling": "⚖️裁定", "case": "📋判例"}.get(t, t)
                    st.write(f"- {label}: {count} 个文档")
            else:
                st.info("知识库为空")
        except Exception as e:
            st.error(f"获取统计失败: {str(e)}")
