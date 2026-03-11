# DTCG Judger 别名映射表构建报告

## 概述

本报告记录了数码宝贝卡牌裁判（DTCG Judger）别名映射表的构建过程、方法和结果。

## 背景

在 DTCG 卡牌查询中，用户可能使用不同的名称变体来搜索同一张卡牌：
- **简称**：如"亚古"代替"亚古兽"
- **音译变体**：如"西尔芙"、"希尔弗"都是"西尔弗兽"
- **日文名**：如"アグモン"对应"亚古兽"
- **后缀差异**：如"XX 龙"、"XX 天使"、"XX 兽"

为解决译名不一致问题，需要构建完善的别名映射表。

## 数据源

### 主要数据源
- **文件**: `skill/data/terms.json`
- **内容**: 中文术语→日文术语映射表
- **总术语数**: 2318 条

### 辅助数据源
- **文件**: `skill/data/cards.json`
- **内容**: 完整卡牌数据库
- **总卡牌数**: 10135 张
- **唯一名称数**: 3878 个

## 构建方法

### 1. 数据分析

通过脚本分析 cards.json 中的卡牌名称模式：

```python
# 提取日文名（片假名）和中文名
katakana = re.findall(r'[\u30A0-\u30FF]+', name)
chinese = re.findall(r'[\u4E00-\u9FFF]+', name)
```

**分析结果**:
- 纯日文名：1627 个
- 纯中文名：1957 个
- 混合名：294 个

### 2. 提取数码兽名称映射

从 terms.json 中提取所有包含"兽"、"龙"、"天使"等后缀的中文名称，并获取对应的日文名。

**筛选条件**:
- 中文名包含"兽"或"兽"或"龙"或"天使"
- 日文名为纯片假名

### 3. 生成简称变体

基于中文标准名自动生成简称：
- 移除"兽"后缀：如"亚古兽" → "亚古"
- 移除"龙兽"后缀：如"三角龙兽" → "三角"
- 移除"天使兽"后缀：如"主天使兽" → "主"

### 4. 手动补充常见变体

添加常见音译变体：
- 西尔芙 → 西尔弗兽
- 希尔弗 → 西尔弗兽
- 美杜莎 → 美杜莎兽
- 灰姑娘 → 灰姑娘兽
- 靴靴 → 靴靴兽

## 构建结果

### 别名映射表结构

```json
{
  "variants": {
    "简称/变体": "标准名",
    ...
  },
  "jp_to_cn": {
    "日文名": "中文名",
    ...
  },
  "suffix_rules": {
    "remove": ["兽", "龙", "天使", "数码兽"],
    "add": ["兽"]
  }
}
```

### 统计数据

| 映射类型 | 数量 | 说明 |
|---------|------|------|
| 变体映射 (variants) | 1052 条 | 中文简称/变体 → 标准名 |
| 日文→中文 (jp_to_cn) | 955 条 | 日文数码兽名 → 中文数码兽名 |

### 映射表示例

#### 变体映射样本

| 变体 | 标准名 |
|------|--------|
| 亚古 | 亚古兽 |
| 加布 | 加布兽 |
| 机械暴龙 | 机械暴龙兽 |
| 战斗暴龙 | 战斗暴龙兽 |
| 公爵 | 公爵兽 |
| 红莲 | 红莲骑士兽 |
| 阿尔法 | 阿尔法兽 |
| 奥米加 | 奥米加兽 |
| 西尔芙 | 西尔弗兽 |
| 美杜莎 | 美杜莎兽 |

#### 日文→中文映射样本

| 日文名 | 中文名 |
|--------|--------|
| アグモン | 亚古兽 |
| ガブモン | 加布兽 |
| グレイモン | 古拉兽 |
| ガルルモン | 加鲁鲁兽 |
| エンジェウーモン | 天女兽 |
| デビモン | 恶魔兽 |
| ピエモン | 小丑皇 |
| オメガモン | 奥米加兽 |
| デュークモン | 公爵兽 |
| シルフィーモン | 西尔弗兽 |

## 集成到查询系统

### 修改的文件

- **文件**: `skill/src/judger.py`
- **修改内容**:
  1. `_load_data()`: 加载 name_aliases.json 而非 name_variants.json
  2. `search_card_by_name()`: 应用别名映射和日文→中文映射
  3. `search_rulings()`: 应用日文关键词映射

