# 数码宝贝卡牌爬虫

爬取 digimoncard.com 官网的卡牌信息。

## 安装依赖

```bash
pip install -r requirements.txt
```

还需要安装 Chrome 浏览器和对应版本的 ChromeDriver。

## 使用方法

### 爬取指定卡包
```bash
python scraper.py --category 503035
```

### 爬取所有卡包
```bash
python scraper.py
```

### 限制爬取数量（测试用）
```bash
python scraper.py --max-packs 3
```

### 显示浏览器窗口
```bash
python scraper.py --no-headless
```

## 数据字段说明

### 卡包 (CardPack)
| 字段 | 说明 |
|------|------|
| pack_id | 卡包ID (category参数值) |
| pack_name | 卡包名称 |
| pack_code | 卡包代码 (如 BT-24) |
| release_date | 发售日期 |
| pack_url | 卡包页面URL |
| card_count | 卡牌数量 |

### 卡牌 (Card)
| 字段 | 说明 |
|------|------|
| card_no | 卡牌编号 |
| card_name | 卡牌名称 |
| card_type | 类型 (デジモン/オプション/テイマー/デジタマ) |
| color | 颜色 |
| level | 等级 |
| cost | 登场费用 |
| dp | DP值 |
| effect | 效果文本 |
| rarity | 稀有度 |
| image_url | 卡图URL |

## 输出文件

- `*_packs.json` - 卡包数据
- `*_cards.json` - 卡牌数据  
- `*_summary.json` - 汇总信息
