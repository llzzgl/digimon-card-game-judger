# 快速开始指南

## 5 分钟上手 Scraper Skill

### 1. 安装依赖

```bash
cd D:\LLMProject\dtcg_judger
pip install selenium webdriver-manager requests beautifulsoup4
```

### 2. 运行测试

确保一切正常：

```bash
python scraper_skill/tests/test_scrapers.py
```

看到 `🎉 所有测试通过！` 即表示安装成功。

### 3. 爬取中文卡牌

创建脚本 `my_scraper.py`：

```python
from pathlib import Path
import sys

# 添加路径
sys.path.insert(0, "scraper_skill")

from src.utils.cn_scraper import ChineseCardScraper

# 配置
config = {
    "headless": True,  # 无头模式（不显示浏览器）
    "output_path": "digimon_cards_cn.json",
}

# 创建爬虫
scraper = ChineseCardScraper(config)

# 爬取（max_pages=None 表示爬取所有）
new_count = scraper.scrape_all_cards(max_pages=5)

print(f"✓ 新增 {new_count} 张卡牌")

# 清理
scraper.close()
```

运行：

```bash
python my_scraper.py
```

### 4. 爬取 QA 裁定

```python
from pathlib import Path
import sys

sys.path.insert(0, "scraper_skill")

from src.qa_scraper import QAScraper

config = {
    "headless": True,
    "output_path": "rulings.json",
}

scraper = QAScraper(config)
new_count = scraper.scrape_japanese_official()

print(f"✓ 新增 {new_count} 条 QA")
scraper.close()
```

### 5. 使用统一接口

```python
from pathlib import Path
import sys

sys.path.insert(0, "scraper_skill")

from src.card_scraper import CardScraper

config = {
    "output_path": "skill/data/cards.json",
}

scraper = CardScraper(config)

# 爬取中文卡牌
scraper.scrape_chinese(max_pages=10)

# 验证数据
report = scraper.validate_cards()
print(f"✓ 验证完成：{report['valid']} 有效 / {report['invalid']} 无效")
```

### 6. 查询数据

```python
import json

# 加载卡牌数据
with open("skill/data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

# 查找特定卡牌
for card in cards:
    if card.get("card_no") == "BT24-001":
        print(f"找到卡牌：{card['card_name']}")
        print(f"效果：{card.get('effect', '')}")
        break

# 加载 QA 数据
with open("skill/data/rulings.json", "r", encoding="utf-8") as f:
    rulings = json.load(f)

# 查找特定卡牌的 QA
card_rulings = [q for q in rulings if q.get("card_no") == "BT24-001"]
print(f"BT24-001 有 {len(card_rulings)} 条裁定")
```

## 常见问题

### Q: 浏览器启动失败？

A: 确保已安装 Chrome 浏览器，并检查 ChromeDriver 版本是否匹配。

### Q: 爬取速度慢？

A: 这是正常的，爬虫包含延迟以避免对服务器造成压力。不要移除延迟。

### Q: 如何增量爬取？

A: 中文爬虫和 QA 爬虫自动支持增量爬取，会跳过已存在的卡牌/QA。

### Q: 数据保存在哪里？

A: 默认保存在配置的 `output_path`，可以通过配置修改。

## 下一步

- 查看 `README.md` 了解完整 API
- 查看 `examples.py` 查看更多示例
- 查看 `SCRAPER_SKILL_REPORT.md` 了解重构详情

## 获取帮助

如有问题，请查看日志输出或检查：
1. 网络连接是否正常
2. Chrome 浏览器是否已安装
3. 目标网站是否可访问
4. 依赖是否已正确安装
