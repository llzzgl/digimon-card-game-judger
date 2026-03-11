# 记忆系统使用指南

## 概述

记忆系统是一个智能的知识积累机制，通过用户反馈来持续改进AI裁判的回答质量。系统会记住经过验证的问答对，并在未来遇到类似问题时优先使用这些记忆。

## 核心特性

### 1. 人工验证机制
- 每次AI回答后，用户可以标记答案是否正确
- 只有用户确认正确的答案才会被保存为高质量记忆
- 不正确的答案也会被记录，用于后续改进

### 2. 智能总结
- 使用LLM自动总结问答对的核心内容
- 提炼关键规则、卡牌编号和适用场景
- 便于后续快速检索和理解

### 3. 记忆检索
- 在回答问题前，优先搜索相关记忆
- 已验证的记忆会被优先使用
- 提高回答速度和准确性

### 4. 持久化存储
- 记忆保存在本地文件系统
- 使用ChromaDB进行向量检索
- 支持增量更新和删除

## 使用流程

### 步骤1: 提问
在"💬 提问"标签页输入问题，点击"🔍 提问"按钮。

```
示例问题：
- BT01-001的登场时效果能否触发？
- 两张卡牌同时触发效果时，如何判断优先级？
- 反击效果可以在对方回合使用吗？
```

### 步骤2: 查看答案
系统会显示：
- 🎴 卡牌效果（如果查询包含卡牌编号）
- ⚖️ AI分析（基于规则和裁定的分析）
- 📚 规则参考（引用的规则来源）

### 步骤3: 反馈
在答案下方的"🧠 记忆反馈"区域：
- 点击"✅ 正确，保存为记忆" - 如果答案正确且有价值
- 点击"❌ 不正确" - 如果答案有误

### 步骤4: 自动总结
系统会自动：
1. 使用LLM总结问答对
2. 提取关键信息（卡牌编号、规则要点等）
3. 保存为长期记忆

### 步骤5: 未来使用
下次遇到类似问题时：
- 系统会优先搜索记忆
- 已验证的记忆会被优先使用
- 提高回答速度和准确性

## 记忆管理

### 查看记忆统计
在"🧠 记忆"标签页可以看到：
- 记忆总数
- 已验证记忆数
- 最近使用的记忆数

### 搜索记忆
1. 在搜索框输入问题
2. 点击"🔍 搜索"
3. 查看相关记忆及其相似度

### 记忆详情
每条记忆包含：
- ✅/❓ 验证状态
- 问题和答案
- 总结内容
- 相似度评分
- 重要性等级（⭐）

## 配置选项

### 记忆配置文件
位置：`app/memory_config.py`

```python
@dataclass
class MemoryConfig:
    # 存储配置
    storage_path: str = "./data/memory"
    max_short_term_memories: int = 50
    max_long_term_memories: int = 1000
    
    # 检索配置
    enable_memory_search: bool = True
    memory_search_top_k: int = 3
    memory_similarity_threshold: float = 0.7
    
    # 总结配置
    enable_auto_summarize: bool = True
    
    # 验证配置
    require_user_confirmation: bool = True
```

### 修改配置
编辑 `.env` 文件添加：

```bash
# 记忆系统配置
MEMORY_STORAGE_PATH=./data/memory
MEMORY_SEARCH_ENABLED=true
MEMORY_AUTO_SUMMARIZE=true
```

## API接口

### 保存记忆
```http
POST /memory/save
Content-Type: multipart/form-data

question: 问题文本
answer: 答案文本
user_confirmed: true/false
importance: 1-4
tags: 标签1,标签2
```

### 搜索记忆
```http
GET /memory/search?query=问题&top_k=5
```

### 获取记忆详情
```http
GET /memory/{memory_id}
```

### 更新反馈
```http
POST /memory/{memory_id}/feedback
Content-Type: multipart/form-data

confirmed: true/false
feedback: 反馈文本（可选）
```

### 删除记忆
```http
DELETE /memory/{memory_id}
```

### 获取统计
```http
GET /memory/stats
```

## 记忆类型

### 1. 短期记忆 (Short-term)
- 存储在内存中
- 当前会话有效
- 最多保存50条
- 用于快速访问

