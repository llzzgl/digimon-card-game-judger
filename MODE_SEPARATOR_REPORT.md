# DTCG Judger API 模式分离实现报告

## 📋 概述

本次实现为 DTCG Judger API 添加了**提问模式**和**纠错模式**的分离功能，支持通过 API 参数、消息前缀或混合方式区分用户意图。

**实现日期**: 2026-03-11  
**版本**: 1.1.0

---

## 🎯 实现目标

1. ✅ 区分两种使用场景：提问模式（正常查询）和纠错模式（纠正裁定）
2. ✅ 支持多种模式检测方式（API 参数、前缀标记、混合模式）
3. ✅ 为纠错模式提供特殊处理（记录、验证、报告生成）
4. ✅ 保持向后兼容性

---

## 🏗️ 方案设计

采用**混合方案（方案 C）**，优先级如下：

```
1. API 参数 mode（如果明确指定）
   ↓
2. 消息前缀检测（[纠错]/[提问] 等）
   ↓
3. 默认提问模式
```

### 方案对比

| 方案 | 优点 | 缺点 | 采用情况 |
|------|------|------|----------|
| **A: API 参数** | 清晰明确，易于维护 | 需要客户端配合修改 | ✅ 作为最高优先级 |
| **B: 前缀标记** | 用户友好，无需改客户端 | 可能误判，需清理文本 | ✅ 作为次要检测 |
| **C: 混合方案** | 兼顾灵活性和明确性 | 实现稍复杂 | ✅ **最终方案** |

---

## 📁 文件修改清单

### 新增文件

1. **`src/judger/api/modes.py`** (新建)
   - 模式定义枚举
   - 前缀检测函数
   - 纠错查询解析
   - CorrectionRecord 数据模型

2. **`test_mode_separator.py`** (新建)
   - 完整的测试用例套件
   - 覆盖 5 个测试类别

### 修改文件

1. **`card_game_judge/app/models.py`**
   - 新增 `QueryMode` 枚举
   - 新增 `CorrectionRequest` 模型
   - 更新 `QueryRequest` 添加 `mode` 和 `context` 字段
   - 更新 `QueryResponse` 添加 `mode` 和 `correction_record` 字段

2. **`skill/src/judger.py`**
   - 新增 `QueryMode` 枚举
   - 新增 `process_query()` 方法（模式分发）
   - 新增 `_handle_question()` 方法（提问处理）
   - 新增 `_handle_correction()` 方法（纠错处理）
   - 新增辅助方法：`_extract_card_numbers()`, `_parse_correction_query()`, `_generate_correction_suggestion()`

3. **`src/judger/api/routes.py`**
   - 新增 `/judge` 统一接口（自动检测）
   - 新增 `/judge/question` 提问接口
   - 新增 `/judge/correction` 纠错接口
   - 保留 `/query` 旧接口（向后兼容）
   - 实现 `_handle_question_api()` 和 `_handle_correction_api()` 内部函数

---

## 🔌 API 接口设计

### 1. 统一接口（推荐）

```http
POST /api/judge
Content-Type: application/json

{
    "question": "[纠错] BT24-037 的原答案错误",
    "mode": "auto",  // 或 "question"/"correction"
    "doc_types": ["rule", "ruling"],
    "top_k": 5
}
```

**响应示例（纠错模式）**:
```json
{
    "answer": "## 纠错报告\n\n**纠正内容**: BT24-037 的原答案错误\n**涉及卡牌**: BT24-037\n**状态**: 待审核\n**建议**: 已找到相关参考数据...",
    "sources": [],
    "cards": [],
    "mode": "correction",
    "correction_record": {
        "original_query": "[纠错] BT24-037 的原答案错误",
        "correction": "BT24-037 的原答案错误",
        "target_card": "BT24-037",
        "timestamp": "2026-03-11T21:30:00",
        "status": "pending_review"
    }
}
```

### 2. 提问接口

```http
POST /api/judge/question
Content-Type: application/json

{
    "question": "BT24-037 的效果是什么",
    "doc_types": ["rule", "ruling", "case"],
    "top_k": 5,
    "context": {
        "user_id": "user_123"
    }
}
```

### 3. 纠错接口

```http
POST /api/judge/correction
Content-Type: application/json

{
    "query": "原答案说不能激活，但实际可以",
    "original_answer_id": "ans_456",
    "reference": "规则 6-2 活跃阶段",
    "corrector_id": "user_123"
}
```

---

## 🔍 模式检测逻辑

### 前缀定义

```python
# 提问前缀
QUESTION_PREFIXES = ['[提问]', '[问题]', '[Q]', '[问]']

# 纠错前缀
CORRECTION_PREFIXES = ['[纠错]', '[纠正]', '[C]', '[错]']
```

### 检测流程

