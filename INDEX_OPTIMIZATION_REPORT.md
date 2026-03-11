# DTCG Judger 索引优化报告

## 执行日期
2026-03-11

## 优化概述

本次优化为 DTCG Judger 添加了多种索引结构，显著提升了卡牌查询和 QA 搜索的性能。

## 实施的索引

### 1. 卡牌编号索引 (card_no_index)
- **类型**: 字典哈希索引
- **复杂度**: O(1) 查询
- **条目数**: 6,185 个卡牌编号
- **实现位置**: `_load_data()` 方法

```python
self.card_no_index = {}
for card in self.cards:
    card_no = card.get('card_no', '').upper()
    if card_no:
        # 标准化编号
        card_no_normalized = re.sub(r'^(EX)0(\d-)', r'\1\2', card_no)
        card_no_normalized = re.sub(r'^(BT)0(\d-)', r'\1\2', card_no_normalized)
        self.card_no_index[card_no_normalized] = card
```

### 2. 卡牌名称索引 (card_name_index)
- **类型**: 倒排索引（关键词 → 卡牌列表）
- **复杂度**: O(k) 查询，k 为匹配关键词数量
- **条目数**: 9,716 个关键词
- **实现位置**: `_load_data()` 方法

```python
self.card_name_index = {}
for card in self.cards:
    for lang in ['card_name', 'card_name_jp']:
        name = card.get(lang, '').lower()
        if name:
            keywords = self._extract_keywords(name)
            for kw in keywords:
                if kw not in self.card_name_index:
                    self.card_name_index[kw] = []
                if card not in self.card_name_index[kw]:
                    self.card_name_index[kw].append(card)
```

### 3. QA 裁定索引 (ruling_index)
- **类型**: 倒排索引（关键词 → 裁定列表）
- **复杂度**: O(k) 查询
- **条目数**: 11,518 个关键词
- **实现位置**: `_load_data()` 方法

```python
self.ruling_index = {}
for ruling in self.rulings:
    text = f"{ruling.get('question', '')} {ruling.get('answer', '')}".lower()
    keywords = self._extract_keywords(text)
    for kw in keywords:
        if kw not in self.ruling_index:
            self.ruling_index[kw] = []
        if ruling not in self.ruling_index[kw]:
            self.ruling_index[kw].append(ruling)
```

### 4. 规则章节索引 (rule_section_index)
- **类型**: 章节 → 内容行列表
- **复杂度**: O(1) 章节访问
- **条目数**: 158 个章节
- **实现位置**: `_load_data()` 方法

## 性能测试结果

### 测试环境
- **数据规模**: 
  - 卡牌：10,135 张
  - 裁定：4,636 条
  - 规则：55,635 字符
  - 术语：2,318 条
- **索引构建时间**: 0.65 秒
- **索引内存占用**: ~814 KB

### 查询性能对比

| 查询类型 | 索引查询 | 线性查询 | 性能提升 |
|---------|---------|---------|---------|
| 卡牌编号查询 (1000 次) | 2.04 μs/次 | 6.91 μs/次 | **3.4x** |
| 卡牌名称搜索 (100 次) | 3.57 ms/次 | 2.54 ms/次 | 0.7x* |
| QA 裁定搜索 (100 次) | 0.00 ms/次 | 6.28 ms/次 | **5434x** |

*注：卡牌名称搜索性能略有下降是因为当前实现包含二次验证逻辑以确保精确匹配。可以通过优化验证逻辑进一步提升。

### 总体性能
- **索引查询总耗时**: 0.36s
- **线性查询总耗时**: 0.89s
- **总体提升**: **2.5x**
- **节省时间**: 59.6%

## 关键优化点

### search_card() - O(1) 查询
```python
def search_card(self, card_no: str) -> Optional[Dict[str, Any]]:
    card_no = card_no.strip().upper()
    card_no = re.sub(r'^(EX)0(\d-)', r'\1\2', card_no)
    card_no = re.sub(r'^(BT)0(\d-)', r'\1\2', card_no)
    return self.card_no_index.get(card_no)  # O(1)
```

### search_card_by_name() - 倒排索引查询
```python
def search_card_by_name(self, name: str, language: str = 'cn') -> List[Dict[str, Any]]:
    name = name.strip().lower()
    
    # 使用索引查询
    if name in self.card_name_index:
        return self.card_name_index[name]
    
    # 关键词提取和多关键词搜索
    keywords = self._extract_keywords(name)
    # ... 索引查询逻辑
```

### search_rulings() - 倒排索引查询
```python
def search_rulings(self, keyword: str) -> List[Dict[str, Any]]:
    keyword = keyword.lower()
    # 日文关键词映射...
    
    # 使用索引查询
    if keyword in self.ruling_index:
        return self.ruling_index[keyword]
    
    # 关键词提取和多关键词搜索
    keywords = self._extract_keywords(keyword)
    # ... 索引查询逻辑
```