### 查询流程

```
用户输入
    ↓
[日文名？] → 是 → jp_to_cn 映射 → 中文名
    ↓ 否
[别名/简称？] → 是 → variants 映射 → 标准名
    ↓ 否
使用标准名搜索索引
    ↓
返回匹配结果
```

### 代码示例

```python
def search_card_by_name(self, name: str, language: str = 'cn'):
    # 1. 日文名→中文名映射
    if name in self.jp_to_cn_map:
        name = self.jp_to_cn_map[name]
    
    # 2. 中文别名→标准名映射
    if name.lower() in self.name_variants:
        name = self.name_variants[name.lower()]
    
    # 3. 使用索引查询
    return self.card_name_index.get(name, [])
```

## 自动化脚本

### 脚本清单

1. **tools/build_alias_from_terms.py**
   - 从 terms.json 提取数码兽名称映射
   - 自动生成简称变体
   - 输出 name_aliases.json

2. **tools/extract_jp_cn.py**
   - 从 cards.json 提取日文→中文映射候选
   - 供人工审核使用

3. **tools/generate_aliases.py**
   - 综合构建别名映射表
   - 包含手动补充的常见变体

### 使用方法

```bash
# 从 terms.json 构建别名表
python tools/build_alias_from_terms.py

# 从 cards.json 提取映射候选
python tools/extract_jp_cn.py

# 综合生成别名表
python tools/generate_aliases.py
```

## 测试建议

### 测试用例

1. **简称查询**
   - 输入："亚古" → 期望：返回"亚古兽"相关卡牌
   - 输入："加布" → 期望：返回"加布兽"相关卡牌

2. **音译变体查询**
   - 输入："西尔芙" → 期望：返回"西尔弗兽"相关卡牌
   - 输入："美杜莎" → 期望：返回"美杜莎兽"相关卡牌

3. **日文名查询**
   - 输入："アグモン" → 期望：返回"亚古兽"相关卡牌
   - 输入："オメガモン" → 期望：返回"奥米加兽"相关卡牌

4. **裁定查询**
   - 输入："アグモン 进化" → 期望：返回亚古兽相关进化裁定

### 测试命令

```python
from skill.src.judger import DTCGJudger

judger = DTCGJudger()

# 测试简称查询
results = judger.search_card_by_name("亚古")
print(f"找到 {len(results)} 张卡牌")

# 测试日文名查询
results = judger.search_card_by_name("アグモン", language='jp')
print(f"找到 {len(results)} 张卡牌")

# 测试裁定查询
results = judger.search_rulings("亚古兽 进化")
print(f"找到 {len(results)} 条裁定")
```

## 维护建议

### 定期更新

1. **新卡包发布时**: 运行 `build_alias_from_terms.py` 更新映射表
2. **用户反馈新变体**: 手动添加到 name_aliases.json 的 variants 部分
3. **季度审查**: 检查映射表的完整性和准确性

### 扩展方向

1. **多语言支持**: 添加英文名→中文名映射
2. **智能推荐**: 基于搜索日志自动发现新变体
3. **模糊匹配优化**: 改进相似度算法提高查询准确率

## 文件清单

| 文件 | 说明 |
|------|------|
| `skill/data/name_aliases.json` | 别名映射表（主文件） |
| `skill/data/alias_extraction_report.txt` | 提取详细报告 |
| `tools/build_alias_from_terms.py` | 别名构建脚本 |
| `tools/extract_jp_cn.py` | 日文→中文提取脚本 |
| `tools/generate_aliases.py` | 综合生成脚本 |
| `skill/src/judger.py` | 查询系统集成（已修改） |
| `ALIAS_MAP_REPORT.md` | 本报告 |

## 总结

别名映射表的构建显著提升了 DTCG Judger 的查询体验：

✅ **支持 1052 个中文变体**：用户可使用简称、音译变体查询
✅ **支持 955 个日文名映射**：日文名用户可直接搜索
✅ **自动化构建流程**：便于后续维护和更新
✅ **无缝集成查询系统**：无需修改调用代码

下一步建议进行充分测试，并根据用户反馈持续优化映射表。

---

**报告生成时间**: 2026-03-11
**生成工具**: DTCG Judger 别名映射构建脚本
**数据版本**: cards.json (10135 张卡牌), terms.json (2318 条术语)
