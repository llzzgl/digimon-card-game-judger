# DTCG Judger 项目 - 定时任务配置说明

**配置日期**: 2026-03-13  
**项目位置**: `D:\LLMProject\dtcg_judger`  
**配置人**: 管理者 🎯

---

## 📋 定时任务总览

| 任务名称 | 执行周期 | 负责人 | 状态 |
|----------|----------|--------|------|
| DTCG 项目进度报告 | 每 40 分钟 | manager | ✅ 已配置 |
| 图片下载任务 - 进度检查和验证 | 每 30 分钟 | manager | ✅ 已配置 |

---

## 🎯 任务 1: DTCG 项目进度报告

### 基本信息
- **Job ID**: `a2bcb7e0-834a-4a47-ba9d-52cce1a7df5f`
- **执行周期**: 每 40 分钟（cron: `0 */40 * * * *`）
- **时区**: Asia/Shanghai
- **Session 目标**: isolated（隔离会话）
- **超时时间**: 180 秒

### 任务职责

1. **项目范围**: 整个 DTCG Judger 项目
2. **检查内容**:
   - 总体进度百分比
   - 各团队成员状态（工程师 A/B/C/D、测试者）
   - 已完成任务清单
   - 进行中任务状态
   - 待执行任务
   - Git 状态检查
   - 下一步行动建议

3. **参考文档**:
   - `D:\LLMProject\dtcg_judger\DTCG 重构进度报告.md`
   - `D:\LLMProject\dtcg_judger\TASK_ASSIGNMENT_REPORT.md`
   - `D:\LLMProject\dtcg_judger\TASK_CHECKLIST.md`
   - 最新的 `PROGRESS_REPORT_*.md` 文件

4. **输出要求**:
   - 使用 Markdown 格式
   - 包含清晰的进度表格
   - 标注关键里程碑
   - 如果有停滞任务，发出催促通知
   - 更新 `DTCG 重构进度报告.md` 文件

### 团队成员职责

| 成员 | 职责范围 | 当前状态 |
|------|----------|----------|
| 工程师 A | 结构优化、API 模式分离、模糊查询 | ✅ v2.0.1 已完成 |
| 工程师 B | RAG 优化、别名映射表、搜索功能 | ✅ v2.0.1 已完成 |
| 工程师 C | 爬虫 Skill 化重构 | ✅ 已完成（8/8 测试通过） |
| 工程师 D | 翻译 Skill 化重构 | ✅ 已完成（23/23 测试通过） |
| 测试者 | 功能验证测试 | ✅ v2.0.1 验证完成 |
| 测试者 2 | Skill 验证测试 | ✅ 爬虫/翻译 Skill 验证完成 |

### 项目里程碑

| 版本 | 状态 | 完成时间 | 说明 |
|------|------|----------|------|
| v2.0.0 | ✅ 已发布 | 2026-03-11 23:30 | 性能优化 + 模糊查询 + API 模式分离 |
| v2.0.1 | ✅ 已发布 | 2026-03-13 09:35 | 别名映射修复 + 纠错模式修复 |
| Scraper Skill v1.0.0 | ✅ 已完成 | 2026-03-12 09:30 | 爬虫功能 Skill 化 |
| Translation Skill v1.0.0 | ✅ 已完成 | 2026-03-12 09:30 | 翻译功能 Skill 化 |

---

## 🖼️ 任务 2: 图片下载任务 - 进度检查和验证

### 基本信息
- **Job ID**: `e0b54d3c-d4e5-4fa9-b236-8322903278ec`
- **执行周期**: 每 30 分钟（cron: `0 */30 * * * *`）
- **时区**: Asia/Shanghai
- **Session 目标**: isolated（隔离会话）
- **超时时间**: 120 秒

### 任务职责

1. **检查范围**:
   - 日文图片目录：`card_data/images/jp/raw/`
   - 中文图片目录：`card_data/images/cn/raw/`
   - 图片下载 Skill: `image_downloader_skill/`

2. **报告内容**:
   - 日文图片数量统计（目标：≥10 张）
   - 中文图片数量统计（目标：≥10 张）
   - 与上次检查的增量对比
   - 图片文件列表（最新 10 个）
   - 下载任务状态（停滞/进行中/已完成）

3. **验证任务**（当图片数量达标时触发）:
   - 检查图片文件是否可打开
   - 验证图片与卡牌数据的关联
   - 生成验证报告：`card_data/images/VALIDATION_REPORT.md`

4. **参考文档**:
   - `image_downloader_skill/SKILL.md`
   - `card_data_scraper_JP/IMAGE_VERIFICATION.md`
   - `digimon_card_data_chiness/IMAGE_ANALYSIS.md`
   - 最新的 `PROGRESS_ALERT_*.md` 文件

5. **输出要求**:
   - 使用 Markdown 格式
   - 包含进度表格和状态标识
   - 如果进度停滞（>30 分钟无新增），发出催促通知
   - 更新 `PROGRESS_ALERT_YYYY-MM-DD_HHMM.md` 文件

