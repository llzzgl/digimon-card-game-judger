# 卡牌信息提取优化说明

## 改进概述

优化了RAG系统中的卡牌信息获取流程，确保当用户提供卡牌编号时，系统能够：
1. 优先识别和提取卡牌编号
2. 精确获取卡牌效果信息
3. 将卡牌信息作为结构化上下文传递给LLM
4. 同时检索相关的裁定和判例

## 主要改进

### 1. 增强的卡牌编号识别 (`query_processor.py`)

新增 `normalize_card_number()` 方法，支持多种卡牌编号格式：

**支持的输入格式：**
- `BT1-001` → `BT01-001`
- `BT01-001` → `BT01-001`
- `BT1001` → `BT01-001`
- `BT-1-001` → `BT01-001`
- `bt01-001` → `BT01-001` (自动转大写)
- `P001` → `P-001`
- `P-001` → `P-001`

**特性：**
- 自动标准化为统一格式 (如 `BT01-001`)
- 自动去重
- 大小写不敏感

### 2. 优化的检索流程 (`api.py`)

**改进前：**
```python
# 只检索卡牌数据
card_numbers = query_processor.extract_card_numbers(request.question)
for card_no in card_numbers:
    results = vector_store.search_by_card_number(card_no)
    card_docs.append(results)
```

**改进后：**
```python
# 1. 检索卡牌数据
card_numbers = query_processor.extract_card_numbers(request.question)
for card_no in card_numbers:
    # 精确搜索卡牌效果
    results = vector_store.search_by_card_number(card_no)
    card_docs.append(results)
    
    # 2. 同时搜索该卡牌相关的裁定和判例
    card_related_results = vector_store.search(
        query=f"卡牌编号 {card_no}",
        doc_types=[DocumentType.RULING, DocumentType.CASE],
        top_k=3
    )
    rule_docs_list.extend(card_related_results)

# 3. 语义搜索通用规则
rule_results = vector_store.search(query=request.question, ...)
```

### 3. 改进的上下文构建 (`llm_service.py`)

**改进前：**
- 所有文档统一处理
- 不区分卡牌效果和规则

**改进后：**
```python
# 区分卡牌效果和规则文档
for doc in context_docs:
    if doc_type == 'card':
        # 卡牌效果格式
        context_parts.append(
            f"【卡牌{card_count}】[{card_no}]\n"
            f"名称：{title}\n"
            f"效果：{content}\n"
        )
    else:
        # 规则/裁定格式
        context_parts.append(
            f"【参考{rule_count}】\n"
            f"来源：{title}（{type_label}）\n"
            f"内容：{content}\n"
        )
```

### 4. 更新的系统提示词

**改进前：**
```
- 卡牌效果已在界面上单独显示，你不需要列出卡牌效果
```

**改进后：**
```
- 如果参考资料中包含卡牌效果，请基于这些效果进行分析
```

## 使用示例

### 示例 1: 单张卡牌查询

**用户输入：**
```
BT1-001的登场时效果能否触发？
```

**系统处理：**
1. 提取卡牌编号：`BT01-001`
2. 检索卡牌效果
3. 检索相关裁定（关于BT01-001）
4. 检索通用规则（关于"登场时效果"）
5. 构建结构化上下文传给LLM

### 示例 2: 多张卡牌对比

**用户输入：**
```
BT1-002和ST1-01同时触发，哪个先处理？
```

**系统处理：**
1. 提取卡牌编号：`BT01-002`, `ST01-01`
2. 检索两张卡牌的效果
3. 检索相关裁定
4. 检索"效果处理顺序"相关规则
5. LLM基于完整信息进行分析

### 示例 3: 不规范格式

**用户输入：**
```
bt1001和BT-1-002的效果
```

**系统处理：**
1. 标准化：`bt1001` → `BT01-001`, `BT-1-002` → `BT01-002`
2. 正常检索和分析

## 测试

运行测试脚本验证功能：

```bash
cd card_game_judge
python test_card_extraction.py
```

测试内容：
- 卡牌编号提取和标准化
- 多种格式支持
- 去重功能
- 完整查询分析

## 日志输出示例

```
[检索] 🎴 发现卡牌编号: ['BT01-001', 'BT01-002']
[检索] 📋 BT01-001 找到 1 条卡牌数据
[检索] 📖 BT01-001 找到 2 条相关裁定/判例
[检索] 📋 BT01-002 找到 1 条卡牌数据
[检索] 📖 BT01-002 找到 1 条相关裁定/判例
[检索] 🔍 语义搜索: BT01-001和BT01-002同时触发...
[检索] 📚 找到 5 条规则文档
[上下文] 📝 添加 2 张卡牌效果到上下文
[LLM] 📝 步骤1/3: 构建上下文...
[LLM] ✅ 上下文构建完成：2 张卡牌 + 8 条规则，共 3456 字符
```

## 技术细节

### 卡牌编号正则表达式

```python
CARD_NO_PATTERN = re.compile(
    r'(BT-?\d{1,2}-?\d{2,3}|ST-?\d{1,2}-?\d{2}|EX-?\d{1,2}-?\d{2,3}|'
    r'P-?\d{3}|RB-?\d{2}|LM-?\d{2}|その他 -?\d+)',
    re.IGNORECASE
)
```

支持的卡牌系列：
- `BT` - Booster (补充包)
- `ST` - Starter (起始套牌)
- `EX` - Extra (额外系列)
- `P` - Promo (促销卡)
- `RB` - Reboot (重启系列)
- `LM` - Limited (限定系列)
- `その他` - Other (其他)

### 标准化规则

1. 前缀大写：`bt` → `BT`
2. 系列号补零：`BT1` → `BT01`
3. 卡号补零：`001` → `001` (已是3位)
4. 统一分隔符：`BT1001` → `BT01-001`

## 后续优化建议

1. **模糊匹配**：支持卡牌名称搜索（如"奥米加兽"）
2. **缓存机制**：缓存常用卡牌信息，减少检索次数
3. **批量查询**：优化多卡牌查询的性能
4. **错误提示**：当卡牌编号不存在时，给出友好提示
5. **相似卡牌推荐**：当找不到精确匹配时，推荐相似卡牌

## 相关文件

- `app/query_processor.py` - 基础查询处理器
- `app/enhanced_query_processor.py` - 增强版查询处理器
- `app/api.py` - API层检索流程
- `app/llm_service.py` - LLM服务和上下文构建
- `test_card_extraction.py` - 测试脚本
