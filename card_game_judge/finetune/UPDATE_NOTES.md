# 更新说明 - 源数据整理

## 📋 更新内容

**日期：** 2026-01-26  
**版本：** v1.2.1

---

## ✅ 主要变更

### 1. 创建 origin_data/ 文件夹

将所有源数据文件整理到统一的 `origin_data/` 文件夹中：

```
origin_data/
├── README.md           # 源数据说明文档
├── rulebook.txt        # 规则书文件（原：数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt）
├── cards.json          # 卡牌数据文件（原：digimon_cards_cn.json）
└── official_qa.json    # 官方 Q&A 文件
```

**优点：**
- ✅ 集中管理所有源数据
- ✅ 路径统一，易于维护
- ✅ 便于版本控制和备份
- ✅ 文件命名更清晰

---

### 2. 更新 collect_all_data.py

修改了数据文件的读取路径：

**之前：**
```python
# 规则书路径（多个可能路径）
rulebook_path = Path(__file__).parent.parent / "数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt"

# 卡牌数据路径（绝对路径）
card_data_path = Path("D:/niii/zzl/LLMProject/digimon_card_data_chiness/digimon_cards_cn.json")

# 官方 Q&A 路径
official_qa_path = Path(__file__).parent / "training_data" / "official_qa.json"
```

**现在：**
```python
# 规则书路径（统一在 origin_data）
rulebook_path = Path(__file__).parent / "origin_data" / "rulebook.txt"

# 卡牌数据路径（统一在 origin_data）
card_data_path = Path(__file__).parent / "origin_data" / "cards.json"

# 官方 Q&A 路径（统一在 origin_data）
official_qa_path = Path(__file__).parent / "origin_data" / "official_qa.json"
```

**优点：**
- ✅ 路径简洁明了
- ✅ 不依赖绝对路径
- ✅ 跨平台兼容性更好
- ✅ 易于移植和分享

---

### 3. 新增文档

- ✅ `origin_data/README.md` - 源数据说明文档
- ✅ `FILE_STRUCTURE.md` - 文件结构说明
- ✅ `UPDATE_NOTES.md` - 本文件

---

## 🔄 迁移指南

如果你已经在使用旧版本，请按以下步骤迁移：

### 步骤 1：创建 origin_data 文件夹

```bash
cd card_game_judge/finetune
mkdir origin_data
```

### 步骤 2：复制源数据文件

**复制规则书：**
```bash
# Windows
copy ..\数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt origin_data\rulebook.txt

# Linux/Mac
cp ../数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt origin_data/rulebook.txt
```

**复制卡牌数据：**
```bash
# Windows
copy ..\..\digimon_card_data_chiness\digimon_cards_cn.json origin_data\cards.json

# Linux/Mac
cp ../../digimon_card_data_chiness/digimon_cards_cn.json origin_data/cards.json
```

**复制官方 Q&A：**
```bash
# Windows
copy training_data\official_qa.json origin_data\official_qa.json

# Linux/Mac
cp training_data/official_qa.json origin_data/official_qa.json
```

### 步骤 3：更新脚本

```bash
# 拉取最新代码
git pull

# 或手动更新 collect_all_data.py
```

### 步骤 4：测试

```bash
python collect_all_data.py
```

应该看到：
```
【步骤 1】从规则书提取问答...
📖 找到规则书: origin_data\rulebook.txt
✅ 从规则书提取了 282 条问答

【步骤 2】加载官方 Q&A...
✅ 加载了 2 条官方 Q&A

【步骤 3】加载卡牌数据...
📥 加载卡牌数据: origin_data\cards.json
✅ 从卡牌数据生成了 17656 条问答
```

---

## 📊 影响范围

### 受影响的文件
- ✅ `collect_all_data.py` - 已更新路径
- ✅ `QUICK_START.md` - 已更新说明
- ✅ 新增多个文档文件

### 不受影响的文件
- ✅ `finetune_qwen.py` - 无需修改
- ✅ `data_collector.py` - 无需修改
- ✅ `training_data/` - 无需修改
- ✅ 其他脚本 - 无需修改

---

## ⚠️ 注意事项

### 1. 文件名变更

| 原文件名 | 新文件名 | 位置 |
|---------|---------|------|
| 数码宝贝卡牌对战_综合规则_最新版_中文翻译_gemini.txt | rulebook.txt | origin_data/ |
| digimon_cards_cn.json | cards.json | origin_data/ |
| official_qa.json | official_qa.json | origin_data/ |

### 2. 路径变更

所有源数据文件现在都在 `origin_data/` 文件夹中，使用相对路径访问。

### 3. 向后兼容

旧版本的脚本将无法找到源数据文件，需要按照迁移指南更新。

---

## 🎯 后续计划

### 短期
- [ ] 添加数据验证脚本
- [ ] 自动化数据更新流程
- [ ] 添加数据版本管理

### 中期
- [ ] 支持多语言规则书
- [ ] 支持增量更新
- [ ] 添加数据质量检查

---

## 📞 问题反馈

如果在迁移过程中遇到问题，请：

1. 检查 `origin_data/` 文件夹是否存在
2. 检查三个源数据文件是否都已复制
3. 检查文件编码是否为 UTF-8
4. 查看 [FILE_STRUCTURE.md](FILE_STRUCTURE.md) 了解详细结构

---

## ✅ 验收清单

迁移完成后，请确认：

- [ ] `origin_data/` 文件夹已创建
- [ ] `origin_data/rulebook.txt` 存在且可读
- [ ] `origin_data/cards.json` 存在且可读
- [ ] `origin_data/official_qa.json` 存在且可读
- [ ] `python collect_all_data.py` 运行成功
- [ ] 生成了 17,940 条训练数据

---

**更新日期：** 2026-01-26  
**更新者：** AI Assistant  
**版本：** v1.2.1
