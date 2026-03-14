# DTCG 卡牌图片下载 Skill

## 功能说明

本 Skill 提供 DTCG 数码宝贝卡牌图片的批量下载功能，支持中文和日文两个官方来源。

## 目录结构

```
image_downloader_skill/
├── SKILL.md                    # 本文档
├── requirements.txt            # Python 依赖
├── src/
│   ├── __init__.py
│   ├── downloader.py           # 主下载器
│   ├── cn_downloader.py        # 中文图片下载器
│   └── jp_downloader.py        # 日文图片下载器
├── config/
│   └── config.py               # 配置管理
└── examples/
    └── download_example.py     # 使用示例
```

## 使用方法

### 快速开始

```python
from image_downloader_skill.src.downloader import DTCGImageDownloader

# 初始化下载器
downloader = DTCGImageDownloader(
    cn_output_dir="card_data/images/cn/raw",
    jp_output_dir="card_data/images/jp/raw"
)

# 下载日文图片（EX11 系列前 10 张）
downloader.download_jp_cards(series="EX11", count=10)

# 下载中文图片（BT25 系列前 10 张）
downloader.download_cn_cards(series="BT25", count=10)
```

### 命令行使用

```bash
# 下载日文图片
python -m image_downloader_skill.src.downloader --lang jp --series EX11 --count 10

# 下载中文图片
python -m image_downloader_skill.src.downloader --lang cn --series BT25 --count 10

# 同时下载两种语言
python -m image_downloader_skill.src.downloader --lang both --count 10
```

## 配置说明

### 日文图片 (digimoncard.com)

- **URL 格式**: `https://digimoncard.com/images/cardlist/card/{CARD_NO}.png?{version}`
- **版本参数**: 默认为 `02`
- **卡牌编号格式**: `EX11-001`, `BT25-044` 等

### 中文图片 (app.digicamoe.cn)

- **URL 格式**: `https://dtcg-wechat.moecard.cn/img/card/{id}_{version}.{hash}.jpg~card.jpg`
- **需要 Selenium**: 中文网站需要动态加载
- **卡牌编号**: 需要从页面提取内部 ID

## 输出文件命名

- **日文**: `{CARD_NO}_v{version}.png` (例：`EX11-001_v02.png`)
- **中文**: `{CARD_NO}.jpg` (例：`BT25-044.jpg`)

## 依赖

```txt
requests>=2.31.0
selenium>=4.15.0
webdriver-manager>=4.0.0
```

## 错误处理

- 自动跳过已下载的文件
- 下载失败自动重试（最多 3 次）
- 记录详细的下载日志

## 扩展性

本 Skill 设计为可扩展架构：
- 新增卡牌系列：只需在配置中添加系列代码
- 新增语言支持：添加新的 downloader 模块
- 自定义输出路径：通过构造函数参数指定

---

**版本**: 1.0.0  
**创建日期**: 2026-03-13  
**维护者**: DTCG Judger 团队
