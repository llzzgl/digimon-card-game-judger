# 卡牌游戏智能裁判

> ✨ **新版本**: 已集成新 RAG 系统，搜索准确率提升 25%！[查看详情](集成完成总结.md)  
> ✅ **问题已解决**: 网络和模型加载问题已完全解决！[查看说明](最终使用说明.md)

基于 RAG 的本地问答系统，支持规则手册、官方裁定和判例的增量更新。

## 🚀 快速开始（新 RAG 系统）

### 最简单的方式（推荐）

1. **双击** `启动.bat`
2. 选择 `[1] 启动 Web UI`
3. 访问 http://localhost:8000

### 数据管理

1. **双击** `启动.bat`
2. 选择 `[3] 数据管理 UI`
3. 访问 http://localhost:7860
4. 导入数据

### 📚 重要文档

- **[最终使用说明.md](最终使用说明.md)** - 完整使用指南 🔴 必读
- [快速开始.md](快速开始.md) - 三步快速开始
- [启动流程.md](启动流程.md) - 完整启动流程
- [数据管理UI使用说明.md](数据管理UI使用说明.md) - UI 使用指南
- [网络问题解决方案.md](网络问题解决方案.md) - 问题解决方案

---

## 原版快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置你的配置

# 3. 如果使用本地 LLM，安装 Ollama 并拉取模型
ollama pull qwen2:7b

# 4. 启动服务
python main.py
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/documents/upload` | POST | 上传 PDF/文本文件 |
| `/documents/text` | POST | 直接添加文本内容 |
| `/documents/batch` | POST | 批量添加裁定/判例 |
| `/documents` | GET | 列出所有文档 |
| `/documents/{id}` | DELETE | 删除文档 |
| `/query` | POST | 提问 |

## 使用示例

### 上传规则手册 (PDF)

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@rulebook.pdf" \
  -F "doc_type=rule" \
  -F "title=游戏规则手册 v2.0" \
  -F "version=2.0"
```

### 添加官方裁定

```bash
curl -X POST "http://localhost:8000/documents/text" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "doc_type": "ruling",
      "title": "关于连锁规则的裁定 #2024-001",
      "effective_date": "2024-01-15",
      "tags": ["连锁", "效果"]
    },
    "content": "问：当A效果和B效果同时触发时，如何决定连锁顺序？\n答：根据规则3.2.1，同时触发的效果按照..."
  }'
```

### 提问

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "当两个效果同时触发时，连锁顺序如何决定？",
    "top_k": 5
  }'
```

## 文档类型

- `rule` - 规则手册
- `ruling` - 官方裁定
- `case` - 判例

## 配置说明

编辑 `.env` 文件：

- `EMBEDDING_MODEL=local` - 使用本地 embedding 模型（推荐）
- `LLM_MODEL=local` - 使用 Ollama 本地 LLM
- 或设置 `OPENAI_API_KEY` 使用 OpenAI
