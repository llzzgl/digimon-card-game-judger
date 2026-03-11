# DTCG Judger API 模式使用指南

## 📖 简介

DTCG Judger API 支持两种查询模式，通过灵活的模式检测机制区分用户意图：

- **提问模式（Question）**: 正常的卡牌效果、规则、裁定查询
- **纠错模式（Correction）**: 对已有答案、裁定进行纠正和反馈

---

## 🎯 模式检测方法

系统采用**三级优先级**检测机制：

```
┌─────────────────────────────────┐
│  1. API 参数 mode（最高优先级）   │
│     mode: "question"/"correction"│
└──────────────┬──────────────────┘
               │ 未指定
               ▼
┌─────────────────────────────────┐
│  2. 消息前缀检测（次优先级）     │
│     [纠错] xxx / [提问] xxx      │
└──────────────┬──────────────────┘
               │ 无前缀
               ▼
┌─────────────────────────────────┐
│  3. 默认提问模式（最低优先级）   │
│     直接作为提问处理             │
└─────────────────────────────────┘
```

---

## 📡 API 接口

### 接口总览

| 接口 | 方法 | 用途 | 模式 |
|------|------|------|------|
| `/judge` | POST | 统一接口（自动检测） | Auto/Question/Correction |
| `/judge/question` | POST | 专用提问接口 | Question |
| `/judge/correction` | POST | 专用纠错接口 | Correction |
| `/query` | POST | 旧接口（兼容用） | Question |

---

## 🔹 提问模式

### 使用场景

- 查询卡牌效果
- 询问规则细节
- 搜索相关裁定
- 一般性问题

### 方法 1: 使用专用接口（推荐）

```http
POST /judge/question
Content-Type: application/json

{
    "question": "BT24-037 的效果是什么",
    "doc_types": ["rule", "ruling", "case"],
    "top_k": 5,
    "context": {
        "user_id": "user_123",
        "session_id": "session_456"
    }
}
```

**响应示例**:
```json
{
    "answer": "BT24-037 的效果是...",
    "sources": [
        {
            "title": "BT24-037 卡牌数据",
            "doc_type": "card",
            "excerpt": "【启动主要】..."
        }
    ],
    "cards": [
        {
            "card_no": "BT24-037",
            "title": "デジモン名",
            "content": "效果文本..."
        }
    ],
    "mode": "question"
}
```

### 方法 2: 使用统一接口 + API 参数

```http
POST /judge
Content-Type: application/json

{
    "question": "BT24-037 的效果是什么",
    "mode": "question",
    "top_k": 5
}
```

### 方法 3: 使用前缀标记

```http
POST /judge
Content-Type: application/json

{
    "question": "[提问] BT24-037 的效果是什么",
    "mode": "auto"
}
```

> 💡 **提示**: 前缀会被自动移除，处理时使用清理后的文本

### 支持的前缀

- `[提问]` - 标准提问前缀
- `[问题]` - 同提问
- `[Q]` - 简写
- `[问]` - 简写

---

## 🔸 纠错模式

### 使用场景

- 发现答案错误
- 纠正裁定内容
- 反馈规则引用错误
- 更新过时信息

### 方法 1: 使用专用接口（推荐）

```http
POST /judge/correction
Content-Type: application/json

{
    "query": "原答案说不能激活，但根据规则 6-2 实际可以",
    "original_answer_id": "ans_456",
    "reference": "规则 6-2 活跃阶段",
    "corrector_id": "user_123"
}
```

**响应示例**:
```json
{
    "answer": "## 纠错报告\n\n**纠正内容**: 原答案说不能激活...\n**涉及卡牌**: BT24-037\n**涉及规则**: 规则 6-2\n**状态**: 待审核\n**建议**: 已找到相关参考数据，建议核对后更新裁定",
    "sources": [],
    "cards": [],
    "mode": "correction",
    "correction_record": {
        "original_query": "原答案说不能激活，但根据规则 6-2 实际可以",
        "correction": "原答案说不能激活，但根据规则 6-2 实际可以",
        "target_card": "BT24-037",
        "target_rule": "规则 6-2",
        "timestamp": "2026-03-11T21:30:00",
        "status": "pending_review"
    }
}
```

### 方法 2: 使用统一接口 + API 参数

```http
POST /judge
Content-Type: application/json

{
    "question": "原答案错误，BT24-037 可以激活",
    "mode": "correction",
    "context": {
        "original_answer_id": "ans_456",
        "corrector_id": "user_123"
    }
}
```

### 方法 3: 使用前缀标记

```http
POST /judge
Content-Type: application/json

{
    "question": "[纠错] BT24-037 的原答案错误",
    "mode": "auto"
}
```

### 支持的前缀

- `[纠错]` - 标准纠错前缀
- `[纠正]` - 同纠错
- `[C]` - 简写
- `[错]` - 简写

### 纠错记录字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `original_query` | string | 原始查询文本 |
| `correction` | string | 纠正内容 |
| `target_card` | string | 涉及的卡牌编号（自动提取） |
| `target_rule` | string | 涉及的规则章节（自动提取） |
| `corrected_by` | string | 纠正者 ID（可选） |
| `timestamp` | datetime | 时间戳 |
| `status` | string | 状态：`pending_review`/`approved`/`rejected` |
| `reference` | string | 引用依据（可选） |
| `original_answer_id` | string | 被纠正的答案 ID（可选） |

---

## 🔄 模式优先级示例

### 示例 1: API 参数优先

```json
{
    "question": "[纠错] BT24-037 的效果",
    "mode": "question"
}
```

**结果**: 使用**提问模式**（API 参数优先级更高）

