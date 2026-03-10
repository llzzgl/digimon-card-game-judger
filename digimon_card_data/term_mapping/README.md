# 数码宝贝卡牌中日文词汇对照系统

## 项目简介

本项目实现了数码宝贝卡牌游戏中文和日文专有词汇的自动对照提取功能。

## 核心功能

### 1. 游戏机制关键词提取 ⭐推荐

提取真正的游戏机制关键词，如：
- 效果触发时机：登场时、进化时、攻击时等
- 游戏动作：登场、进化、攻击、消灭等
- 游戏区域：手牌、卡组、废弃区、安防区等
- 关键词能力：贯通、突进、干扰、阻挡者等
- 数值相关：DP、Lv、费用、内存值等

**生成文件**：
- `game_mechanics_keywords.json` - 79个游戏机制关键词
- `game_mechanics_report.md` - 分类报告

### 2. 基础词汇提取

提取卡牌基础信息的中日文对照：
- 卡牌名称（数码兽名称）
- 卡牌类型（数码兽卡、数码蛋卡、驯兽师卡、选项卡）
- 颜色（红、蓝、黄、绿、黑、紫、白）
- 形态（幼年期、成长期、成熟期、完全体、究极体）
- 属性（疫苗、数据、病毒等）
- 稀有度（C、U、R、SR等）

**生成文件**：
- `basic_terms_cn_jp.json` - 1,860个基础词汇
- `basic_terms_report.md` - 统计报告

## 快速开始

### Windows用户（推荐）

双击运行批处理文件：

1. **提取游戏机制关键词**（推荐）
   ```
   双击 run_extract_game_mechanics.bat
   ```

2. **提取基础词汇**
   ```
   双击 run_extract_basic.bat
   ```

3. **启动查询工具**
   ```
   双击 run_query.bat
   ```

### 命令行用户

```bash
# 1. 提取游戏机制关键词（推荐）
python extract_game_mechanics_only.py

# 2. 提取基础词汇
python extract_basic_terms_only.py

# 3. 启动查询工具
python query_terms.py

# 4. 运行使用示例
python example_usage.py
```

## 查询工具使用

启动查询工具后，支持以下命令：

```
cn 登场时              # 查询"登场时"的日文
jp 登場時              # 查询"登場時"的中文
search-cn 攻击         # 搜索包含"攻击"的词汇
search-jp モン         # 搜索包含"モン"的日文词汇
category 颜色          # 查看所有颜色词汇
quit                   # 退出
```

## Python编程接口

```python
from query_terms import TermQuery

# 初始化查询器（使用游戏机制关键词）
query = TermQuery("game_mechanics_keywords.json")

# 或使用基础词汇
# query = TermQuery("basic_terms_cn_jp.json")

# 中文→日文
jp_terms = query.query_cn_to_jp("登场时")
print(jp_terms)  # ['登場時']

# 日文→中文
cn_terms = query.query_jp_to_cn("登場時")
print(cn_terms)  # ['登场时']

# 模糊搜索
results = query.search_cn("攻击")
for cn, jp in results.items():
    print(f"{cn} -> {jp}")
```

## 文件说明

### 核心程序
- `extract_game_mechanics_only.py` - 游戏机制关键词提取（推荐）
- `extract_basic_terms_only.py` - 基础词汇提取
- `query_terms.py` - 查询工具
- `example_usage.py` - 使用示例

### 批处理文件（Windows）
- `run_extract_game_mechanics.bat` - 运行游戏机制提取
- `run_extract_basic.bat` - 运行基础词汇提取
- `run_query.bat` - 运行查询工具

### 数据文件
- ⭐ `game_mechanics_keywords.json` - 游戏机制关键词（58个，推荐）
- `game_mechanics_report.md` - 游戏机制关键词报告
- `basic_terms_cn_jp.json` - 基础词汇对照表（1,860个）
- `basic_terms_report.md` - 基础词汇统计报告

### 文档
- `README.md` - 本文件
- `最终说明.md` - 详细说明文档

## 数据统计

### 游戏机制关键词（推荐）
- 效果触发时机：15个
- 游戏动作：17个
- 游戏区域：10个
- 关键词能力：22个
- 数值相关：6个
- 卡牌类型：4个
- 其他术语：5个
- **总计：79个**

### 基础词汇
- 卡牌名称：约1,800个
- 卡牌特征：约60个
- **总计：1,860个**

## 游戏机制关键词示例

| 类别 | 中文示例 | 日文对照 |
|------|----------|----------|
| 触发时机 | 登场时、进化时、攻击时、消灭时 | 登場時、進化時、アタック時、破棄時 |
| 游戏动作 | 登场、进化、攻击、消灭、抽卡 | 登場、進化、アタック、破棄、ドロー |
| 游戏区域 | 手牌、卡组、废弃区、安防区 | 手札、デッキ、トラッシュ、セキュリティ |
| 关键词能力 | 贯通、突进、阻挡者、再启动 | 貫通、突進、ブロッカー、リブート |
| 数值相关 | DP、Lv、费用、内存值 | DP、Lv、コスト、メモリ |

## 数据来源

- **中文卡牌**：`digimon_card_data/digimon_card_data_chiness/digimon_cards_cn.json`
- **日文卡牌**：`digimon_card_data/` 目录下所有 `digimon_cards_*_cards.json` 文件

## 匹配统计

- 中文卡牌总数：3,992张
- 日文卡牌总数：3,951张
- 成功匹配：3,941张
- **匹配率：98.7%**

## 技术特点

1. **高匹配率**：98.7%的卡牌匹配成功率
2. **精准提取**：游戏机制关键词提取准确，无文本片段
3. **双向查询**：支持中日文双向查询
4. **分类管理**：按词汇类型和游戏机制分类
5. **易于使用**：提供批处理文件和交互式查询工具
6. **无需依赖**：仅使用Python标准库

## 应用场景

1. **卡牌翻译**：将中文卡牌信息翻译为日文或反之
2. **规则查询**：快速查询游戏机制关键词的对照
3. **术语标准化**：统一中日文术语翻译标准
4. **开发辅助**：为卡牌游戏相关应用提供词汇对照支持
5. **学习工具**：帮助玩家学习中日文卡牌术语

## 常见问题

### Q: 推荐使用哪个文件？
A: 推荐使用 `game_mechanics_keywords.json`，它只包含58个精准的游戏机制关键词。如需卡牌名称，使用 `basic_terms_cn_jp.json`。

### Q: 如何更新词汇表？
A: 重新运行相应的提取程序即可。

### Q: 找不到某个词汇怎么办？
A: 使用查询工具的模糊搜索功能：`search-cn 关键词` 或 `search-jp キーワード`

## 版本信息

- **创建日期**：2026-03-02
- **版本**：3.0（最终修正版）
- **Python版本要求**：Python 3.6+
- **依赖**：仅使用Python标准库，无需额外安装

## 更多信息

查看 `最终说明.md` 了解完整的功能说明和使用指南。

---

**祝使用愉快！** 🎮
