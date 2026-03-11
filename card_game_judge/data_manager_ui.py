"""
数据管理 UI - 使用 Gradio 创建图形界面

功能：
1. 导入数据（卡牌/规则/裁定）
2. 查看已导入的文档
3. 删除文档
4. 搜索测试

使用方法：
    python data_manager_ui.py
"""
import sys
import json
import warnings
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

# 抑制所有警告
warnings.filterwarnings("ignore")
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.environ["GRADIO_TELEMETRY_ENABLED"] = "False"

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import gradio as gr

from app.rag import (
    RAGManager,
    DocumentType,
    DocumentSource,
    DocumentMetadata,
    create_embedding_provider
)


class DataManagerUI:
    """数据管理 UI"""
    
    def __init__(self, rag_dir: str = "data/rag_store"):
        """初始化"""
        self.rag_dir = rag_dir
        self.rag = None
        self.init_status = "未初始化"
    
    def initialize_rag(self) -> str:
        """初始化 RAG 系统"""
        try:
            self.rag = RAGManager(
                persist_dir=self.rag_dir,
                embedding_provider=create_embedding_provider("local")
            )
            self.init_status = "✅ 已初始化"
            return "✅ RAG 系统初始化成功！"
        except Exception as e:
            self.init_status = f"❌ 初始化失败: {str(e)}"
            return f"❌ 初始化失败: {str(e)}"
    
    def import_cards(self, progress=gr.Progress()) -> str:
        """导入卡牌数据"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统"
        
        progress(0, desc="开始导入卡牌数据...")
        
        # 卡牌数据文件路径
        cards_file = Path(__file__).parent.parent / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        if not cards_file.exists():
            return f"❌ 卡牌数据文件不存在: {cards_file}"
        
        try:
            with open(cards_file, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            
            total = len(cards)
            success = 0
            failed = 0
            
            progress(0.1, desc=f"找到 {total} 张卡牌，开始导入...")
            
            for i, card in enumerate(cards):
                card_no = card.get('card_no', '')
                name_cn = card.get('name_cn', '')
                
                if not card_no:
                    failed += 1
                    continue
                
                # 格式化卡牌内容
                content = self._format_card(card)
                
                # 创建元数据
                metadata = DocumentMetadata(
                    doc_id=f"card_{card_no}",
                    title=f"{card_no} {name_cn}",
                    doc_type=DocumentType.CARD,
                    source=DocumentSource.DATABASE,
                    card_no=card_no,
                    tags=["卡牌数据"],
                    created_at=datetime.now()
                )
                
                try:
                    self.rag.add_document(content, metadata)
                    success += 1
                except Exception as e:
                    failed += 1
                    print(f"导入失败 {card_no}: {e}")
                
                # 更新进度
                if i % 50 == 0:
                    progress((i + 1) / total, desc=f"进度: {i + 1}/{total}")
            
            progress(1.0, desc="导入完成")
            return f"✅ 卡牌导入完成\n成功: {success} 张\n失败: {failed} 张"
            
        except Exception as e:
            return f"❌ 导入失败: {str(e)}"
    
    def import_file(
        self,
        file_path: str,
        doc_type: str,
        title: str,
        tags: str
    ) -> str:
        """导入单个文件"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统"
        
        if not file_path:
            return "❌ 请选择文件"
        
        file_path = Path(file_path)
        if not file_path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        try:
            # 确定文档类型
            dtype = DocumentType(doc_type)
            
            # 读取文件内容
            content = self._read_file(file_path)
            if not content:
                return "❌ 文件内容为空"
            
            # 确定标题
            if not title:
                title = file_path.stem
            
            # 解析标签
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            
            # 创建元数据
            metadata = DocumentMetadata(
                doc_id=f"{doc_type}_{file_path.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                title=title,
                doc_type=dtype,
                source=DocumentSource.DATABASE,
                tags=tag_list,
                created_at=datetime.now()
            )
            
            # 导入
            result = self.rag.add_document(content, metadata)
            
            return f"✅ 导入成功\n文档 ID: {result['doc_id']}\n分块数: {result['chunk_count']}"
            
        except Exception as e:
            return f"❌ 导入失败: {str(e)}"
    
    def list_documents(self, doc_type_filter: str = "全部") -> Tuple[str, List]:
        """列出所有文档"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统", []
        
        try:
            # 确定过滤类型
            dtype = None
            if doc_type_filter != "全部":
                dtype = DocumentType(doc_type_filter.lower())
            
            documents = self.rag.list_documents(dtype)
            
            if not documents:
                return "📭 没有找到文档", []
            
            # 格式化输出
            output_lines = [f"找到 {len(documents)} 个文档\n"]
            
            # 按类型分组
            by_type = {}
            for doc in documents:
                doc_type = doc['doc_type']
                if doc_type not in by_type:
                    by_type[doc_type] = []
                by_type[doc_type].append(doc)
            
            for doc_type, docs in by_type.items():
                type_label = {"rule": "规则", "ruling": "裁定", "card": "卡牌"}.get(doc_type, doc_type)
                output_lines.append(f"\n【{type_label}】({len(docs)} 个文档)")
                output_lines.append("-" * 60)
                
                for doc in docs[:20]:  # 每种类型最多显示 20 个
                    output_lines.append(f"  - {doc['title']}")
                    output_lines.append(f"    ID: {doc['doc_id']}, 分块数: {doc['chunk_count']}")
                
                if len(docs) > 20:
                    output_lines.append(f"  ... 还有 {len(docs) - 20} 个文档")
            
            # 准备表格数据
            table_data = []
            for doc in documents[:100]:  # 最多显示 100 个
                type_label = {"rule": "规则", "ruling": "裁定", "card": "卡牌"}.get(doc['doc_type'], doc['doc_type'])
                table_data.append([
                    doc['doc_id'],
                    doc['title'],
                    type_label,
                    doc['chunk_count']
                ])
            
            return "\n".join(output_lines), table_data
            
        except Exception as e:
            return f"❌ 列出文档失败: {str(e)}", []
    
    def delete_document(self, doc_id: str, doc_type: str) -> str:
        """删除文档"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统"
        
        if not doc_id:
            return "❌ 请输入文档 ID"
        
        try:
            dtype = DocumentType(doc_type)
            success = self.rag.delete_document(doc_id, dtype)
            
            if success:
                return f"✅ 删除成功: {doc_id}"
            else:
                return f"❌ 删除失败: 未找到文档 {doc_id}"
                
        except Exception as e:
            return f"❌ 删除失败: {str(e)}"
    
    def search_test(self, query: str, top_k: int = 5) -> str:
        """搜索测试"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统"
        
        if not query:
            return "❌ 请输入查询内容"
        
        try:
            results = self.rag.search(query, top_k=top_k)
            
            if not results:
                return "📭 没有找到相关结果"
            
            output_lines = [f"找到 {len(results)} 个结果\n"]
            
            for i, result in enumerate(results, 1):
                output_lines.append(f"【结果 {i}】")
                output_lines.append(f"标题: {result.metadata.title}")
                output_lines.append(f"类型: {result.doc_type.value}")
                output_lines.append(f"分数: {result.score:.3f}")
                output_lines.append(f"内容: {result.content[:200]}...")
                output_lines.append("")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"
    
    def search_card(self, card_no: str) -> str:
        """搜索卡牌"""
        if not self.rag:
            return "❌ 请先初始化 RAG 系统"
        
        if not card_no:
            return "❌ 请输入卡牌编号"
        
        try:
            card = self.rag.search_card_by_number(card_no)
            
            if not card:
                return f"❌ 未找到卡牌: {card_no}"
            
            output_lines = [f"✅ 找到卡牌: {card_no}\n"]
            
            if card.get('name_cn'):
                output_lines.append(f"中文名: {card['name_cn']}")
            if card.get('name_jp'):
                output_lines.append(f"日文名: {card['name_jp']}")
            if card.get('type'):
                output_lines.append(f"类型: {card['type']}")
            if card.get('color'):
                output_lines.append(f"颜色: {card['color']}")
            if card.get('level'):
                output_lines.append(f"等级: Lv.{card['level']}")
            if card.get('effect'):
                output_lines.append(f"\n效果:\n{card['effect']}")
            if card.get('inherited_effect'):
                output_lines.append(f"\n继承效果:\n{card['inherited_effect']}")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            return f"❌ 搜索失败: {str(e)}"
    
    def _read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        ext = file_path.suffix.lower()
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    parts = []
                    for item in data:
                        if 'question' in item and 'answer' in item:
                            parts.append(f"Q: {item['question']}\nA: {item['answer']}")
                        else:
                            parts.append(json.dumps(item, ensure_ascii=False))
                    return "\n\n".join(parts)
                else:
                    return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == '.pdf':
            try:
                from app.pdf_processor import extract_text_from_bytes
                content = file_path.read_bytes()
                return extract_text_from_bytes(content, file_path.name)
            except ImportError:
                return ""
        
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _format_card(self, card: dict) -> str:
        """格式化卡牌数据"""
        parts = []
        
        if card.get('card_no'):
            parts.append(f"卡牌编号: {card['card_no']}")
        if card.get('name_cn'):
            parts.append(f"中文名: {card['name_cn']}")
        if card.get('name_jp'):
            parts.append(f"日文名: {card['name_jp']}")
        if card.get('type'):
            parts.append(f"类型: {card['type']}")
        if card.get('color'):
            parts.append(f"颜色: {card['color']}")
        if card.get('rarity'):
            parts.append(f"稀有度: {card['rarity']}")
        if card.get('level'):
            parts.append(f"等级: Lv.{card['level']}")
        if card.get('play_cost'):
            parts.append(f"登场费用: {card['play_cost']}")
        if card.get('dp') and card['dp'] != '-':
            parts.append(f"DP: {card['dp']}")
        if card.get('form'):
            parts.append(f"形态: {card['form']}")
        if card.get('attribute'):
            parts.append(f"属性: {card['attribute']}")
        if card.get('species'):
            parts.append(f"种族: {card['species']}")
        if card.get('evolution_condition'):
            parts.append(f"进化条件: {card['evolution_condition']}")
        if card.get('effect'):
            parts.append(f"效果: {card['effect']}")
        if card.get('inherited_effect'):
            parts.append(f"继承效果: {card['inherited_effect']}")
        if card.get('security_effect'):
            parts.append(f"安防效果: {card['security_effect']}")
        
        return "\n".join(parts)


def create_ui():
    """创建 Gradio UI"""
    manager = DataManagerUI()
    
    with gr.Blocks(title="数据管理 - RAG 系统", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎴 数据管理 - RAG 系统")
        gr.Markdown("管理 RAG 系统的数据：导入、查看、删除文档")
        
        # 初始化状态
        with gr.Row():
            init_btn = gr.Button("🚀 初始化 RAG 系统", variant="primary")
            init_output = gr.Textbox(label="初始化状态", value="未初始化", interactive=False)
        
        init_btn.click(
            fn=manager.initialize_rag,
            outputs=init_output
        )
        
        # 标签页
        with gr.Tabs():
            # 导入数据
            with gr.Tab("📥 导入数据"):
                gr.Markdown("### 导入卡牌数据")
                with gr.Row():
                    import_cards_btn = gr.Button("导入卡牌数据（自动从 digimon_card_data_chiness）", variant="primary")
                import_cards_output = gr.Textbox(label="导入结果", lines=5)
                
                import_cards_btn.click(
                    fn=manager.import_cards,
                    outputs=import_cards_output
                )
                
                gr.Markdown("---")
                gr.Markdown("### 导入单个文件")
                
                with gr.Row():
                    file_input = gr.Textbox(label="文件路径", placeholder="例如: 规则书/综合规则.pdf")
                    doc_type_input = gr.Dropdown(
                        choices=["rule", "ruling", "card"],
                        label="文档类型",
                        value="rule"
                    )
                
                with gr.Row():
                    title_input = gr.Textbox(label="文档标题（可选）", placeholder="留空则使用文件名")
                    tags_input = gr.Textbox(label="标签（逗号分隔）", placeholder="例如: 规则,官方")
                
                import_file_btn = gr.Button("导入文件", variant="primary")
                import_file_output = gr.Textbox(label="导入结果", lines=3)
                
                import_file_btn.click(
                    fn=manager.import_file,
                    inputs=[file_input, doc_type_input, title_input, tags_input],
                    outputs=import_file_output
                )
            
            # 查看文档
            with gr.Tab("📚 查看文档"):
                gr.Markdown("### 文档列表")
                
                with gr.Row():
                    doc_type_filter = gr.Dropdown(
                        choices=["全部", "rule", "ruling", "card"],
                        label="文档类型过滤",
                        value="全部"
                    )
                    list_btn = gr.Button("刷新列表", variant="primary")
                
                list_output = gr.Textbox(label="文档列表", lines=15)
                
                gr.Markdown("### 文档表格")
                doc_table = gr.Dataframe(
                    headers=["文档 ID", "标题", "类型", "分块数"],
                    label="文档详情",
                    interactive=False
                )
                
                list_btn.click(
                    fn=manager.list_documents,
                    inputs=doc_type_filter,
                    outputs=[list_output, doc_table]
                )
            
            # 删除文档
            with gr.Tab("🗑️ 删除文档"):
                gr.Markdown("### 删除文档")
                gr.Markdown("⚠️ 警告：删除操作不可恢复！")
                
                with gr.Row():
                    delete_id_input = gr.Textbox(label="文档 ID", placeholder="从文档列表中复制")
                    delete_type_input = gr.Dropdown(
                        choices=["rule", "ruling", "card"],
                        label="文档类型",
                        value="rule"
                    )
                
                delete_btn = gr.Button("删除文档", variant="stop")
                delete_output = gr.Textbox(label="删除结果", lines=2)
                
                delete_btn.click(
                    fn=manager.delete_document,
                    inputs=[delete_id_input, delete_type_input],
                    outputs=delete_output
                )
            
            # 搜索测试
            with gr.Tab("🔍 搜索测试"):
                gr.Markdown("### 文本搜索")
                
                with gr.Row():
                    search_query = gr.Textbox(label="查询内容", placeholder="例如: 进化规则")
                    search_top_k = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="返回结果数")
                
                search_btn = gr.Button("搜索", variant="primary")
                search_output = gr.Textbox(label="搜索结果", lines=15)
                
                search_btn.click(
                    fn=manager.search_test,
                    inputs=[search_query, search_top_k],
                    outputs=search_output
                )
                
                gr.Markdown("---")
                gr.Markdown("### 卡牌搜索")
                
                card_no_input = gr.Textbox(label="卡牌编号", placeholder="例如: BT1-001")
                card_search_btn = gr.Button("搜索卡牌", variant="primary")
                card_output = gr.Textbox(label="卡牌信息", lines=10)
                
                card_search_btn.click(
                    fn=manager.search_card,
                    inputs=card_no_input,
                    outputs=card_output
                )
        
        gr.Markdown("---")
        gr.Markdown("💡 提示：首次使用请先点击「初始化 RAG 系统」按钮")
    
    return demo


def main():
    """主函数"""
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
