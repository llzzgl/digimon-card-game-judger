"""
向量数据库管理工具 - GUI 版本
支持选择嵌入模型、上传多种类型文档、查看和删除已有文档
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pathlib import Path

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class FileItem:
    """文件项，包含文件路径和元数据"""
    def __init__(self, path, doc_type="rule", title="", tags=""):
        self.path = path
        self.doc_type = doc_type
        self.title = title or Path(path).stem
        self.tags = tags


class VectorDBManagerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("向量数据库管理工具")
        self.root.geometry("950x800")
        self.root.resizable(True, True)
        
        self.msg_queue = queue.Queue()
        self.file_items = []
        self.db_documents = []  # 数据库中的文档列表
        
        self.create_widgets()
        self.check_queue()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === 嵌入模型选择 ===
        model_frame = ttk.LabelFrame(main_frame, text="嵌入模型设置", padding="10")
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(model_frame, text="嵌入模型:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="local")
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=45, state="readonly")
        model_combo['values'] = (
            "local (paraphrase-multilingual-MiniLM-L12-v2)",
            "openai (text-embedding-3-small)",
            "openai-large (text-embedding-3-large)"
        )
        model_combo.current(0)
        model_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # === 标签页 ===
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建两个标签页
        self.import_tab = ttk.Frame(self.notebook)
        self.browse_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.import_tab, text="📥 导入文档")
        self.notebook.add(self.browse_tab, text="📚 浏览数据库")
        
        # 切换标签页时刷新数据
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.create_import_tab()
        self.create_browse_tab()
        
        # === 日志输出（共用） ===
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_import_tab(self):
        """创建导入标签页"""
        tab = self.import_tab
        
        # === 添加文件区域 ===
        add_frame = ttk.LabelFrame(tab, text="添加文件", padding="10")
        add_frame.pack(fill=tk.X, pady=(10, 10), padx=5)
        
        row1 = ttk.Frame(add_frame)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row1, text="文档类型:").pack(side=tk.LEFT)
        self.add_type_var = tk.StringVar(value="rule")
        type_combo = ttk.Combobox(row1, textvariable=self.add_type_var, width=15, state="readonly")
        type_combo['values'] = ("rule", "terminology", "card", "ruling")
        type_combo.current(0)
        type_combo.pack(side=tk.LEFT, padx=(5, 20))
        type_combo.bind("<<ComboboxSelected>>", self.on_add_type_change)
        
        ttk.Button(row1, text="📂 添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row1, text="📁 添加文件夹", command=self.add_folder).pack(side=tk.LEFT)
        
        row2 = ttk.Frame(add_frame)
        row2.pack(fill=tk.X)
        
        ttk.Label(row2, text="默认标签:").pack(side=tk.LEFT)
        self.default_tags_var = tk.StringVar(value="规则书,官方规则")
        ttk.Entry(row2, textvariable=self.default_tags_var, width=50).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(row2, text="(新添加文件的默认标签)").pack(side=tk.LEFT, padx=(10, 0))
        
        # === 文件列表 ===
        list_frame = ttk.LabelFrame(tab, text="待导入文件列表（双击编辑）", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        columns = ("type", "title", "tags", "path")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("type", text="类型")
        self.tree.heading("title", text="标题")
        self.tree.heading("tags", text="标签")
        self.tree.heading("path", text="文件路径")
        
        self.tree.column("type", width=80, anchor=tk.CENTER)
        self.tree.column("title", width=200)
        self.tree.column("tags", width=200)
        self.tree.column("path", width=350)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.edit_item)
        
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="✏️ 编辑选中", command=self.edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ 移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self.clear_files).pack(side=tk.LEFT)
        
        # === 进度显示 ===
        progress_frame = ttk.LabelFrame(tab, text="导入进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="就绪 - 导入是追加模式，不会删除已有数据")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(5, 0))
        
        # === 操作按钮 ===
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, padx=5)
        
        self.import_btn = ttk.Button(action_frame, text="🚀 开始导入（追加模式）", command=self.start_import)
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="🗑️ 清空数据库", command=self.clear_database).pack(side=tk.LEFT)

    def create_browse_tab(self):
        """创建浏览数据库标签页"""
        tab = self.browse_tab
        
        # === 统计信息 ===
        stats_frame = ttk.LabelFrame(tab, text="数据库统计", padding="10")
        stats_frame.pack(fill=tk.X, pady=(10, 10), padx=5)
        
        self.stats_var = tk.StringVar(value="点击刷新查看统计信息")
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(side=tk.LEFT)
        ttk.Button(stats_frame, text="🔄 刷新", command=self.refresh_db_list).pack(side=tk.RIGHT)
        
        # === 文档列表 ===
        list_frame = ttk.LabelFrame(tab, text="数据库中的文档（可多选删除）", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        columns = ("doc_id", "title", "doc_type", "chunks", "tags", "created_at")
        self.db_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.db_tree.heading("doc_id", text="文档ID")
        self.db_tree.heading("title", text="标题")
        self.db_tree.heading("doc_type", text="类型")
        self.db_tree.heading("chunks", text="分块数")
        self.db_tree.heading("tags", text="标签")
        self.db_tree.heading("created_at", text="创建时间")
        
        self.db_tree.column("doc_id", width=100)
        self.db_tree.column("title", width=250)
        self.db_tree.column("doc_type", width=80, anchor=tk.CENTER)
        self.db_tree.column("chunks", width=60, anchor=tk.CENTER)
        self.db_tree.column("tags", width=200)
        self.db_tree.column("created_at", width=150)
        
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.db_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.db_tree.xview)
        self.db_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.db_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # === 操作按钮 ===
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        ttk.Button(action_frame, text="🔄 刷新列表", command=self.refresh_db_list).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🗑️ 删除选中文档", command=self.delete_selected_docs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="📋 查看分块内容", command=self.view_chunks).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🧹 清空全部数据", command=self.clear_database).pack(side=tk.LEFT)

    def on_tab_changed(self, event):
        """标签页切换时刷新数据"""
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 1:  # 浏览数据库标签页
            self.refresh_db_list()
    
    def refresh_db_list(self):
        """刷新数据库文档列表"""
        try:
            from app.vector_store import vector_store
            
            # 清空现有列表
            self.db_tree.delete(*self.db_tree.get_children())
            self.db_documents.clear()
            
            docs = vector_store.list_documents()
            self.db_documents = docs
            
            if not docs:
                self.stats_var.set("知识库为空")
                return
            
            # 统计信息
            total_chunks = sum(d.get('chunk_count', 0) for d in docs)
            by_type = {}
            for d in docs:
                t = d.get('doc_type', 'unknown')
                by_type[t] = by_type.get(t, 0) + 1
            
            type_stats = ", ".join([f"{t}: {c}" for t, c in by_type.items()])
            self.stats_var.set(f"文档总数: {len(docs)} | 分块总数: {total_chunks} | {type_stats}")
            
            # 填充列表
            type_icons = {"rule": "📘", "ruling": "⚖️", "case": "📋"}
            for doc in docs:
                doc_type = doc.get('doc_type', '')
                icon = type_icons.get(doc_type, "📄")
                created = doc.get('created_at', '')[:16] if doc.get('created_at') else ''
                
                self.db_tree.insert("", tk.END, values=(
                    doc.get('doc_id', ''),
                    doc.get('title', ''),
                    f"{icon} {doc_type}",
                    doc.get('chunk_count', 0),
                    doc.get('tags', ''),
                    created
                ))
            
            self.log(f"已加载 {len(docs)} 个文档")
            
        except Exception as e:
            self.stats_var.set(f"加载失败: {str(e)}")
            self.log(f"刷新列表失败: {str(e)}")
    
    def delete_selected_docs(self):
        """删除选中的文档"""
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的文档")
            return
        
        count = len(selected)
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {count} 个文档吗？\n此操作不可恢复！"):
            return
        
        try:
            from app.vector_store import vector_store
            from app.models import DocumentType
            
            success = 0
            failed = 0
            
            for item in selected:
                values = self.db_tree.item(item, 'values')
                doc_id = values[0]
                doc_type_str = values[2].split()[-1]  # 去掉图标
                
                try:
                    doc_type = DocumentType(doc_type_str)
                    if vector_store.delete_document(doc_id, doc_type):
                        success += 1
                        self.log(f"✓ 已删除: {values[1]} ({doc_id})")
                    else:
                        failed += 1
                        self.log(f"✗ 删除失败: {values[1]} ({doc_id})")
                except Exception as e:
                    failed += 1
                    self.log(f"✗ 删除失败: {values[1]} - {str(e)}")
            
            messagebox.showinfo("完成", f"删除完成！\n成功: {success}\n失败: {failed}")
            self.refresh_db_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def view_chunks(self):
        """查看选中文档的分块内容"""
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要查看的文档")
            return
        
        # 只查看第一个选中的
        item = selected[0]
        values = self.db_tree.item(item, 'values')
        doc_id = values[0]
        title = values[1]
        
        try:
            from app.vector_store import vector_store
            
            chunks = vector_store.get_document_chunks(doc_id)
            if not chunks:
                messagebox.showinfo("提示", "未找到分块内容")
                return
            
            # 创建查看窗口
            dialog = tk.Toplevel(self.root)
            dialog.title(f"分块内容 - {title}")
            dialog.geometry("700x500")
            dialog.transient(self.root)
            
            frame = ttk.Frame(dialog, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"文档: {title} | 共 {len(chunks)} 个分块").pack(anchor=tk.W)
            
            text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            for chunk in chunks:
                text.insert(tk.END, f"=== 分块 {chunk['chunk_index'] + 1} ===\n")
                text.insert(tk.END, chunk['content'])
                text.insert(tk.END, "\n\n")
            
            text.configure(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取分块失败: {str(e)}")

    def on_add_type_change(self, event=None):
        """添加类型改变时更新默认标签"""
        doc_type = self.add_type_var.get()
        default_tags = {
            "rule": "规则书,官方规则",
            "terminology": "术语,翻译,日中对照",
            "card": "卡牌数据",
            "ruling": "裁定,QA,官方回答"
        }
        self.default_tags_var.set(default_tags.get(doc_type, ""))
    
    def get_file_types(self):
        """根据文档类型返回支持的文件类型"""
        doc_type = self.add_type_var.get()
        if doc_type == "card":
            return [("JSON 文件", "*.json"), ("所有文件", "*.*")]
        elif doc_type == "terminology":
            return [("JSON/TXT 文件", "*.json *.txt"), ("所有文件", "*.*")]
        else:
            return [
                ("支持的文件", "*.pdf *.txt *.json"),
                ("PDF 文件", "*.pdf"),
                ("文本文件", "*.txt"),
                ("JSON 文件", "*.json"),
                ("所有文件", "*.*")
            ]
    
    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择文件（可多选）",
            filetypes=self.get_file_types()
        )
        self._add_file_items(files)
    
    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            doc_type = self.add_type_var.get()
            patterns = ["*.json"] if doc_type in ["card", "terminology"] else ["*.pdf", "*.txt", "*.json"]
            
            folder_path = Path(folder)
            files = []
            for pattern in patterns:
                files.extend([str(f) for f in folder_path.glob(pattern)])
            
            self._add_file_items(files)
    
    def _add_file_items(self, files):
        """添加文件项到列表"""
        doc_type = self.add_type_var.get()
        default_tags = self.default_tags_var.get()
        
        for f in files:
            if any(item.path == f for item in self.file_items):
                continue
            
            item = FileItem(
                path=f,
                doc_type=doc_type,
                title=Path(f).stem,
                tags=default_tags
            )
            self.file_items.append(item)
            
            type_display = {"rule": "📘规则", "terminology": "📋对照", "card": "🎴卡牌", "ruling": "⚖️裁定"}
            self.tree.insert("", tk.END, values=(
                type_display.get(item.doc_type, item.doc_type),
                item.title,
                item.tags,
                item.path
            ))
    
    def edit_item(self, event):
        """双击编辑项目"""
        self.edit_selected()
    
    def edit_selected(self):
        """编辑选中的项目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要编辑的文件")
            return
        
        item_id = selected[0]
        idx = self.tree.index(item_id)
        item = self.file_items[idx]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑文件属性")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(frame, text=Path(item.path).name).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        type_var = tk.StringVar(value=item.doc_type)
        type_combo = ttk.Combobox(frame, textvariable=type_var, width=30, state="readonly")
        type_combo['values'] = ("rule", "terminology", "card", "ruling")
        type_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="标题:").grid(row=2, column=0, sticky=tk.W, pady=5)
        title_var = tk.StringVar(value=item.title)
        ttk.Entry(frame, textvariable=title_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="标签:").grid(row=3, column=0, sticky=tk.W, pady=5)
        tags_var = tk.StringVar(value=item.tags)
        ttk.Entry(frame, textvariable=tags_var, width=40).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        def save():
            item.doc_type = type_var.get()
            item.title = title_var.get()
            item.tags = tags_var.get()
            
            type_display = {"rule": "📘规则", "terminology": "📋对照", "card": "🎴卡牌", "ruling": "⚖️裁定"}
            self.tree.item(item_id, values=(
                type_display.get(item.doc_type, item.doc_type),
                item.title,
                item.tags,
                item.path
            ))
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def remove_selected(self):
        """移除选中的文件"""
        selected = self.tree.selection()
        if not selected:
            return
        
        indices = sorted([self.tree.index(item) for item in selected], reverse=True)
        for idx in indices:
            del self.file_items[idx]
        
        for item in selected:
            self.tree.delete(item)
    
    def clear_files(self):
        """清空文件列表"""
        self.tree.delete(*self.tree.get_children())
        self.file_items.clear()

    def log(self, message):
        """添加日志"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        print(message)
    
    def check_queue(self):
        """检查消息队列"""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg[0] == "log":
                    self.log(msg[1])
                elif msg[0] == "progress":
                    self.progress_var.set(msg[1])
                elif msg[0] == "status":
                    self.status_var.set(msg[1])
                elif msg[0] == "done":
                    self.import_btn.configure(state=tk.NORMAL)
                    messagebox.showinfo("完成", msg[1])
                elif msg[0] == "error":
                    self.import_btn.configure(state=tk.NORMAL)
                    messagebox.showerror("错误", msg[1])
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)
    
    def start_import(self):
        """开始导入"""
        if not self.file_items:
            messagebox.showwarning("警告", "请先添加文件")
            return
        
        self.import_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.do_import, daemon=True)
        thread.start()
    
    def do_import(self):
        """执行导入（在后台线程）"""
        try:
            from app.vector_store import vector_store
            from app.pdf_processor import extract_text_from_bytes
            from app.models import DocumentType, DocumentMetadata
            import json
            
            type_map = {
                "rule": DocumentType.RULE,
                "terminology": DocumentType.RULE,
                "card": DocumentType.RULE,
                "ruling": DocumentType.RULING
            }
            
            total = len(self.file_items)
            success = 0
            failed = 0
            total_chunks = 0
            
            self.msg_queue.put(("log", f"开始导入 {total} 个文件（追加模式）..."))
            self.msg_queue.put(("log", "=" * 50))
            
            for i, item in enumerate(self.file_items):
                p = Path(item.path)
                self.msg_queue.put(("status", f"处理中: {p.name} ({i+1}/{total})"))
                
                try:
                    content = p.read_bytes()
                    dtype = type_map.get(item.doc_type, DocumentType.RULE)
                    tags = [t.strip() for t in item.tags.split(",") if t.strip()]
                    
                    if item.doc_type == "card" and p.suffix.lower() == ".json":
                        json_data = json.loads(content.decode('utf-8'))
                        cards = json_data if isinstance(json_data, list) else [json_data]
                        
                        card_chunks = 0
                        for card in cards:
                            card_text_parts = []
                            card_name = card.get('name', card.get('card_name', ''))
                            card_no = card.get('card_no', card.get('number', ''))
                            
                            for key, value in card.items():
                                if value and str(value).strip():
                                    card_text_parts.append(f"{key}: {value}")
                            
                            card_text = "\n".join(card_text_parts)
                            if not card_text.strip():
                                continue
                            
                            card_title = f"{card_no} {card_name}".strip()
                            card_tags = tags + ([card_no] if card_no else [])
                            
                            metadata = DocumentMetadata(
                                doc_type=dtype,
                                title=card_title,
                                source=str(p),
                                tags=card_tags
                            )
                            result = vector_store.add_document(card_text, metadata)
                            card_chunks += result['chunk_count']
                        
                        total_chunks += card_chunks
                        success += 1
                        self.msg_queue.put(("log", f"✓ {p.name}: {len(cards)} 张卡牌, {card_chunks} chunks"))
                    else:
                        text = extract_text_from_bytes(content, p.name)
                        
                        if not text.strip():
                            self.msg_queue.put(("log", f"✗ {p.name}: 无法提取文本"))
                            failed += 1
                            continue
                        
                        metadata = DocumentMetadata(
                            doc_type=dtype,
                            title=item.title,
                            source=str(p),
                            tags=tags
                        )
                        
                        result = vector_store.add_document(text, metadata)
                        total_chunks += result['chunk_count']
                        success += 1
                        
                        self.msg_queue.put(("log", f"✓ {p.name}: {result['chunk_count']} chunks"))
                
                except Exception as e:
                    self.msg_queue.put(("log", f"✗ {p.name}: {str(e)}"))
                    failed += 1
                
                progress = (i + 1) / total * 100
                self.msg_queue.put(("progress", progress))
            
            self.msg_queue.put(("log", "=" * 50))
            self.msg_queue.put(("log", f"导入完成: 成功 {success}, 失败 {failed}, 总计 {total_chunks} chunks"))
            self.msg_queue.put(("status", "完成 - 数据已追加到数据库"))
            self.msg_queue.put(("done", f"导入完成！\n成功: {success}\n失败: {failed}\n新增分块数: {total_chunks}"))
            
        except Exception as e:
            import traceback
            self.msg_queue.put(("log", f"导入失败: {str(e)}"))
            self.msg_queue.put(("log", traceback.format_exc()))
            self.msg_queue.put(("error", f"导入失败: {str(e)}"))

    def clear_database(self):
        """清空数据库"""
        if not messagebox.askyesno("确认", "确定要清空整个向量数据库吗？\n此操作不可恢复！\n\n清空后需要重启程序才能继续导入。"):
            return
        
        try:
            import shutil
            import gc
            
            try:
                from app.vector_store import vector_store
                for doc_type in ["rule", "ruling", "case"]:
                    try:
                        vector_store.client.delete_collection(f"card_game_{doc_type}")
                        self.log(f"删除 collection: card_game_{doc_type}")
                    except:
                        pass
                vector_store.client = None
                vector_store._embeddings = None
            except:
                pass
            
            gc.collect()
            
            # 使用项目根目录的 data/chroma_db
            chroma_dir = Path(__file__).parent.parent / "data" / "chroma_db"
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir, ignore_errors=True)
                self.log("向量数据库文件已删除")
            
            # 清空浏览列表
            self.db_tree.delete(*self.db_tree.get_children())
            self.db_documents.clear()
            self.stats_var.set("数据库已清空")
            
            messagebox.showinfo("完成", "向量数据库已清空！\n\n请关闭此程序后重新打开，然后再导入数据。")
            
        except Exception as e:
            import traceback
            self.log(f"清空失败: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror("错误", f"清空失败: {str(e)}")


def main():
    root = tk.Tk()
    app = VectorDBManagerUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