---

### 示例 2: 前缀检测（AUTO 模式）

```json
{
    "question": "[纠错] BT24-037 的原答案错误",
    "mode": "auto"
}
```

**结果**: 使用**纠错模式**（检测到前缀）

---

### 示例 3: 默认模式

```json
{
    "question": "BT24-037 的效果是什么",
    "mode": "auto"
}
```

**结果**: 使用**提问模式**（无前缀，默认提问）

---

## 🧩 自动提取功能

纠错模式支持自动提取关键信息：

### 卡牌编号提取

```python
# 输入
"[纠错] BT24-037 的效果描述不对"

# 自动提取
target_card: "BT24-037"
```

### 规则引用提取

```python
# 输入
"根据规则 6-2，这个裁定有误"

# 自动提取
target_rule: "规则 6-2"
```

### 原答案引用提取

```python
# 输入
"原答案说不能激活，但实际可以"

# 自动提取
original_answer_ref: "不能激活"
```

---

## 📊 状态流转

纠错记录的状态流转：

```
pending_review (待审核)
       │
       ├─→ approved (已通过)
       │
       └─→ rejected (已拒绝)
```

> 💡 **注意**: 当前版本仅生成纠错记录，审核功能需后续实现

---

## 🔧 请求参数详解

### QueryRequest（提问请求）

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `question` | string | ✅ | - | 问题文本 |
| `mode` | string | ❌ | "auto" | 模式：auto/question/correction |
| `doc_types` | array | ❌ | null | 限定搜索范围：["rule", "ruling", "case"] |
| `top_k` | integer | ❌ | 5 | 检索文档数量 |
| `context` | object | ❌ | null | 上下文信息 |

### CorrectionRequest（纠错请求）

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | ✅ | - | 纠错内容 |
| `original_answer_id` | string | ❌ | null | 被纠正的答案 ID |
| `reference` | string | ❌ | null | 引用依据 |
| `corrector_id` | string | ❌ | null | 纠正者 ID |

---

## 💻 代码示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 提问模式
def ask_question(question: str):
    response = requests.post(
        f"{BASE_URL}/judge/question",
        json={
            "question": question,
            "top_k": 5
        }
    )
    return response.json()

# 纠错模式（专用接口）
def submit_correction(query: str, answer_id: str = None, reference: str = None):
    response = requests.post(
        f"{BASE_URL}/judge/correction",
        json={
            "query": query,
            "original_answer_id": answer_id,
            "reference": reference,
            "corrector_id": "user_123"
        }
    )
    return response.json()

# 纠错模式（统一接口 + 前缀）
def submit_correction_auto(query: str):
    response = requests.post(
        f"{BASE_URL}/judge",
        json={
            "question": f"[纠错] {query}",
            "mode": "auto"
        }
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 提问
    result = ask_question("BT24-037 的效果是什么")
    print(f"答案：{result['answer']}")
    
    # 纠错
    correction = submit_correction(
        "原答案说不能激活，但实际可以",
        answer_id="ans_456",
        reference="规则 6-2"
    )
    print(f"纠错记录：{correction['correction_record']}")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000';

// 提问模式
async function askQuestion(question) {
    const response = await fetch(`${BASE_URL}/judge/question`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: question,
            top_k: 5
        })
    });
    return await response.json();
}

// 纠错模式
async function submitCorrection(query, answerId = null, reference = null) {
    const response = await fetch(`${BASE_URL}/judge/correction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: query,
            original_answer_id: answerId,
            reference: reference,
            corrector_id: 'user_123'
        })
    });
    return await response.json();
}

// 使用示例
(async () => {
    // 提问
    const result = await askQuestion('BT24-037 的效果是什么');
    console.log('答案:', result.answer);
    
    // 纠错
    const correction = await submitCorrection(
        '原答案说不能激活，但实际可以',
        'ans_456',
        '规则 6-2'
    );
    console.log('纠错记录:', correction.correction_record);
})();
```

---

## ❓ 常见问题

### Q1: 应该使用哪个接口？

**推荐**:
- 新应用：使用 `/judge/question` 和 `/judge/correction` 专用接口
- 旧应用升级：使用 `/judge` 统一接口，逐步迁移
- 快速集成：使用前缀标记，无需改代码

### Q2: 纠错记录如何审核？

当前版本生成纠错记录后状态为 `pending_review`。审核功能计划在后续版本实现，包括：
- 审核接口（approve/reject）
- 审核意见记录
- 通知纠正者

### Q3: 能否批量提交纠错？

当前不支持批量提交。如需批量处理，建议：
1. 循环调用 `/judge/correction`
2. 或联系管理员直接导入数据

### Q4: 前缀会被保留吗？

不会。前缀在检测后会被自动移除，处理时使用清理后的文本。

---

## 📝 最佳实践

1. **明确意图时使用 API 参数**
   ```json
   {"mode": "correction"}  // 清晰明确
   ```

2. **用户输入场景使用前缀**
   ```
   用户输入：[纠错] xxx
   系统自动检测，无需额外配置
   ```

3. **提供引用依据**
   ```json
   {
       "query": "原答案错误",
       "reference": "规则 6-2 活跃阶段"  // 提高可信度
   }
   ```

4. **记录纠正者信息**
   ```json
   {
       "corrector_id": "user_123"  // 便于追溯和统计
   }
   ```

---

## 🔗 相关文档

- [实现报告](./MODE_SEPARATOR_REPORT.md)
- [测试用例](./test_mode_separator.py)
- [API Swagger](http://localhost:8000/docs)

---

**版本**: 1.1.0  
**更新日期**: 2026-03-11
