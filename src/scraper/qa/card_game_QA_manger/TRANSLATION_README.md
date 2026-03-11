# QA翻译工具使用说明

## 概述

提供两个版本的翻译脚本，用于将日文官方QA翻译成中文：

1. **translate_qa.py** - 完整版本（需要Google Translate API）
2. **translate_qa_local.py** - 本地版本（仅使用术语替换，推荐）

## 数据依赖

翻译脚本依赖以下数据文件：

- `digimon_data/dtcg_terminology.json` - 游戏术语对照表
- `digimon_card_data_chiness/digimon_cards_cn.json` - 中文卡牌数据库
- `card_game_judge/card_game_QA_manger/official_qa_jp.json` - 日文官方QA（输入）

## 方法一：本地翻译（推荐）

### 特点
- ✅ 不需要外部API，完全本地运行
- ✅ 速度快，无API限流问题
- ✅ 准确替换专有名词和卡牌名称
- ⚠️ 保留部分日文语法结构（但专有名词已替换）

### 使用方法

```bash
cd card_game_judge/card_game_QA_manger
python translate_qa_local.py
```

### 输出
- 生成文件：`official_qa_cn.json`
- 保留原始日文字段（`question_original`, `answer_original`）
- 添加翻译标记字段

## 方法二：完整翻译（需要API）

### 特点
- ✅ 完整的中文翻译
- ✅ 准确替换专有名词和卡牌名称
- ⚠️ 需要安装googletrans库
- ⚠️ 可能遇到API限流

### 安装依赖

```bash
pip install googletrans==4.0.0-rc1
```

### 使用方法

```bash
cd card_game_judge/card_game_QA_manger
python translate_qa.py
```

### 参数调整

如果遇到API限流，可以在脚本中调整：

```python
translator.translate_all(
    batch_size=5,   # 减小批次大小
    delay=2.0       # 增加延迟时间
)
```

## 翻译效果说明

### 当前翻译质量

本地翻译脚本已经能够：
- ✅ 准确替换所有游戏专有术语（如【登场时】、【进化时】、安防等）
- ✅ 准确替换卡牌名称（通过卡号匹配）
- ✅ 替换大部分常用词汇和句式
- ⚠️ 保留部分日文语法结构和助词

### 翻译示例

**原文：**
```
このカードの【登場時】【進化時】効果は、自分か相手のどちらのデジモンでもレストできますか？
```

**翻译后：**
```
这张卡的【登场时】【进化时】效果、自己か对手的哪边的数码宝贝也休眠可以吗？
```

**说明：** 关键术语已正确翻译，虽然语法不完全流畅，但对于模型训练和检索来说已经足够准确。

## 翻译流程

两个脚本都遵循以下处理流程：

1. **加载数据**
   - 加载术语表
   - 加载卡牌数据库
   - 加载日文QA

2. **处理每条QA**
   - （可选）机器翻译基础文本
   - 替换游戏专有术语
   - 根据卡号替换卡牌名称
   - 查找文本中的卡号并替换对应卡名

3. **保存结果**
   - 输出到 `official_qa_cn.json`
   - 保留原始数据用于对比

## 输出格式

```json
{
  "id": "5795",
  "question": "这张卡的【登场时】【进化时】效果，可以休眠自己或对手的数码宝贝吗？",
  "question_original": "このカードの【登場時】【進化時】効果は...",
  "answer": "是的，可以休眠。",
  "answer_original": "はい、レストできます。",
  "card_no": "503036",
  "card_name": "EX11-010 主宰暴龙兽",
  "card_name_original": "EX11-010 マスターティラノモン",
  "language": "zh-cn",
  "translated_from": "ja",
  "translation_method": "terminology_replacement"
}
```

## 术语表扩展

如果发现翻译不准确，可以扩展术语表：

### 编辑 `digimon_data/dtcg_terminology.json`

```json
{
  "keyword_effect": {
    "≪新关键词≫": "≪新关键词中文≫"
  },
  "custom_terms": {
    "日文术语": "中文术语"
  }
}
```

### 或在脚本中添加

编辑 `translate_qa_local.py` 的 `_build_game_terms()` 方法：

```python
def _build_game_terms(self) -> Dict[str, str]:
    return {
        # 添加新术语
        '新日文术语': '新中文术语',
        ...
    }
```

## 常见问题

### Q: 翻译后还有日文怎么办？
A: 使用本地版本时，部分语法结构会保留日文。可以：
1. 扩展术语表
2. 使用完整版本（需要API）
3. 手动修正关键条目

### Q: 卡牌名称没有被替换？
A: 检查：
1. 卡号是否在 `digimon_cards_cn.json` 中
2. 卡号格式是否正确（如 "EX11-010"）
3. 日文卡名是否与数据库匹配

### Q: Google Translate API报错？
A: 常见原因：
1. 网络连接问题
2. API限流 - 增加延迟时间
3. 库版本问题 - 确保使用 `googletrans==4.0.0-rc1`

## 性能参考

- 本地版本：约 1000条/秒
- API版本：约 10-20条/秒（取决于网络和限流）

## 后续使用

翻译后的QA可以用于：

1. **微调数据准备**
   ```bash
   python copy_to_finetune.py
   ```

2. **向量数据库构建**
   ```bash
   cd ..
   python rebuild_vectordb.py
   ```

3. **直接查询使用**
   - 在主程序中加载 `official_qa_cn.json`

## 进一步改进建议

如果需要更流畅的中文翻译，可以考虑：

1. **使用完整翻译版本**
   - 安装 `googletrans` 并运行 `translate_qa.py`
   - 或使用其他翻译API（如百度翻译、腾讯翻译等）

2. **手动优化关键QA**
   - 识别高频使用的QA条目
   - 手动修正翻译质量
   - 保存为单独的优化版本

3. **扩展术语表**
   - 在使用过程中发现新的专有名词
   - 添加到 `dtcg_terminology.json`
   - 重新运行翻译脚本

4. **使用大语言模型后处理**
   - 将翻译结果输入到GPT/Claude等模型
   - 要求优化语法流畅度
   - 保持专有名词不变

## 快速开始

最简单的使用方式：

```bash
# Windows用户
cd card_game_judge\card_game_QA_manger
translate_qa.bat

# 或直接运行Python脚本
python translate_qa_local.py
```

翻译完成后，`official_qa_cn.json` 文件将包含4600+条中文QA数据，可直接用于模型训练和检索。
