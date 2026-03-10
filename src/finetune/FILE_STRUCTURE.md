# 文件结构说明

## 📁 目录结构

```
card_game_judge/finetune/
├── origin_data/                    # 源数据文件夹 ⭐
│   ├── README.md                   # 源数据说明文档
│   ├── rulebook.txt                # 规则书文件
│   ├── cards.json                  # 卡牌数据文件
│   └── official_qa.json            # 官方 Q&A 文件
│
├── training_data/                  # 训练数据输出文件夹
│   ├── dtcg_finetune_data.jsonl    # 微调格式（17,940 条）
│   ├── dtcg_finetune_data.json     # JSON 格式（便于查看）
│   └── dtcg_conversation.jsonl     # 对话格式
│
├── output/                         # 微调输出文件夹（训练后生成）
│   └── dtcg_qwen_lora/             # LoRA 权重
│       ├── adapter_config.json
│       ├── adapter_model.bin
│       └── ...
│
├── finetune_qwen.py                # 微调主脚本
├── data_collector.py               # 数据收集器
├── collect_all_data.py             # 完整数据收集脚本 ⭐
├── test_card_data.py               # 卡牌数据测试脚本
├── view_samples.py                 # 查看数据示例脚本
│
├── README_CARD_DATA.md             # 卡牌数据集成文档
├── QUICK_START.md                  # 快速开始指南
├── COMPLETION_REPORT.md            # 完成报告
├── SUMMARY.md                      # 项目总结
├── CHANGELOG.md                    # 更新日志
└── FILE_STRUCTURE.md               # 本文件
```

---

## 📂 文件夹说明

### 1. origin_data/ ⭐ 新增
**用途：** 存放所有源数据文件

**包含文件：**
- `rulebook.txt` - DTCG 官方综合规则书（中文翻译版）
- `cards.json` - 所有卡牌的完整数据（3,992 张）
- `official_qa.json` - 官方 Q&A 数据

**特点：**
- 集中管理所有源数据
- 便于版本控制和备份
- 路径统一，易于维护

**详细说明：** 参见 [origin_data/README.md](origin_data/README.md)

---

### 2. training_data/
**用途：** 存放生成的训练数据

**包含文件：**
- `dtcg_finetune_data.jsonl` - 微调格式（推荐用于训练）
- `dtcg_finetune_data.json` - JSON 格式（便于查看和编辑）
- `dtcg_conversation.jsonl` - 对话格式（ChatML 风格）

**生成方式：**
```bash
python collect_all_data.py
```

---

### 3. output/
**用途：** 存放微调后的模型权重

**生成方式：**
```bash
python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl
```

**包含内容：**
- LoRA 权重文件
- 训练配置
- TensorBoard 日志
- 检查点

---

## 📄 核心脚本说明

### 1. collect_all_data.py ⭐ 已更新
**功能：** 从 origin_data/ 读取源数据，生成训练数据

**数据流程：**
```
origin_data/rulebook.txt    ──┐
origin_data/cards.json       ──┼──> collect_all_data.py ──> training_data/
origin_data/official_qa.json ──┘
```

**使用方法：**
```bash
python collect_all_data.py
```

**输出：**
- 17,940 条训练数据
- 3 种格式文件

---

### 2. finetune_qwen.py
**功能：** 使用训练数据微调 Qwen2 模型

**使用方法：**
```bash
python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl
```

---

### 3. data_collector.py
**功能：** 数据收集器核心类库

**主要类：**
- `DTCGDataCollector` - 数据收集器
- `QAPair` - 问答对数据结构

**主要方法：**
- `extract_from_rulebook()` - 从规则书提取问答
- `load_card_data()` - 加载卡牌数据
- `load_official_qa_from_file()` - 加载官方 Q&A
- `export_jsonl()` - 导出训练数据

---

## 🔄 工作流程

### 完整流程

```
1. 准备源数据
   ├── 将规则书放到 origin_data/rulebook.txt
   ├── 将卡牌数据放到 origin_data/cards.json
   └── 将官方 Q&A 放到 origin_data/official_qa.json

2. 生成训练数据
   └── python collect_all_data.py
       └── 输出到 training_data/

3. 开始微调
   └── python finetune_qwen.py --data training_data/dtcg_finetune_data.jsonl
       └── 输出到 output/

4. 测试模型
   └── 使用微调后的模型进行推理
```

---

## 📊 数据统计

### 源数据
| 文件 | 大小 | 内容 |
|------|------|------|
| rulebook.txt | ~133 KB | 1 份规则书 |
| cards.json | ~3.5 MB | 3,992 张卡牌 |
| official_qa.json | ~783 B | 2 条 Q&A |

### 训练数据
| 文件 | 大小 | 数据量 |
|------|------|--------|
| dtcg_finetune_data.jsonl | ~12.9 MB | 17,940 条 |
| dtcg_finetune_data.json | ~15.7 MB | 17,940 条 |
| dtcg_conversation.jsonl | ~14.3 MB | 17,940 条 |

---

## 🔧 维护指南

### 更新源数据

**更新规则书：**
```bash
# 1. 替换文件
cp new_rulebook.txt origin_data/rulebook.txt

# 2. 重新生成训练数据
python collect_all_data.py
```

**更新卡牌数据：**
```bash
# 1. 运行爬虫获取最新数据
cd ../../digimon_card_data_chiness
python scraper_v3.py

# 2. 复制到 origin_data
cp digimon_cards_cn.json ../card_game_judge/finetune/origin_data/cards.json

# 3. 重新生成训练数据
cd ../card_game_judge/finetune
python collect_all_data.py
```

**添加官方 Q&A：**
```bash
# 1. 编辑文件
notepad origin_data/official_qa.json

# 2. 重新生成训练数据
python collect_all_data.py
```

---

## ⚠️ 注意事项

1. **不要修改 origin_data/ 中的文件名**
   - 脚本依赖固定的文件名
   - 如需修改，请同时更新 collect_all_data.py

2. **保持文件编码为 UTF-8**
   - 所有文本文件必须使用 UTF-8 编码
   - 避免中文乱码问题

3. **定期备份源数据**
   - origin_data/ 中的文件是唯一的数据源
   - 建议使用 Git 进行版本控制

4. **training_data/ 可以重新生成**
   - 这些文件是从 origin_data/ 生成的
   - 可以随时删除并重新生成

---

## 📝 版本历史

### v1.2.0 (2026-01-26)
- ✅ 创建 origin_data/ 文件夹
- ✅ 整理所有源数据到统一位置
- ✅ 更新 collect_all_data.py 路径配置
- ✅ 添加详细的文件结构文档

### v1.1.0 (2026-01-26)
- ✅ 集成卡牌数据
- ✅ 提取规则书数据
- ✅ 生成 17,940 条训练数据

---

**最后更新：** 2026-01-26  
**维护者：** AI Assistant
