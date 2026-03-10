# 增强版裁判系统使用指南

**版本:** 1.0  
**日期:** 2026-03-06  
**状态:** 测试阶段

---

## 🚀 快速开始

### 安装依赖

确保已安装基础依赖：
```bash
cd card_game_judge
pip install -r requirements.txt
```

### 测试增强版裁判

```bash
# 运行完整测试套件
python test_enhanced_judge.py --all

# 测试单个问题
python main_enhanced.py --test "我方联展了 bt23-032 土偶兽，把对方的数码兽退化成 bt24-016 拉米亚兽..."

# 从文件读取测试问题
python main_enhanced.py --test-file my_question.txt
```

---

## 📋 核心改进

### 1. 增强查询处理

**文件:** `app/enhanced_query_processor.py`

自动识别：
- 效果时机（登场时/进化时/攻击时/消灭时等 12 种）
- 问题类型（顺序/时机/裁定/效果/卡牌）
- 涉及卡牌（自动提取卡号）
- 是否需要连锁分析

**示例:**
```python
from app.enhanced_query_processor import enhanced_query_processor

query = "我方联展了 bt23-032 土偶兽，对方拉米亚兽消灭时会发生什么？"
analysis = enhanced_query_processor.analyze_scenario(query)

print(analysis['question_type'])      # 输出：sequence
print(analysis['involved_cards'])     # 输出：['BT23-032', 'BT24-016']
print(analysis['needs_sequence_analysis'])  # 输出：True
```

---

### 2. 场面分析器

**文件:** `app/scenario_analyzer.py`

专门处理复杂场面的效果诱发和处理顺序分析。

**分析方法论:**
1. 涉及的卡牌效果
2. 相关规则引用
3. 效果时机分析
4. 处理顺序推导（回合玩家优先）
5. 场面推导
6. 结论

**示例:**
```python
from app.scenario_analyzer import scenario_analyzer

report = scenario_analyzer.generate_scenario_analysis(
    question="我方联展了 bt23-032 土偶兽...",
    retrieved_context=search_results
)
print(report)
```

---

### 3. 分层检索

**文件:** `app/enhanced_vector_store.py`

根据问题类型智能选择检索策略：

| 问题类型 | 检索策略 | 文档类型 |
|----------|----------|----------|
| 卡牌查询 | 卡牌感知检索 | 卡牌（精确匹配） |
| 处理顺序 | 分层检索 | 规则→裁定→判例 |
| 时机判断 | 分层检索 | 规则→裁定 |
| 一般问题 | 分层检索 | 规则→裁定→卡牌 |

**权重配置:**
- 卡牌精确匹配：1.5×
- 官方裁定：1.2×
- 规则：1.0×
- 判例：0.8×

---

### 4. 结构化 Prompt

**文件:** `app/enhanced_llm_service.py`

**改进前:**
```
规则 1: xxx
规则 2: xxx
卡牌：xxx
问题：xxx
```

**改进后:**
```
【卡牌信息】
1. BT23-032 土偶兽：【攻击时】...

【相关规则】
1. 综合规则 3.2.1 (相关度：0.85): 当多个效果...

【官方裁定】
1. 裁定#2024-001: 关于连锁规则...

【玩家问题】
我方联展了 bt23-032 土偶兽...
```

---

## 🔧 使用场景

### 场景 1: 复杂场面分析

```bash
python main_enhanced.py --test "我方联展了 bt23-032 土偶兽，把对方的数码兽退化成 bt24-016 拉米亚兽，并选择其主要阶段开始时攻击。土偶进化源中有 bt23-027 天使兽和 bt23-050 甲龙兽。对方拉米亚进化源中有 bt21-001 基基兽。此时移交回合后会发生什么？"
```

**输出包含:**
- 涉及的卡牌效果分析
- 相关规则引用
- 效果时机分析
- 处理顺序推导
- 场面逐步推导
- 明确结论

---

### 场景 2: 效果处理顺序查询

```bash
python main_enhanced.py --test "我的数码兽攻击对手，对战中消灭了对手的数码兽。我的数码兽有≪贯通≫效果，同时有【消灭对手数码兽时】的效果。请问这两个效果如何处理？"
```

**自动识别:**
- 问题类型：sequence（处理顺序）
- 效果时机：攻击时、消灭时
- 需要连锁分析：是

---

### 场景 3: 卡牌效果查询

```bash
python main_enhanced.py --test "BT23-032 土偶兽的效果是什么？"
```

**检索策略:**
- 优先卡牌精确匹配
- 补充相关规则
- 自动格式化输出

---

## 📊 测试用例

内置 5 个标准测试用例：

1. **复杂场面分析** - 土偶兽联展（综合测试）
2. **效果处理顺序** - 同时触发（时机 + 顺序）
3. **安防效果时机** - 安防判定（时机判断）
4. **连锁规则** - 回合玩家优先（规则查询）
5. **卡牌效果查询** - 单卡查询（卡牌检索）

运行测试：
```bash
python test_enhanced_judge.py --all
```

---

## 🔍 质量检查

回答质量自动检查项：

- ✅ **结构化输出** - 使用标题和列表
- ✅ **包含引用** - 标注参考来源
- ✅ **包含分析步骤** - 明确分析过程
- ✅ **明确结论** - 给出裁定结论

---

## ⚙️ 配置选项

### 环境变量

```bash
# LLM 模型选择
export LLM_MODEL=finetuned  # 微调模型
export LLM_MODEL=qwen       # 通义千问
export LLM_MODEL=gemini     # Gemini
export LLM_MODEL=local      # 本地 Ollama

# 微调模型路径
export FINETUNED_LORA_PATH=finetune/output/dtcg_qwen_lora
export FINETUNED_BASE_MODEL=Qwen/Qwen2-1.5B-Instruct
```

### 检索配置

在 `app/enhanced_vector_store.py` 中调整权重：

```python
self.type_weights = {
    "rule": 1.0,    # 规则
    "ruling": 1.2,  # 官方裁定
    "case": 0.8,    # 判例
    "card": 1.5,    # 卡牌数据
}
```

---

## 📝 API 使用（待实现）

```python
from main_enhanced import EnhancedCardGameJudge

judge = EnhancedCardGameJudge()

# 普通查询
answer = judge.query("BT23-032 的效果是什么？")

# 场面分析
answer = judge.query("我方联展了 bt23-032...", use_scenario_analysis=True)
```

---

## 🐛 已知问题

1. **Web UI 未实现** - 仅支持命令行测试
2. **API 服务未实现** - 待添加 FastAPI 路由
3. **性能待优化** - 分层检索可能增加延迟
4. **依赖未测试** - 需在完整环境中验证

---

## 📚 相关文档

- `REFACTORING_PLAN.md` - 重构方案
- `REFACTORING_LOG.md` - 重构日志
- `README.md` - 原版使用说明

---

## 🤝 贡献指南

发现问题或有改进建议？

1. 记录问题现象和复现步骤
2. 检查是否已存在于已知问题
3. 提交到重构日志
4. 联系项目维护者

---

**最后更新:** 2026-03-06  
**维护者:** AI Agent + 用户
