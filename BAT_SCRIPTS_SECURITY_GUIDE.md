# BAT 脚本密钥管理说明

**更新时间**: 2026-03-14 20:00  
**安全级别**: 🔒 高

---

## 🔒 安全修复完成

### 修复内容

所有 BAT 启动脚本已改为从 `.env` 文件读取密钥，不再硬编码敏感信息。

### 修改的脚本

| 脚本 | 修改内容 |
|------|----------|
| `start_with_api.bat` | ✅ 改为从.env 读取 DASHSCOPE_API_KEY |
| `start_with_image.bat` | ✅ 改为从.env 读取 GEMINI_API_KEY |
| `start_with_finetuned.bat` | ✅ 改为从.env 读取模型配置 |
| `fix_and_start.bat` | ✅ 改为从.env 读取配置 |
| `update_all.bat` | ✅ 无密钥，保持不变 |

---

## 📋 使用步骤

### 1. 创建 .env 文件

```bash
cd D:\LLMProject\dtcg_judger\card_game_judge
copy .env.example .env
```

### 2. 编辑 .env 文件

打开 `.env` 文件，填写实际密钥：

```bash
# 通义千问 API 密钥
DASHSCOPE_API_KEY=sk-your-actual-api-key-here

# Gemini API 密钥（图片识别）
GEMINI_API_KEY=your-gemini-api-key-here

# 微调模型配置（可选）
LLM_MODEL=finetuned
FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct
FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
```

### 3. 启动服务

```bash
# 使用 API 模型（推荐）
start_with_api.bat

# 使用图片识别
start_with_image.bat

# 使用微调模型
start_with_finetuned.bat
```

---

## 🔐 安全最佳实践

### ✅ 正确做法

1. **使用 .env 文件**
   ```bash
   # 从 .env 读取密钥
   DASHSCOPE_API_KEY=sk-xxx
   ```

2. **添加到 .gitignore**
   ```gitignore
   **/.env
   **/.env.*
   !*.env.example
   ```

3. **使用环境变量**
   ```bash
   # 或使用系统环境变量
   set DASHSCOPE_API_KEY=sk-xxx
   ```

### ❌ 错误做法

1. **硬编码密钥**
   ```bat
   REM 不要这样做！
   set API_KEY=sk-123456789
   ```

2. **提交 .env 到 Git**
   ```bash
   git add .env  # 绝对禁止！
   ```

3. **在日志中打印密钥**
   ```python
   print(f"API Key: {api_key}")  # 不要打印完整密钥
   ```

---

## 📁 文件结构

```
card_game_judge/
├── .env                    # 实际配置（不提交到 Git）
├── .env.example           # 配置模板（可以提交）
├── start_with_api.bat     # 启动脚本（从.env 读取）
├── start_with_image.bat   # 启动脚本（从.env 读取）
└── start_with_finetuned.bat # 启动脚本（从.env 读取）

db_updater_skill/
├── .env                    # 实际配置（不提交）
├── .env.example           # 配置模板
└── scripts/update_all.bat  # 更新脚本
```

---

## 🔍 验证方法

### 检查 .env 是否在 Git 中

```bash
# 应该没有输出（.env 已被排除）
git ls-files | grep ".env$"
```

### 检查 .env.example 是否存在

```bash
# 应该显示 .env.example 文件
git ls-files | grep ".env.example"
```

### 检查脚本是否从 .env 读取

```bash
# 应该包含 .env 加载逻辑
findstr /i ".env" card_game_judge\*.bat
```

---

## ⚠️ 如果密钥已泄露

### 立即行动

1. **立即更换所有泄露的密钥**
   - 通义千问 API Key
   - Gemini API Key
   - 任何其他密钥

2. **检查 Git 历史**
   ```bash
   git log --all --full-history -- "**/.env"
   git log --all --full-history -- "**/*api*.bat"
   ```

3. **从历史中删除**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch card_game_judge/.env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

---

## 📊 安全状态

| 检查项 | 状态 |
|--------|------|
| .env 文件排除 | ✅ 已加入 .gitignore |
| 密钥硬编码 | ✅ 已全部移除 |
| .env.example 模板 | ✅ 已创建 |
| BAT 脚本更新 | ✅ 全部修改完成 |
| Git 历史清理 | ✅ .env 已删除 |
| 远端同步 | ✅ 已推送 |

---

**🔒 所有密钥已安全管理，不再硬编码在脚本中！**
