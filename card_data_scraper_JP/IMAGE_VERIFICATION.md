# 图片 URL 验证报告

**验证日期:** 2026-03-13  
**验证人:** 工程师 B  
**目标网站:** https://digimoncard.com

---

## 1. 图片 URL 格式

### 列表页图片 URL
从卡牌列表页提取的图片 URL 格式：
```
https://digimoncard.com/images/cardlist/card/{CARD_NO}.png?{version}
```

**示例:**
- `https://digimoncard.com/images/cardlist/card/EX11-001.png?02`
- `https://digimoncard.com/images/cardlist/card/EX11-002.png?02`

### URL 提取位置
在 `scraper.py` 中，图片 URL 从以下位置提取：

1. **列表页** (第 204-207 行，`_parse_card_element` 方法):
```python
try:
    img_elem = elem.find_element(By.TAG_NAME, "img")
    image_url = img_elem.get_attribute("src")
except NoSuchElementException:
    image_url = None
```

2. **详情页** (第 337-341 行，`_parse_card_detail_page` 方法):
```python
try:
    img_elem = self.driver.find_element(By.CSS_SELECTOR, ".card_img img, .cardimage img, .detail_image img")
    details["image_url"] = img_elem.get_attribute("src")
except NoSuchElementException:
    pass
```

---

## 2. URL 有效性测试

### 测试方法
使用 PowerShell `Invoke-WebRequest` 测试图片 URL 是否可访问。

### 测试结果

| 测试项目 | 结果 |
|---------|------|
| URL 格式 | ✅ 有效 |
| HTTP 状态码 | ✅ 200 OK |
| 可直接下载 | ✅ 是 |
| 需要认证 | ❌ 否 |
| 图片大小 | ✅ 正常 (约 78KB) |

### 测试命令
```powershell
$url = "https://digimoncard.com/images/cardlist/card/EX11-001.png?02"
Invoke-WebRequest -Uri $url -OutFile "test_image.png" -UseBasicParsing
```

### 下载结果
```
Downloaded to: D:\LLMProject\dtcg_judger\card_data_scraper_JP\test_image.png
Name           Length
----           ------
test_image.png  79944
```

---

## 3. 卡牌元素结构

列表页卡牌元素结构：
```html
<li class="image_lists_item data page-1">
  <a href="javascript:void(0);">
    <img src="https://digimoncard.com/images/cardlist/card/EX11-001.png?02" 
         alt="EX11-001コロモン">
  </a>
</li>
```

**关键信息:**
- 卡牌编号从 `alt` 属性提取：`EX11-001コロモン`
- 图片 URL 从 `src` 属性提取
- 链接使用 `javascript:void(0)`，点击后触发模态框或 JS 事件

---

## 4. 注意事项

1. **URL 版本参数**: 图片 URL 带有 `?02` 等版本参数，可能是缓存控制
2. **无图占位符**: 部分卡牌显示 `noimage.png`，需要跳过或标记
3. **跨域访问**: 图片可直接下载，无需处理 CORS 或认证
4. **网站结构**: 网站使用 JavaScript 动态加载，爬虫需使用 Selenium

---

## 5. 结论

✅ **图片 URL 有效，可以直接用于下载**

建议：
- 使用列表页的 `img src` 作为主要图片源
- 详情页作为备用源（如果需要更高分辨率）
- 下载前检查 URL 是否包含 `noimage.png`

---

**下一步:** 创建 `image_downloader.py` 模块
