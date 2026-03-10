# 快速开始 - QA翻译工具

## 三步开始使用

### 1️⃣ 安装依赖（1分钟）

```bash
cd card_game_judge\card_game_QA_manger
install_deps.bat
```

### 2️⃣ 配置密钥（1分钟）

编辑 `card_game_judge\.env`，添加：
```
DASHSCOPE_API_KEY=sk-你的通义千问密钥
```

### 3️⃣ 开始翻译（1分钟）

```bash
python translate_qa_with_terminology.py
```
选择：`1` (Qwen) → `1` (测试10条)

---

## 完整命令速查

| 操作 | 命令 | 说明 |
|------|------|------|
| 安装依赖 | `install_deps.bat` | 一键安装所有依赖 |
| 检查依赖 | `python check_dependencies.py` | 验证依赖是否安装 |
| 测试配置 | `python test_translation_setup.py` | 验证数据文件 |
| 一键测试 | `test_translation.bat` | 完整测试流程 |
| 翻译工具 | `python translate_qa_with_terminology.py` | 主翻译工具 |

---

## 翻译模式

| 模式 | 数量 | 用途 | 时间 |
|------|------|------|------|
| 1 - 测试 | 10条 | 验证质量 | ~1分钟 |
| 2 - 小批量 | 100条 | 快速预览 | ~10分钟 |
| 3 - 完整 | 全部 | 正式翻译 | ~5小时 |

---

## LLM选择

| LLM | 推荐度 | 优点 | 缺点 |
|-----|--------|------|------|
| 1 - Qwen | ⭐⭐⭐⭐⭐ | 国内快、质量好 | 需要API密钥 |
| 2 - Gemini | ⭐⭐⭐ | 免费、质量好 | 需要代理 |
| 3 - Ollama | ⭐⭐ | 完全免费、离线 | 需要安装、质量一般 |

---

## 常见问题

### ❓ 提示"No module named 'openai'"

```bash
pip install openai
```

### ❓ 提示"请设置DASHSCOPE_API_KEY"

在 `.env` 文件中添加：
```
DASHSCOPE_API_KEY=sk-你的密钥
```

### ❓ 如何获取通义千问API密钥？

1. 访问：https://dashscope.aliyun.com/
2. 登录/注册阿里云账号
3. 进入控制台 → API-KEY管理
4. 创建新的API-KEY

### ❓ 翻译中断了怎么办？

不用担心！再次运行翻译工具，会自动从断点继续。

### ❓ 如何重新开始翻译？

删除检查点文件：
```bash
del official_qa_cn_*_checkpoint.json
```

---

## 输出文件

翻译完成后会生成：

```
official_qa_cn_qwen.json
```

包含：
- ✅ 翻译后的问题和答案
- ✅ 原始日文（保留参考）
- ✅ 中文卡名（自动映射）
- ✅ 翻译方法标记

---

## 质量保证

翻译工具会自动：

- ✅ 使用79个游戏术语标准译名
- ✅ 自动映射卡牌中文名称
- ✅ 保持日文效果标记格式
- ✅ 确保语句流畅自然
- ✅ 保留所有原始信息

---

## 进阶使用

### 调整模型

编辑 `translate_qa_with_terminology.py` 第67行：

```python
self.model_name = "qwen-max"  # 更高质量
# 或
self.model_name = "qwen-turbo"  # 更快速度
```

### 调整批次大小

```python
translator.translate_all(
    batch_size=20,  # 每批处理20条
    delay=0.5       # 批次间延迟0.5秒
)
```

### 从指定位置开始

```python
translator.translate_all(
    start_from=100,  # 从第100条开始
    max_count=50     # 只翻译50条
)
```

---

## 文件位置

```
card_game_judge/
├── .env                              # API密钥配置
└── card_game_QA_manger/
    ├── translate_qa_with_terminology.py  # 主工具
    ├── official_qa_jp.json               # 输入
    └── official_qa_cn_qwen.json          # 输出
```

---

## 获取帮助

查看详细文档：
- `README_TRANSLATION.md` - 完整使用指南
- `INSTALL_DEPENDENCIES.md` - 依赖安装指南
- `TRANSLATION_STATUS.md` - 状态报告
- `WORKFLOW.md` - 工作流程图

---

## 一键测试脚本

```batch
@echo off
cd card_game_judge\card_game_QA_manger
echo 1. 安装依赖...
call install_deps.bat
echo.
echo 2. 测试配置...
python check_dependencies.py
echo.
echo 3. 开始翻译测试...
python translate_qa_with_terminology.py
```

保存为 `quick_test.bat`，双击运行！

---

## 成功标志

看到以下输出表示成功：

```
✓ 通义千问已初始化 (模型: qwen-plus)
✓ 加载了 79 个术语
✓ 加载了 3992 张卡牌数据
✓ 加载了 3000+ 条QA
✓ 初始化完成

[1/10] ✓
[2/10] ✓
...
✓ 翻译完成！共翻译 10 条QA
✓ 输出文件: official_qa_cn_qwen.json
```

---

## 下一步

1. ✅ 运行测试模式（10条）
2. ✅ 检查翻译质量
3. ✅ 如果满意，运行完整翻译
4. ✅ 使用翻译后的QA数据

---

**祝使用愉快！** 🎉

如有问题，请查看详细文档或检查错误信息。
