# 数码兽卡牌中文数据爬虫

从 https://app.digicamoe.cn/search 爬取数码兽卡牌中文数据

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python scraper_v3.py
```

## 配置选项

在 `scraper_v3.py` 的 `main()` 函数中可以修改：

```python
# headless=True  无头模式（后台运行）
# headless=False 显示浏览器窗口
# max_pages=None 爬取所有页面
# max_pages=2    只爬取前2页
scraper = DigimonCardScraperV3(headless=True, max_pages=None)
```

## 输出字段

| 字段 | 说明 |
|------|------|
| url | 详情页URL |
| name_cn | 中文名 |
| name_jp | 日文名 |
| card_no | 编号 |
| type | 卡片类型 |
| rarity | 罕贵度 |
| color | 颜色 |
| level | 等级 |
| play_cost | 登场费用 |
| dp | DP值 |
| form | 形态 |
| attribute | 属性 |
| species | 种类 |
| evolution_condition | 进化条件 |
| effect | 效果 |
| inherited_effect | 进化源能力 |
| security_effect | 安防效果 |

## 输出文件

爬取完成后生成 `digimon_cards_cn_YYYYMMDD_HHMMSS.json`


## 接口服务

```
from scraper_v3 import scrape_all_cards, update_single_card, get_database

# 1. 爬取所有卡牌（翻页爬取）
db = scrape_all_cards()                    # 爬取全部
db = scrape_all_cards(max_pages=5)         # 只爬前5页
db = scrape_all_cards(headless=False)      # 显示浏览器

# 2. 更新单张卡牌
card = update_single_card("https://app.digicamoe.cn/Cards/EX-11/EX11-025/U")

# 3. 获取数据库（不启动爬虫）
db = get_database()
card = db.get_card("EX11-025")
all_cards = db.get_all_cards()
print(f"共 {db.count()} 张卡牌")
```