```python
def detect_mode_from_query(query: str) -> Tuple[QueryMode, str]:
    # 1. 检查纠错前缀
    if query.startswith('[纠错]') or query.startswith('[纠正]')...:
        return CORRECTION, cleaned_query
    
    # 2. 检查提问前缀
    if query.startswith('[提问]') or query.startswith('[问题]')...:
        return QUESTION, cleaned_query
    
    # 3. 默认提问
    return QUESTION, query
```

---

## 📊 纠错模式特殊处理

### 纠错记录数据结构

```python
correction_record = {
    "original_query": "...",           # 原始查询
    "correction": "...",               # 纠正内容
    "target_card": "BT24-037",         # 涉及卡牌（可选）
    "target_rule": "规则 6-2",         # 涉及规则（可选）
    "corrected_by": "user_123",        # 纠正者 ID（可选）
    "timestamp": "2026-03-11T21:30:00",
    "status": "pending_review",        # pending/approved/rejected
    "reference": "规则 6-2 活跃阶段",   # 引用依据（可选）
    "original_answer_id": "ans_456"    # 被纠正的答案 ID（可选）
}
```

### 纠错处理流程

1. **识别被纠正的对象**
   - 提取卡牌编号（正则匹配）
   - 提取规则引用（正则匹配）
   - 提取原答案引用（模式匹配）

2. **与参考数据对比验证**
   - 查询卡牌数据
   - 查询规则内容
   - 生成匹配结果

3. **生成纠正报告**
   - 格式化输出
   - 提供建议
   - 标记待审核状态

4. **保存纠错历史**（可选扩展）
   - 可后续添加到数据库

---

## 🧪 测试用例

### 测试覆盖

1. **TestModeDetection** - 模式检测功能
   - ✅ 提问前缀检测
   - ✅ 纠错前缀检测
   - ✅ 默认模式检测
   - ✅ 纠错查询解析

2. **TestJudgerModes** - 裁判器模式处理
   - ✅ 基本提问模式
   - ✅ 基本纠错模式
   - ✅ 卡牌提取
   - ✅ 规则引用提取

3. **TestCorrectionRecord** - 纠错记录模型
   - ✅ 记录创建
   - ✅ 带引用依据的记录

4. **TestAPIParamMode** - API 参数模式
   - ✅ 参数指定提问
   - ✅ 参数指定纠错
   - ✅ 参数自动检测

5. **TestMixedMode** - 混合模式优先级
   - ✅ API 参数优先级
   - ✅ 前缀检测
   - ✅ 默认模式

### 运行测试

```bash
cd D:\LLMProject\dtcg_judger
python test_mode_separator.py
```

---

## 🔄 向后兼容性

- ✅ 保留 `/query` 旧接口
- ✅ 默认模式为提问（与原有行为一致）
- ✅ 无前缀时自动使用提问模式
- ✅ 所有原有字段保持不变

---

## 📝 使用示例

### 示例 1: 提问模式（API 参数）

```python
import requests

response = requests.post("http://localhost:8000/judge/question", json={
    "question": "BT24-037 的效果是什么",
    "top_k": 5
})

print(response.json())
```

### 示例 2: 纠错模式（前缀）

```python
response = requests.post("http://localhost:8000/judge", json={
    "question": "[纠错] BT24-037 的原答案说不能激活，但实际可以",
    "mode": "auto"  # 自动检测
})

print(response.json()["correction_record"])
```

### 示例 3: 纠错模式（专用接口）

```python
response = requests.post("http://localhost:8000/judge/correction", json={
    "query": "原答案错误，根据规则 6-2 应该可以激活",
    "original_answer_id": "ans_456",
    "reference": "规则 6-2 活跃阶段",
    "corrector_id": "user_123"
})

print(response.json())
```

---

## 🚀 后续扩展建议

1. **纠错审核流程**
   - 添加审核接口（approve/reject）
   - 记录审核意见
   - 通知纠正者

2. **纠错历史**
   - 持久化存储纠错记录
   - 提供查询接口
   - 统计分析

3. **自动验证**
   - 与官方数据源对比
   - AI 辅助判断正确性
   - 置信度评分

4. **用户反馈**
   - 点赞/点踩
   - 评论讨论
   - 社区投票

---

## 📋 检查清单

- [x] 模式定义枚举
- [x] API 参数支持
- [x] 前缀标记检测
- [x] 混合模式实现
- [x] 提问模式处理
- [x] 纠错模式处理
- [x] 纠错记录结构
- [x] 卡牌提取
- [x] 规则引用提取
- [x] 纠正报告生成
- [x] API 路由设计
- [x] 测试用例
- [x] 向后兼容
- [x] 文档编写

---

## ✅ 总结

本次实现成功为 DTCG Judger API 添加了模式分离功能，采用混合方案兼顾了灵活性和明确性。纠错模式提供了完整的记录、验证和报告生成能力，为后续的审核流程和数据质量提升打下基础。

**核心优势**:
- 🎯 清晰区分用户意图
- 🔧 针对性优化响应
- 📊 完整的纠错记录
- 🔄 向后兼容
- 🧪 充分测试覆盖
