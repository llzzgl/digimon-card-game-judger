# DTCG Judger Skill - 数码宝贝卡牌裁判技能

## 概述

这是一个用于数码宝贝卡牌对战（Digimon Card Game）的裁判辅助技能。提供卡牌数据查询、规则裁定、术语翻译等功能。

## 功能

### 1. 卡牌查询
- 根据卡牌编号查询卡牌信息
- 根据卡牌名称搜索卡牌
- 支持中文和日文名称检索
- 查看卡牌效果、进化条件、继承效果等

### 2. 规则裁定
- 查询官方 Q&A 裁定
- 根据卡牌或场景检索相关裁定
- 提供规则条文引用

### 3. 规则书
- 完整的游戏综合规则（Ver.3.6）
- 关键词效果解释
- 游戏流程说明

### 4. 术语映射
- 中日术语对照
- 数码兽名称映射
- 游戏机制术语解释

## 数据结构

```
data/
├── cards.json      # 合并后的卡牌数据（去重、标准化）
├── rulings.json    # 官方 Q&A 裁定数据
├── rules.txt       # 综合规则书全文
└── terms.json      # 术语映射表
```

## 使用方法

```python
from src.judger import DTCGJudger

judger = DTCGJudger()

# 查询卡牌
card = judger.search_card("BT24-001")
card = judger.search_card_by_name("基基兽")

# 查询裁定
rulings = judger.search_rulings("安防")
rulings = judger.get_rulings_by_card("BT24-001")

# 查询规则
rules = judger.search_rules("进化")

# 术语翻译
term = judger.translate_term("贯通关")
```

## 数据来源

- 卡牌数据：digimoncard.com 官方数据
- 裁定数据：digimoncard.com 官方 Q&A
- 规则书：数码宝贝卡牌对战 综合规则 Ver.3.6
- 术语映射：社区整理的中日术语对照

## 更新记录

- 2026-03-10: 初始版本，整合卡牌数据、裁定、规则书和术语映射
