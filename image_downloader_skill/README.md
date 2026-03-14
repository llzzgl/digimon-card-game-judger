# image_downloader_skill 使用文档

## 快速开始

### 1. 安装依赖

```bash
cd D:\LLMProject\dtcg_judger
pip install -r image_downloader_skill\requirements.txt
```

### 2. 下载日文图片（推荐）

**方法 A - 使用快速脚本**:
```bash
python quick_download_images.py
```

**方法 B - 使用 Python API**:
```python
from image_downloader_skill.src.downloader import DTCGImageDownloader

# 初始化下载器
downloader = DTCGImageDownloader()

# 下载 EX11 系列前 10 张
result = downloader.download_jp_cards(series="EX11", count=10)

print(f"下载完成：{result['success']} 张")
```

**方法 C - 使用命令行**:
```bash
python -m image_downloader_skill.src.downloader --lang jp --series EX11 --count 10
```

### 3. 下载中文图片（需要 Selenium）

**安装 Selenium**:
```bash
pip install selenium webdriver-manager
```

**下载中文图片**:
```bash
python quick_download_cn_images.py
```

---

## 配置说明

### 输出目录

默认输出目录：
- **日文图片**: `D:\LLMProject\dtcg_judger\card_data\images\jp\raw\`
- **中文图片**: `D:\LLMProject\dtcg_judger\card_data\images\cn\raw\`

自定义输出目录：
```python
downloader = DTCGImageDownloader(
    cn_output_dir="D:\\custom\\cn\\output",
    jp_output_dir="D:\\custom\\jp\\output"
)
```

### 卡牌系列

支持的日文系列（部分）：
- EX 系列：EX01-EX11（最新）
- BT 系列：BT01-BT25
- ST 系列：ST01-ST23

支持的中文系列（部分）：
- BT 系列：BT01-BT25
- ST 系列：ST01-ST23

---

## API 参考

### DTCGImageDownloader

主下载器类，提供统一的下载接口。

#### 初始化

```python
downloader = DTCGImageDownloader(
    cn_output_dir: str = None,  # 中文输出目录（默认：card_data/images/cn/raw）
    jp_output_dir: str = None   # 日文输出目录（默认：card_data/images/jp/raw）
)
```

#### 方法

##### download_jp_cards(series, count, skip_existing)

下载日文卡牌图片。

```python
result = downloader.download_jp_cards(
    series="EX11",        # 系列代码
    count=10,             # 下载数量
    skip_existing=True    # 跳过已存在的文件
)
```

返回值：
```python
{
    "total": 10,          # 总尝试数量
    "success": 8,         # 成功下载数量
    "failed": 0,          # 失败数量
    "skipped": 2,         # 跳过数量（已存在）
    "files": [...]        # 下载的文件名列表
}
```

##### download_cn_cards(card_urls, output_prefix)

下载中文卡牌图片（需要 Selenium）。

```python
card_urls = [
    "https://app.digicamoe.cn/Cards/BT-25/BT25-001/C",
    "https://app.digicamoe.cn/Cards/BT-25/BT25-002/C",
]

result = downloader.download_cn_cards(
    card_urls=card_urls,      # 卡牌详情页 URL 列表
    output_prefix=""          # 输出文件名前缀
)
```

##### download_both(jp_series, jp_count, cn_urls)

同时下载日文和中文卡牌图片。

```python
results = downloader.download_both(
    jp_series="EX11",     # 日文系列
    jp_count=10,          # 日文数量
    cn_urls=[...]         # 中文 URL 列表（可选）
)

print(f"日文：{results['japanese']['success']} 张")
print(f"中文：{results['chinese']['success']} 张")
```

---

### JapaneseImageDownloader

日文图片专用下载器。

```python
from image_downloader_skill.src.jp_downloader import JapaneseImageDownloader

downloader = JapaneseImageDownloader(
    output_dir="D:\\output\\jp",
    version="02"  # 图片版本号
)

# 生成卡牌编号
cards = downloader.generate_card_numbers("EX11", 10)
# ['EX11-001', 'EX11-002', ..., 'EX11-010']

# 构建图片 URL
url = downloader.build_image_url("EX11-001")
# https://digimoncard.com/images/cardlist/card/EX11-001.png?02

# 批量下载
result = downloader.download_cards("EX11", 10)
```

---

### ChineseImageDownloader

中文图片专用下载器（需要 Selenium）。

```python
from image_downloader_skill.src.cn_downloader import ChineseImageDownloader