### 职责划分

| 成员 | 负责区域 | 目标 | 检查路径 |
|------|----------|------|----------|
| 工程师 A | 中文图片下载 | ≥10 张 | `digimon_card_data_chiness/` |
| 工程师 B | 日文图片下载 | ≥10 张 | `card_data_scraper_JP/` |
| 测试者 | 图片验证任务 | - | `card_data/images/` |

### 图片 URL 格式

**日文图片** (digimoncard.com):
```
https://digimoncard.com/images/cardlist/card/{CARD_NO}.png?{version}
示例：https://digimoncard.com/images/cardlist/card/EX11-001.png?02
```

**中文图片** (app.digicamoe.cn):
```
https://dtcg-wechat.moecard.cn/img/card/{id}_{version}.{hash}.jpg~card.jpg
需要从页面提取内部 ID 和 hash
```

### 输出文件命名

- **日文**: `{CARD_NO}_v{version}.png` (例：`EX11-001_v02.png`)
- **中文**: `{CARD_NO}.jpg` (例：`BT25-044.jpg`)

---

## 📁 项目目录结构

```
D:\LLMProject\dtcg_judger\
├── src/                          # 重构后主代码
│   ├── judger/                   # 智能裁判核心
│   │   ├── api/                  # API 路由
│   │   ├── llm/                  # LLM 服务
│   │   ├── memory/               # 记忆管理
│   │   ├── query/                # 查询处理
│   │   └── rag/                  # RAG 检索
│   ├── scraper/                  # 数据爬取
│   └── translation/              # 翻译工具
├── card_game_judge/              # 原有系统 (保留兼容)
├── skill/                        # Skill 包
├── scraper_skill/                # 爬虫 Skill (新建)
├── translation_skill/            # 翻译 Skill (新建)
├── image_downloader_skill/       # 图片下载 Skill (新建)
├── db_updater_skill/             # 数据库更新 Skill
├── card_data/                    # 卡牌数据
│   └── images/
│       ├── jp/raw/               # 日文图片
│       └── cn/raw/               # 中文图片
├── card_data_scraper_JP/         # 日文爬虫
├── digimon_card_data_chiness/    # 中文爬虫
├── digimon_data/                 # 数码兽名称映射
├── scripts/                      # 工具脚本
└── [报告文档]
```

---

## ⚠️ 重要规则

### 1. 项目范围限制

- **只处理 DTCG Judger 项目相关任务**
- 所有路径都在 `D:\LLMProject\dtcg_judger`
- 如果有其他项目任务，会由其他 Agent 处理
- 不要越界处理非 DTCG 项目的事务

### 2. 上下文和历史记录

- 每次执行前必须阅读最新的进度报告
- 保持任务连续性，避免重复工作
- 如果有任务偏移，立即纠正并记录原因
- 所有变更都要更新到相应的报告文档

### 3. 报告格式规范

- 使用 Markdown 格式
- 包含清晰的进度表格
- 标注关键里程碑和完成时间
- 突出显示需要立即行动的任务
- 保持报告简洁但信息完整

### 4. 催促通知机制

- 如果任务停滞 >30 分钟，发出催促通知
- 使用 `PROGRESS_ALERT_YYYY-MM-DD_HHMM.md` 格式
- 包含具体的解决方案建议
- 明确时间节点和责任人

---

## 🔧 Cron 任务管理命令

### 查看任务列表
```bash
openclaw cron list
```

### 查看任务详情
```bash
openclaw cron runs --jobId <job-id>
```

### 手动触发任务
```bash
openclaw cron run --jobId <job-id>
```

### 删除任务
```bash
openclaw cron remove --jobId <job-id>
```

### 更新任务
```bash
openclaw cron update --jobId <job-id> --patch '<json-patch>'
```

---

## 📊 当前 Cron 任务状态

| Job ID | 名称 | 周期 | 下次执行 | 状态 |
|--------|------|------|----------|------|
| `a2bcb7e0-834a-4a47-ba9d-52cce1a7df5f` | DTCG 项目进度报告 | 40 分钟 | 动态计算 | ✅ 启用 |
| `e0b54d3c-d4e5-4fa9-b236-8322903278ec` | 图片下载任务 - 进度检查和验证 | 30 分钟 | 动态计算 | ✅ 启用 |

---

## 📝 更新日志

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-03-13 10:44 | 重新配置定时任务 | 删除旧任务，创建新的整合任务 |
| 2026-03-13 10:44 | 创建 DTCG 项目进度报告 | 每 40 分钟汇报整体项目进度 |
| 2026-03-13 10:44 | 创建图片下载任务检查 | 每 30 分钟检查图片下载进度 |

---

*本文档由 DTCG Judger 项目管理团队维护*  
*最后更新：2026-03-13 10:44 (Asia/Shanghai)*
