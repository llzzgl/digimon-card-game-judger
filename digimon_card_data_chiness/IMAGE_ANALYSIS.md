# 卡牌图片 URL 结构分析

**分析日期:** 2026-03-13  
**分析网站:** https://app.digicamoe.cn  
**分析页面:** 卡牌详情页 (例如：https://app.digicamoe.cn/Cards/BT-25/BT25-044/SR)

---

## 1. 图片 URL 格式

### 基本格式
```
https://dtcg-wechat.moecard.cn/img/card/{id}_{version}.{hash}.jpg~card.jpg
```

### 示例 URL
```
https://dtcg-wechat.moecard.cn/img/card/12617_19775.MRqPzaYHOV6.jpg~card.jpg
https://dtcg-wechat.moecard.cn/img/card/12618_19776.MBwrrI7UuOX.jpg~card.jpg
```

### URL 组成部分
| 部分 | 说明 | 示例 |
|------|------|------|
| 域名 | 图片 CDN 域名 | `dtcg-wechat.moecard.cn` |
| 路径 | 固定路径 | `/img/card/` |
| ID | 卡牌内部 ID | `12617` |
| Version | 版本号 | `19775` |
| Hash | 随机哈希值 | `MRqPzaYHOV6` |
| 后缀 | 固定后缀 | `.jpg~card.jpg` |

---

## 2. HTML 元素特征

### 图片元素示例
```html
<img alt="ユノモン" 
     title="朱诺兽的卡图" 
     src="https://dtcg-wechat.moecard.cn/img/card/12617_19775.MRqPzaYHOV6.jpg~card.jpg" 
     style="max-width:99%;" 
     data-v-09c2dcb4="" 
     class="lazyLoad isLoaded">
```

### 关键属性
| 属性 | 说明 | 示例值 |
|------|------|--------|
| `class` | 包含 `lazyLoad` 类 | `lazyLoad isLoaded` |
| `alt` | 卡牌日文名 | `ユノモン` |
| `title` | 卡牌中文名 + "的卡图" | `朱诺兽的卡图` |
| `src` | 图片完整 URL | `https://dtcg-wechat.moecard.cn/img/card/...` |
| `data-src` | 懒加载时的占位符（可能不存在） | `null` 或实际 URL |

---

## 3. 提取方法

### 方法 1: CSS 选择器（推荐）
```python
# 查找带有 lazyLoad 类的图片
img_element = driver.find_element(By.CSS_SELECTOR, "img.lazyLoad")
image_url = img_element.get_attribute("src")
```

### 方法 2: 通过 title 属性
```python
# 查找 title 包含"卡图"的图片
img_element = driver.find_element(By.XPATH, "//img[contains(@title, '卡图')]")
image_url = img_element.get_attribute("src")
```

### 方法 3: 通过 alt 属性（日文名）
```python
# 查找有 alt 属性的图片（排除 logo 等）
img_elements = driver.find_elements(By.CSS_SELECTOR, "img[alt]")
for img in img_elements:
    alt = img.get_attribute("alt")
    src = img.get_attribute("src")
    if src and "dtcg-wechat.moecard.cn" in src:
        image_url = src
        break
```

---

## 4. 实现建议

### 在 scraper_v3.py 中的集成
在 `extract_card_detail` 方法中添加：

```python
def extract_card_detail(self, driver):
    """提取卡牌详情"""
    try:
        time.sleep(2)
        page_title = driver.title
        url = driver.current_url
        body = driver.find_element(By.TAG_NAME, 'body')
        full_text = body.text
        
        card_info = self.parse_card_info(full_text, page_title, url)
        
        # 提取图片 URL
        image_url = self.extract_image_url(driver)
        card_info['image_url'] = image_url
        
        return card_info
    except Exception as e:
        return {'error': str(e), 'url': driver.current_url}

def extract_image_url(self, driver):
    """提取卡牌图片 URL"""
    try:
        # 方法 1: 通过 lazyLoad class
        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.lazyLoad")
        for img in img_elements:
            src = img.get_attribute("src")
            if src and "dtcg-wechat.moecard.cn" in src:
                return src
        
        # 方法 2: 通过 title 属性
        img_element = driver.find_element(By.XPATH, "//img[contains(@title, '卡图')]")
        return img_element.get_attribute("src")
    except:
        return ""
```

---

## 5. 注意事项

1. **懒加载**: 图片可能使用懒加载，需要等待 `isLoaded` class 出现
2. **多版本**: 同一卡牌可能有多个版本（普通版、异画版等），每个版本有不同 URL
3. **CDN 稳定性**: 图片托管在外部 CDN，下载时应考虑重试机制
4. **文件名生成**: 建议使用卡牌编号作为文件名，如 `BT25-044.jpg`

---

## 6. 测试用例

| 卡牌编号 | 预期图片 URL 前缀 | 状态 |
|----------|------------------|------|
| BT25-044 | `https://dtcg-wechat.moecard.cn/img/card/12617_19775.*` | ✅ 已验证 |
| BT25-097 | `https://dtcg-wechat.moecard.cn/img/card/*` | ⏳ 待测试 |
| ST23-01 | `https://dtcg-wechat.moecard.cn/img/card/*` | ⏳ 待测试 |
