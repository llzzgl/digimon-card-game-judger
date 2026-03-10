# Git 提交策略

**目标**: 有序提交重构成果到远程仓库

---

## 📋 提交计划

### 提交 1: 清理冗余文件
```bash
git add -u
git commit -m "chore: 清理冗余文件 - 删除 60+ 个重复/乱码文档"
```

### 提交 2: Skill 提取
```bash
git add skill/
git commit -m "feat: 提取 OpenClaw Skill - 10,135 张卡牌 + 4,636 条裁定"
```

### 提交 3: 结构重组
```bash
git add src/
git commit -m "refactor: 项目结构重组 - 创建 src/ 模块化目录"
```

### 提交 4: RAG 优化
```bash
git add card_game_judge/app/rag/*.py
git commit -m "feat: RAG 系统优化 - 思维链 + 精确匹配 + 分块策略"
```

### 提交 5: 文档更新
```bash
git add *.md
git commit -m "docs: 添加重构文档和迁移报告"
```

---

## 🚀 推送策略

### 方案 A: 推送到 dev 分支 (推荐)
```bash
git checkout -b dev
git push origin dev
```

### 方案 B: 更新 main 分支
```bash
git checkout main
git merge dev
git push origin main
```

---

## ⏰ 执行时间

预计 10-15 分钟完成所有提交和推送。