downloader = ChineseImageDownloader(
    output_dir="D:\\output\\cn"
)

# 从 URL 列表下载
card_urls = [
    "https://app.digicamoe.cn/Cards/BT-25/BT25-001/C",
    "https://app.digicamoe.cn/Cards/BT-25/BT25-002/C",
]

result = downloader.download_cards_from_urls(card_urls)

# WebDriver 会自动初始化和关闭
```

---

## 命令行使用

### 基本用法

```bash
# 下载日文图片
python -m image_downloader_skill.src.downloader --lang jp --series EX11 --count 10

# 下载中文图片（需要提供 URL）
python -m image_downloader_skill.src.downloader --lang cn --cn-urls URL1 URL2 URL3

# 同时下载两种语言
python -m image_downloader_skill.src.downloader --lang both --series EX11 --count 10 --cn-urls URL1 URL2
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--lang` | 下载语言：jp/cn/both | jp |
| `--series` | 日文卡牌系列代码 | EX11 |
| `--count` | 下载数量 | 10 |
| `--cn-urls` | 中文卡牌 URL 列表（空格分隔） | - |
| `--output-prefix` | 中文输出文件名前缀 | "" |

---

## 错误处理

### 常见问题

#### 1. 下载失败

**现象**: 部分图片下载失败

**原因**: 网络连接问题或网站暂时不可用

**解决**: 
- 脚本会自动重试（最多 3 次）
- 检查网络连接
- 稍后重新运行

#### 2. Selenium 未安装

**现象**: `ModuleNotFoundError: No module named 'selenium'`

**解决**:
```bash
pip install selenium webdriver-manager
```

#### 3. ChromeDriver 版本不匹配

**现象**: `WebDriverException: This version of ChromeDriver only supports...`

**解决**: webdriver-manager 会自动下载匹配的 ChromeDriver，确保 Chrome 浏览器已更新到最新版本。

#### 4. 文件已存在

**现象**: 下载统计显示"跳过"数量

**原因**: `skip_existing=True`（默认）会跳过已存在的文件

**解决**: 
- 这是正常行为，避免重复下载
- 如需强制重新下载，设置 `skip_existing=False`

---

## 扩展示例

### 添加新的卡牌系列

编辑 `image_downloader_skill/config/config.py`:

```python
JP_CONFIG = {
    "series": [
        "EX11", "EX10", ...,  # 现有系列
        "EX12", "EX13",       # 新增系列
    ]
}
```

### 自定义下载逻辑

继承基类并覆盖方法：

```python
from image_downloader_skill.src.jp_downloader import JapaneseImageDownloader

class CustomImageDownloader(JapaneseImageDownloader):
    def download_image(self, url, output_path, max_retries=5):
        # 自定义下载逻辑（如增加重试次数）
        return super().download_image(url, output_path, max_retries)
```

### 批量下载多个系列

```python
from image_downloader_skill.src.downloader import DTCGImageDownloader

downloader = DTCGImageDownloader()

series_list = ["EX11", "EX10", "EX09"]
for series in series_list:
    result = downloader.download_jp_cards(series=series, count=20)
    print(f"{series}: {result['success']} 张")
```

---

## 性能优化

### 并发下载（未来扩展）

当前版本为串行下载，未来可以添加并发支持：

```python
# 伪代码示例
from concurrent.futures import ThreadPoolExecutor

def download_concurrent(card_numbers):
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_single, card_numbers)
```

### 缓存机制

已下载的文件会自动跳过，避免重复下载。

---

## 日志配置

### 调整日志级别

```python
import logging

# 设置为 DEBUG 级别（更详细的日志）
logging.basicConfig(level=logging.DEBUG)

# 或设置为 WARNING 级别（仅警告和错误）
logging.basicConfig(level=logging.WARNING)
```

### 日志输出到文件

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)
```

---

## 版本历史

### v1.0.0 (2026-03-13)

- ✅ 初始版本
- ✅ 日文图片批量下载
- ✅ 中文图片下载（Selenium）
- ✅ 自动跳过已存在文件
- ✅ 错误重试机制
- ✅ 详细日志输出
- ✅ 可扩展架构

---

## 支持

遇到问题？

1. 查看日志输出
2. 检查网络连接
3. 确认依赖已安装
4. 查看本文档的"错误处理"部分

---

**维护者**: DTCG Judger 团队  
**最后更新**: 2026-03-13
