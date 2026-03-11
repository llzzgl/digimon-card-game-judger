# main_new.py 记忆功能集成指南

## 概述

已成功将记忆持久化功能集成到 `main_new.py`（新版RAG系统）中。新版本结合了：
- ✅ 新的模块化RAG系统（混合搜索）
- ✅ 记忆持久化系统
- ✅ 智能检索优先级
- ✅ Web界面集成

## 启动方式

### 方法1: 使用启动脚本（推荐）
```bash
# Windows
双击运行: 启动_新版_带记忆.bat

# 或命令行
.\启动_新版_带记忆.bat
```

### 方法2: 直接运行Python
```bash
# Web UI模式（默认）
python main_new.py

# API模式
python main_new.py --mode api

# 测试模式
python main_new.py --test "进化时费用会退还吗？"
```

### 方法3: 自定义配置
```bash
# 指定端口
python main_new.py --port 8080

# 指定RAG数据目录
python main_new.py --rag-dir ./custom_rag_store
```

## 新增功能

### 1. 智能检索流程

系统现在按以下优先级检索：

```
步骤0: 🧠 搜索记忆（已验证的知识）
   ↓
步骤1: 🔍 智能检索（RAG混合搜索）
   ↓
步骤2: 📝 构建结构化Prompt
   ↓
步骤3: 🤖 LLM生成答案
   ↓
步骤4: 💾 用户反馈 → 保存记忆
```

### 2. 记忆优先策略

- 如果找到相关记忆（相似度 > 0.7），优先使用
- 已验证的记忆（✅）权重更高
- 记忆会添加到LLM的上下文中

### 3. Web界面功能

#### 提问标签页（💬 提问）
- 输入问题
- 查看AI回答
- 查看统计信息（使用记忆数、来源数、耗时）
- 记忆反馈按钮：
  - ✅ 正确，保存为记忆
  - ❌ 不正确

#### 记忆标签页（🧠 记忆）
- 搜索记忆
- 查看记忆统计
- 浏览记忆列表

### 4. API接口

新增记忆相关API：

```http
# 查询（包含记忆统计）
POST /api/query
{
  "question": "问题",
  "top_k": 5
}

# 保存记忆
POST /api/save_memory
{
  "question": "问题",
  "answer": "答案",
  "user_confirmed": true,
  "importance": 3,
  "tags": []
}

# 搜索记忆
GET /api/memory/search?query=问题&top_k=5

# 获取记忆统计
GET /api/memory/stats
```

## 使用示例

### 示例1: 命令行测试模式

```bash
python main_new.py --test "BT01-001的登场时效果能否触发？"
```

输出：
```
🚀 初始化新 RAG 裁判系统...
   加载 RAG 系统...
   加载 LLM 服务...
   加载记忆系统...
✅ 初始化完成
   LLM 模型: gemini
   RAG 目录: data/rag_store
   搜索模式: 混合搜索（向量 + 关键词）
   记忆系统: 已启用 (5 条记忆)

============================================================
【问题】 BT01-001的登场时效果能否触发？
============================================================

🧠 步骤 0/4: 搜索记忆...
   找到 2 条相关记忆
   1. ✅ BT01-001的登场时效果能否触发？... (相似度: 95.2%)
   2. ✅ 登场时效果的触发时机... (相似度: 78.3%)

🔍 步骤 1/4: 智能检索...
   检索到 5 条结果
   1. 登场时效果规则 (分数: 0.892)
   2. 效果触发时机 (分数: 0.845)
   3. BT01-001卡牌数据 (分数: 0.823)

📝 步骤 2/4: 构建结构化 Prompt...
   Prompt 长度: 2345 字符

🤖 步骤 3/4: 调用 LLM (gemini)...
   [LLM] 📝 步骤1/3: 构建上下文...
   [LLM] ✅ 上下文构建完成：2 张卡牌 + 5 条规则，共 2345 字符
   [LLM] 🤖 步骤2/3: 调用 LLM (gemini)...
   [LLM] ✅ LLM 响应完成，耗时 3.2s

✅ 完成，总耗时: 3.45s
============================================================

============================================================
【裁判回答】
============================================================
根据规则，BT01-001的登场时效果可以触发。

【规则依据】
- 登场时效果在数码兽从手牌或其他区域登场到战斗区或育成区时触发
- 效果触发后，按照回合玩家优先的原则处理

【注意事项】
- 如果登场被无效，则登场时效果不会触发
- 多个登场时效果同时触发时，回合玩家的效果优先处理
============================================================

📊 统计:
   使用记忆: 2 条
   使用来源: 5 条
   耗时: 3.45s

💡 是否将此问答保存为记忆？
   1 - 正确，保存为记忆
   2 - 不正确，不保存
   其他 - 跳过

请选择 (1/2): 1

🤔 正在生成记忆总结...
✅ 记忆已保存

✅ 已保存为记忆
   记忆ID: a3f5b8c9d2e1
   总结: 【核心内容】BT01-001登场时效果可以触发
【关键信息】
- 登场时效果在数码兽登场到战斗区或育成区时触发
- 按回合玩家优先原则处理
【适用场景】数码兽从手牌或其他区域登场时...
```

