# DTCG 卡牌数据翻译工具

将日文 DTCG（数码宝贝卡牌游戏）卡牌数据翻译成中文。

## 翻译策略

1. **数码宝贝名称**: 使用数码宝贝图鉴官网 (http://digimons.net/digimon/chn.html) 的官方中文名称
2. **游戏术语**: 使用 DTCG 规则书中的专有名词对照表
3. **效果文本**: 先用术语表替换，再用 AI 翻译剩余日文

## 文件说明

| 文件 | 说明 |
|------|------|
| `digimon_name_mapping.json` | 数码宝贝日文-中文名称映射 |
| `dtcg_terminology.py` | DTCG 专有名词术语表 |
| `dtcg_terminology.json` | 术语表 JSON 格式 |
| `card_translator.py` | 卡牌翻译器核心代码 |
| `translate_cards.py` | 翻译主程序 |
| `digimon_name_scraper.py` | 数码宝贝图鉴爬虫（可选） |

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# Gemini API (推荐)
GOOGLE_API_KEY=your_google_api_key

# 或 OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 代理设置（可选）
USE_PROXY=false
PROXY_HOST=127.0.0.1
PROXY_PORT=7897
```

### 3. 运行翻译

```bash
cd digimon_data
python translate_cards.py
```

翻译后的文件将保存在 `translated_cards/` 目录。

## 翻译字段对照

| 日文字段 | 中文字段 | 说明 |
|----------|----------|------|
| card_name | card_name | 卡牌名称（翻译后） |
| card_name_jp | - | 保留的日文原名 |
| card_type | card_type | 卡牌类型 |
| color | color | 颜色 |
| form | form | 形态 |
| attribute | attribute | 属性 |
| digimon_type | digimon_type | 数码宝贝类型 |
| effect | effect | 效果（翻译后） |
| effect_jp | - | 保留的日文效果 |
| inherited_effect | inherited_effect | 进化源效果 |
| security_effect | security_effect | 安防效果 |

## 术语对照表

### 卡牌类型
- デジタマ → 数码蛋
- デジモン → 数码宝贝
- テイマー → 驯兽师
- オプション → 选项

### 颜色
- 赤 → 红
- 青 → 蓝
- 黄 → 黄
- 緑 → 绿
- 黒 → 黑
- 紫 → 紫
- 白 → 白

### 形态
- 幼年期 → 幼年期
- 成長期 → 成长期
- 成熟期 → 成熟期
- 完全体 → 完全体
- 究極体 → 究极体

### 属性
- ワクチン種 → 疫苗种
- データ種 → 数据种
- ウィルス種 → 病毒种
- フリー種 → 自由种

## 扩展名称映射

如需添加更多数码宝贝名称映射，编辑 `digimon_name_mapping.json`：

```json
{
  "日文名": "中文名",
  "アグモン": "亚古兽"
}
```

## 注意事项

1. AI 翻译需要网络连接和有效的 API Key
2. 大量翻译可能产生 API 费用
3. 建议先用小批量测试翻译效果
4. 翻译结果保留日文原文便于校对
