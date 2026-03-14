# 🧪 图片验证任务 - 日文图片 (EX11 系列)

**任务创建时间**: 2026-03-13 12:30  
**触发条件**: 日文图片下载完成 ≥10 张  
**验证对象**: `card_data/images/jp/raw/` 目录下的 10 张图片

---

## 📋 验证任务清单

### 任务 1: 文件完整性检查

- [ ] 确认目录中有 10 张图片文件
- [ ] 检查所有文件是否可正常打开（无损坏）
- [ ] 记录每个文件的大小和分辨率

**预期文件列表**:
```
EX11-001_v02.png  (约 78 KB)
EX11-002_v02.png  (约 89 KB)
EX11-003_v02.png  (约 88 KB)
EX11-004_v02.png  (约 79 KB)
EX11-005_v02.png  (约 103 KB)
EX11-006_v02.png  (约 100 KB)
EX11-007_v02.png  (约 69 KB)
EX11-008_v02.png  (约 73 KB)
EX11-009_v02.png  (约 92 KB)
EX11-010_v02.png  (约 101 KB)
```

---

### 任务 2: 图片内容验证

- [ ] 逐一打开每张图片，确认内容正确
- [ ] 验证图片与卡牌编号的对应关系
- [ ] 检查图片是否为正确的 EX11 系列卡牌

**验证方法**:
1. 使用图片查看器打开文件
2. 对比卡牌编号与图片内容
3. 确认图片显示的是对应的数码宝贝卡牌

**参考数据**: `card_data_scraper_JP/cards_JP_EX11.json`

---

### 任务 3: 图片质量检查

- [ ] 检查图片分辨率（预期：约 600x800 或更高）
- [ ] 检查图片清晰度（无明显模糊或压缩痕迹）
- [ ] 检查图片完整性（无缺失、无损坏）

**技术规格**:
- 格式：PNG
- 来源：https://digimoncard.com
- 版本：v02

---

### 任务 4: 数据关联验证

- [ ] 确认每张图片在卡牌数据 JSON 中有对应记录
- [ ] 验证图片命名与卡牌编号一致
- [ ] 检查是否有遗漏的卡牌

**关联数据文件**:
- `card_data_scraper_JP/cards_JP_EX11.json`
- `card_data_scraper_JP/IMAGE_VERIFICATION.md`

---

## 📝 验证报告模板

完成验证后，请复制以下模板并填写：

```markdown
# 图片验证报告 - 日文 EX11 系列

**验证时间**: YYYY-MM-DD HH:MM  
**验证人**: [姓名/角色]

## 验证结果

| 文件 | 大小 (KB) | 可打开 | 内容正确 | 质量合格 | 备注 |
|------|-----------|--------|----------|----------|------|
| EX11-001_v02.png | | ✅/❌ | ✅/❌ | ✅/❌ | |
| EX11-002_v02.png | | ✅/❌ | ✅/❌ | ✅/❌ | |
| ... | | | | | |

## 总体评价

- **文件总数**: 10 张
- **可正常打开**: X 张
- **内容正确**: X 张
- **质量合格**: X 张
- **通过率**: XX%

## 问题记录

[如有问题，请详细描述]

## 结论

- [ ] ✅ 所有图片验证通过，可以用于项目
- [ ] ⚠️ 部分图片有问题，需要重新下载
- [ ] ❌ 验证失败，需要重新检查

## 建议

[如有建议，请填写]
```

---

## 🔧 验证工具

### PowerShell 快速检查脚本

```powershell
# 检查文件数量和大小
$files = Get-ChildItem "D:\LLMProject\dtcg_judger\card_data\images\jp\raw\*.png"
$files | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB,1)}}, CreationTime | Format-Table

# 检查文件是否可读取
foreach ($file in $files) {
    try {
        $bmp = [System.Drawing.Bitmap]::FromFile($file.FullName)
        Write-Host "$($file.Name): ✅ $($bmp.Width)x$($bmp.Height)"
        $bmp.Dispose()
    } catch {
        Write-Host "$($file.Name): ❌ $($_.Exception.Message)"
    }
}
```

### Python 验证脚本

```python
from PIL import Image
from pathlib import Path

img_dir = Path("D:/LLMProject/dtcg_judger/card_data/images/jp/raw")
for img_path in img_dir.glob("*.png"):
    try:
        with Image.open(img_path) as img:
            print(f"✅ {img_path.name}: {img.size[0]}x{img.size[1]}")
    except Exception as e:
        print(f"❌ {img_path.name}: {e}")
```

---

## 📚 参考文档

- `image_downloader_skill/SKILL.md` - 图片下载器使用说明
- `card_data_scraper_JP/IMAGE_VERIFICATION.md` - 日文图片 URL 验证报告
- `PROGRESS_ALERT_2026-03-13_1230.md` - 最新进度报告

---

## ⏰ 时间要求

- **开始时间**: 立即开始
- **预计完成**: 15-30 分钟
- **最晚完成**: 2026-03-13 13:00

---

## 📞 问题反馈

如遇到问题，请在进度汇报中说明：

```markdown
### 验证问题反馈 - [时间]

**验证人**: [姓名]
**问题描述**: [详细描述]
**影响范围**: [哪些文件/功能受影响]
**建议解决方案**: [如有]
```

---

*验证完成后，请将报告保存为 `card_data/images/VALIDATION_REPORT_JP.md`*