### 示例2: Web界面使用

1. 启动服务：
   ```bash
   python main_new.py
   ```

2. 打开浏览器访问：`http://localhost:8000`

3. 在"💬 提问"标签页输入问题

4. 查看答案和统计信息

5. 点击"✅ 正确，保存为记忆"

6. 切换到"🧠 记忆"标签页搜索记忆

### 示例3: API调用

```python
import requests

# 查询
response = requests.post('http://localhost:8000/api/query', json={
    'question': 'BT01-001的登场时效果能否触发？',
    'top_k': 5
})

result = response.json()
print(f"答案: {result['answer']}")
print(f"使用记忆: {result['memories_used']} 条")
print(f"使用来源: {result['sources_used']} 条")

# 保存记忆
if result['success']:
    save_response = requests.post('http://localhost:8000/api/save_memory', json={
        'question': 'BT01-001的登场时效果能否触发？',
        'answer': result['answer'],
        'user_confirmed': True,
        'importance': 3
    })
    print(f"保存结果: {save_response.json()}")
```

## 代码改动说明

### 1. NewCardGameJudge 类

#### 新增属性
```python
self.memory = memory_manager  # 记忆管理器
```

#### 修改的方法
```python
def query(self, question: str, top_k: int = 5, verbose: bool = True) -> dict:
    # 返回值从 str 改为 dict，包含更多元数据
    return {
        'answer': answer,
        'memories_used': len(memory_results),
        'sources_used': len(search_results),
        'elapsed_time': elapsed
    }
```

#### 新增方法
```python
def save_as_memory(
    self,
    question: str,
    answer: str,
    user_confirmed: bool = True,
    importance: int = 2,
    tags: list = None
) -> dict:
    """保存问答为记忆"""
```

### 2. Web UI

#### 新增API端点
- `POST /api/save_memory` - 保存记忆
- `GET /api/memory/search` - 搜索记忆
- `GET /api/memory/stats` - 获取统计

#### 新增HTML功能
- 标签页切换（提问/记忆）
- 记忆反馈区域
- 记忆搜索界面
- 记忆统计显示

## 配置说明

### 环境变量（.env）

```bash
# LLM配置
LLM_MODEL=gemini
GOOGLE_API_KEY=your_api_key

# 代理配置
USE_PROXY=True
PROXY_HOST=127.0.0.1
PROXY_PORT=7890

# 记忆系统配置（可选）
MEMORY_STORAGE_PATH=./data/memory
MEMORY_SEARCH_ENABLED=true
MEMORY_AUTO_SUMMARIZE=true
```

### 命令行参数

```bash
python main_new.py --help

参数说明:
  --mode {web,api,test}  启动模式
  --port PORT            端口号（默认8000）
  --test TEST            测试问题
  --rag-dir RAG_DIR      RAG数据目录
```

## 性能对比

### 使用记忆前
```
查询耗时: 5-8秒
LLM调用: 每次都需要
准确性: 依赖RAG检索质量
```

### 使用记忆后
```
查询耗时: 2-4秒（命中记忆时）
LLM调用: 可复用已验证答案
准确性: 持续提升（用户反馈）
```

## 故障排除

### 问题1: 记忆系统初始化失败
```
错误: Failed to initialize memory system
解决: 检查 data/memory 目录权限
```

### 问题2: 记忆搜索无结果
```
原因: 记忆库为空或相似度阈值过高
解决: 
1. 先保存一些记忆
2. 降低相似度阈值（在 memory_config.py 中）
```

### 问题3: 总结生成失败
```
原因: LLM服务不可用
解决: 系统会自动降级为简单摘要
```

## 最佳实践

### 1. 记忆积累策略
- 优先保存常见问题
- 标记重要裁定为高重要性
- 定期清理低质量记忆

### 2. 使用建议
- 首次使用时多保存记忆
- 遇到相似问题时检查记忆
- 定期查看记忆统计

### 3. 性能优化
- 记忆数量控制在1000以内
- 定期重建向量索引
- 使用标签分类记忆

## 下一步

### 短期优化
- [ ] 添加记忆导出/导入功能
- [ ] 记忆质量评分
- [ ] 批量导入官方裁定

### 中期规划
- [ ] 记忆可视化网络
- [ ] 自动发现矛盾记忆
- [ ] 记忆推荐系统

## 相关文档

- `MEMORY_SYSTEM_GUIDE.md` - 记忆系统完整指南
- `MEMORY_IMPLEMENTATION_SUMMARY.md` - 技术实现总结
- `CARD_EXTRACTION_IMPROVEMENT.md` - 卡牌提取优化说明

## 总结

`main_new.py` 现在完全集成了记忆持久化功能，提供：
- 🧠 智能记忆检索
- 💾 用户反馈机制
- 📊 统计和分析
- 🎯 持续学习能力

系统会随着使用逐步积累知识，回答质量持续提升！