### 2. 长期记忆 (Long-term)
- 持久化到磁盘
- 跨会话保留
- 最多保存1000条
- 用于知识积累

### 3. 情景记忆 (Episodic)
- 特定场景的记忆
- 包含上下文信息
- 用于复杂场景分析

### 4. 语义记忆 (Semantic)
- 抽象的规则知识
- 不依赖具体场景
- 用于通用规则查询

## 记忆重要性

### 等级划分
- 🌟 低 (1) - 一般性问题
- 🌟🌟 中 (2) - 常见问题
- 🌟🌟🌟 高 (3) - 重要裁定
- 🌟🌟🌟🌟 关键 (4) - 核心规则

### 自动评级
系统会根据以下因素自动评级：
- 用户确认状态
- 访问频率
- 卡牌重要性
- 规则复杂度

## 最佳实践

### 1. 及时反馈
- 每次获得答案后，及时标记正确性
- 帮助系统快速学习和改进

### 2. 详细标签
- 为重要记忆添加标签
- 便于分类和检索

### 3. 定期清理
- 删除过时或错误的记忆
- 保持记忆库的质量

### 4. 批量导入
- 可以批量导入官方裁定
- 快速建立知识库

### 5. 备份记忆
- 定期备份 `data/memory` 目录
- 防止数据丢失

## 故障排除

### 问题1: 记忆保存失败
**原因：** 存储目录权限不足或磁盘空间不足
**解决：** 检查 `data/memory` 目录权限和磁盘空间

### 问题2: 搜索不到记忆
**原因：** 相似度阈值过高或记忆未正确索引
**解决：** 降低 `memory_similarity_threshold` 或重建索引

### 问题3: 总结生成失败
**原因：** LLM服务不可用或API配额用完
**解决：** 检查LLM配置，系统会自动降级为简单摘要

### 问题4: 记忆数量过多
**原因：** 超过最大限制
**解决：** 增加 `max_long_term_memories` 或清理旧记忆

## 高级功能

### 记忆衰减
- 长时间未使用的记忆会降低重要性
- 可配置衰减系数
- 自动清理低重要性记忆

### 记忆合并
- 相似记忆可以合并
- 减少冗余
- 提高检索效率

### 记忆导出
```python
from app.memory_manager import memory_manager

# 导出所有记忆
memories = memory_manager.export_all()

# 保存为JSON
import json
with open('memories_backup.json', 'w') as f:
    json.dump(memories, f, ensure_ascii=False, indent=2)
```

### 记忆导入
```python
# 从JSON导入
with open('memories_backup.json', 'r') as f:
    memories = json.load(f)

for mem in memories:
    memory_manager.add_memory(**mem)
```

## 灵魂配置 (Soul Config)

灵魂配置定义了AI裁判的人格和行为准则：

```python
soul_config = {
    "name": "DTCG裁判助手",
    "role": "数码宝贝卡牌游戏裁判",
    "personality": "专业、严谨、友好",
    "expertise": [
        "规则解释",
        "效果裁定",
        "时机判断",
        "连锁处理"
    ],
    "principles": [
        "基于官方规则和裁定",
        "优先使用已验证的记忆",
        "不确定时明确说明",
        "持续学习和改进"
    ]
}
```

这些配置会影响：
- LLM的系统提示词
- 记忆的总结风格
- 答案的表达方式
- 不确定性的处理

## 性能优化

### 1. 索引优化
- 定期重建向量索引
- 使用更高效的嵌入模型

### 2. 缓存策略
- 缓存常用记忆
- 减少磁盘I/O

### 3. 批量操作
- 批量添加记忆
- 批量更新统计

### 4. 异步处理
- 异步生成总结
- 后台更新索引

## 未来规划

- [ ] 记忆可视化界面
- [ ] 记忆质量评分
- [ ] 自动发现矛盾记忆
- [ ] 记忆推荐系统
- [ ] 多用户记忆隔离
- [ ] 记忆版本控制
- [ ] 记忆协作编辑

## 参考资料

- [ChromaDB文档](https://docs.trychroma.com/)
- [LangChain记忆系统](https://python.langchain.com/docs/modules/memory/)
- [向量数据库最佳实践](https://www.pinecone.io/learn/vector-database/)
