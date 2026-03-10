# QA翻译工具 - 状态报告

## 已完成的工作

### 1. 修复了LLM关键词提取工具的样本收集逻辑 ✓

**文件**: `digimon_card_data/term_mapping/extract_with_llm.py`

**问题**: 
- 原来的 `collect_effect_samples` 方法使用了 `count` 变量来跟踪样本数
- 但在内层循环中同时检查 `count` 和 `sample_size`，导致逻辑混乱
- 当 `sample_size` 设置为很大的值（如10000）时，可能无法正确收集所有样本

**修复**:
- 直接使用 `len(samples)` 来判断是否达到目标数量
- 简化了逻辑，更清晰易懂
- 现在可以正确处理大样本量的情况

### 2. 创建了QA翻译工具 ✓

**文件**: `card_game_judge/card_game_QA_manger/translate_qa_with_terminology.py`

**功能**:
- 支持多种LLM: Qwen (通义千问)、Gemini、Ollama
- 自动加载游戏术语表 (`game_mechanics_keywords.json`)
- 自动加载卡牌数据进行名称映射
- 使用专业的翻译提示词
- 支持断点续传
- 支持批量处理和进度保存

**特点**:
- 参考了 `card_game_judge/app/llm_service.py` 的实现模式
- 使用统一的API接口设计
- 完善的错误处理和日志输出
- 灵活的配置选项

### 3. 创建了配套工具和文档 ✓

**测试工具**: `test_translation_setup.py`
- 检查所有必需文件是否存在
- 验证数据是否正确加载
- 测试模块导入

**使用文档**: `README_TRANSLATION.md`
- 详细的使用说明
- API密钥配置指南
- 常见问题解答
- 进阶配置说明

**批处理脚本**: `test_translation.bat`
- Windows下一键测试
- 自动运行配置检查和翻译测试

## 当前状态

### 已就绪 ✓
- [x] LLM关键词提取工具已修复
- [x] QA翻译工具已创建
- [x] 测试工具已创建
- [x] 文档已完善

### 待测试 ⚠️
- [ ] 运行 `test_translation_setup.py` 验证配置
- [ ] 运行翻译工具测试模式（10条QA）
- [ ] 检查翻译质量
- [ ] 根据需要调整提示词或参数

## 下一步操作

### 1. 测试配置（必需）

```bash
cd card_game_judge\card_game_QA_manger
python test_translation_setup.py
```

这会检查：
- 术语表是否存在并正确加载
- 卡牌数据是否存在并正确加载
- 日文QA数据是否存在
- API密钥是否配置

### 2. 测试翻译（推荐）

**方法A: 使用批处理脚本（Windows）**
```bash
test_translation.bat
```

**方法B: 手动运行**
```bash
python translate_qa_with_terminology.py
```
然后选择：
- LLM类型: 1 (Qwen)
- 翻译模式: 1 (测试10条)

### 3. 检查结果

翻译完成后，检查生成的文件：
- `official_qa_cn_qwen.json`

查看翻译质量：
- 术语是否正确
- 卡名是否正确
- 语句是否流畅
- 信息是否完整

### 4. 调整优化（如需要）

如果翻译质量不理想，可以：

**调整模型**:
```python
# 在 _init_qwen() 方法中
self.model_name = "qwen-max"  # 使用更强的模型
```

**调整提示词**:
- 修改 `_build_translation_prompt()` 方法
- 添加更多示例
- 调整翻译原则

**调整术语表**:
- 检查 `game_mechanics_keywords.json`
- 添加缺失的术语
- 修正错误的对应关系

### 5. 正式翻译（确认质量后）

```bash
python translate_qa_with_terminology.py
```
选择模式 3 (完整翻译)

## 技术细节

### LLM配置

**Qwen (通义千问)**:
- API Base: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 模型: `qwen-plus` (可选: qwen-turbo, qwen-max)
- 需要: `DASHSCOPE_API_KEY`

**Gemini**:
- 模型: `gemini-2.0-flash-exp`
- 需要: `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`
- 注意: 可能需要代理

**Ollama**:
- API Base: `http://localhost:11434/v1`
- 模型: `qwen2:7b` (可配置)
- 需要: 本地安装Ollama

### 数据流程

```
日文QA (official_qa_jp.json)
    ↓
加载术语表 (game_mechanics_keywords.json)
    ↓
加载卡牌数据 (digimon_cards_cn.json)
    ↓
构建翻译提示词（包含术语表和卡牌信息）
    ↓
调用LLM翻译
    ↓
保存结果 (official_qa_cn_{llm_type}.json)
```

### 翻译提示词结构

1. **角色定位**: 专业的数码宝贝卡牌游戏翻译专家
2. **翻译原则**: 信达雅、通俗易懂、专业准确
3. **专有名词表**: 前50个术语示例
4. **翻译要求**: 效果标记、卡牌名称、语气、数值、流畅度、完整性
5. **翻译示例**: 2个示例展示期望的翻译风格
6. **注意事项**: 不要逐字翻译、保持完整性等

## 已知问题

### 1. 术语表可能不完整
- 当前术语表来自 `game_mechanics_keywords.json`
- 可能缺少一些新卡牌的术语
- 建议: 运行 `extract_with_llm.py` 提取更多术语

### 2. 卡牌数据可能不是最新
- 需要定期更新卡牌数据
- 新卡牌的名称可能无法映射

### 3. API限流
- 大批量翻译时可能触发API限流
- 建议: 适当增加 `delay` 参数

## 相关文件清单

### 核心文件
- `translate_qa_with_terminology.py` - 主翻译工具
- `test_translation_setup.py` - 配置测试工具
- `README_TRANSLATION.md` - 使用文档
- `test_translation.bat` - Windows测试脚本
- `TRANSLATION_STATUS.md` - 本文件

### 数据文件
- `official_qa_jp.json` - 输入：日文QA
- `official_qa_cn_{llm_type}.json` - 输出：中文QA
- `official_qa_cn_{llm_type}_checkpoint.json` - 检查点文件

### 依赖文件
- `../../digimon_card_data/term_mapping/game_mechanics_keywords.json` - 术语表
- `../../digimon_card_data/digimon_card_data_chiness/digimon_cards_cn.json` - 卡牌数据
- `../.env` - 环境变量配置

### 参考文件
- `../app/llm_service.py` - LLM服务实现参考
- `translate_qa_with_llm.py` - 旧版翻译工具（不使用术语表）

## 更新日志

### 2026-03-06
- ✓ 修复了 `extract_with_llm.py` 的样本收集逻辑
- ✓ 创建了 `translate_qa_with_terminology.py`
- ✓ 创建了测试工具和文档
- ✓ 统一了API接口设计
- ⚠️ 等待用户测试和反馈