## 新增辅助方法

### _extract_keywords() - 关键词提取
```python
def _extract_keywords(self, text: str) -> List[str]:
    """从文本中提取关键词（中文分词简化版）"""
    keywords = []
    text = text.strip()
    for i in range(len(text)):
        for length in [2, 3, 4]:
            if i + length <= len(text):
                kw = text[i:i+length]
                if kw and not kw.isdigit() and not re.match(r'^[^\u4e00-\u9fa5a-zA-Z]+$', kw):
                    keywords.append(kw)
    return keywords
```

### get_index_stats() - 索引统计
```python
def get_index_stats(self) -> Dict[str, Any]:
    """获取索引统计信息"""
    return {
        "card_no_index_entries": len(self.card_no_index),
        "card_name_index_keywords": len(self.card_name_index),
        "ruling_index_keywords": len(self.ruling_index),
        "rule_section_index_sections": len(self.rule_section_index),
        "index_memory_estimate_bytes": ...
    }
```

## 性能目标达成情况

| 查询类型 | 当前 | 目标 | 实际提升 | 达成 |
|---------|------|------|---------|------|
| 卡牌编号查询 | O(n) | O(1) | 3.4x | ✓ |
| 卡牌名称搜索 | O(n*m) | O(k) | 0.7x* | △ |
| QA 搜索 | O(n*m) | O(k) | 5434x | ✓✓ |

*卡牌名称搜索需要进一步优化二次验证逻辑

## 内存占用分析

- **总索引内存**: ~814 KB
- **卡牌编号索引**: ~200 KB (估算)
- **卡牌名称索引**: ~350 KB (估算)
- **QA 裁定索引**: ~250 KB (估算)
- **规则章节索引**: ~14 KB (估算)

内存占用合理，对于现代应用可忽略不计。

## 后续优化建议

### 高优先级
1. **优化卡牌名称搜索的二次验证逻辑**
   - 当前实现为了精确匹配进行了二次线性验证
   - 可以考虑使用卡牌 ID 集合来避免重复验证
   - 预期提升：2-5x

2. **添加缓存层**
   - 对热门查询结果进行缓存
   - 使用 LRU Cache 限制内存占用
   - 预期提升：10x+ (对于重复查询)

### 中优先级
3. **优化关键词提取算法**
   - 当前使用简单的 n-gram 分词
   - 可以考虑集成中文分词库（如 jieba）
   - 预期提升：更准确的匹配，减少误报

4. **异步索引构建**
   - 将索引构建移到后台线程
   - 加快应用启动速度
   - 预期提升：启动时间减少 50%

### 低优先级
5. **持久化索引**
   - 将索引序列化到磁盘
   - 避免每次启动都重新构建
   - 预期提升：启动时间减少 80%

6. **增量索引更新**
   - 支持数据变更时增量更新索引
   - 避免全量重建

## 测试脚本

性能测试脚本位于：`skill/src/benchmark_index.py`

运行方式：
```bash
cd D:\LLMProject\dtcg_judger
python skill/src/benchmark_index.py
```

## 修改文件清单

1. `skill/src/judger.py` - 核心优化
   - 添加索引数据结构
   - 修改 `_load_data()` 构建索引
   - 优化 `search_card()` 为 O(1)
   - 优化 `search_card_by_name()` 使用倒排索引
   - 优化 `search_rulings()` 使用倒排索引
   - 优化 `search_rules()` 使用章节索引
   - 优化 `get_rule_section()` 使用预计算索引
   - 新增 `_extract_keywords()` 方法
   - 新增 `_is_section_header()` 方法
   - 新增 `_parse_section_number()` 方法
   - 新增 `get_index_stats()` 方法

2. `skill/src/benchmark_index.py` - 新增
   - 卡牌编号查询性能测试
   - 卡牌名称搜索性能测试
   - QA 裁定搜索性能测试
   - 索引构建时间测试
   - 内存占用估算

## 结论

本次索引优化显著提升了 DTCG Judger 的查询性能：

- **QA 搜索性能提升巨大**：5434x，从毫秒级降至微秒级
- **卡牌编号查询稳定提升**：3.4x，实现 O(1) 复杂度
- **总体性能提升**：2.5x，节省 59.6% 查询时间
- **内存开销合理**：~814 KB，对现代应用可忽略

卡牌名称搜索性能未达预期，主要原因是当前实现包含二次验证逻辑。建议后续优化该部分，预期可再提升 2-5x。

索引构建时间 0.65 秒，在可接受范围内。如需进一步优化启动速度，可考虑索引持久化方案。

---

**优化完成日期**: 2026-03-11  
**优化负责人**: engineer-b-perf-index (subagent)
