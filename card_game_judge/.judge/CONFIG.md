# CONFIG.md - 系统配置

_这个文件包含记忆系统和裁判AI的技术配置_

## 记忆系统配置

### 存储配置

```yaml
# 记忆存储路径
MEMORY_STORAGE_PATH: ./data/memory

# 向量数据库配置
VECTOR_DB_TYPE: chromadb
VECTOR_DB_PATH: ./data/memory/vectordb
EMBEDDING_MODEL: text-embedding-004  # Google的嵌入模型

# 记忆文件组织
MEMORY_STRUCTURE:
  rulings: ./data/memory/rulings/      # 裁定记忆
  rules: ./data/memory/rules/          # 规则记忆
  cards: ./data/memory/cards/          # 卡牌记忆
  qa: ./data/memory/qa/                # QA记忆
```

### 检索配置

```yaml
# 记忆搜索配置
MEMORY_SEARCH_ENABLED: true
MEMORY_SEARCH_TOP_K: 3                 # 返回前3个最相关的记忆
MEMORY_SIMILARITY_THRESHOLD: 0.70      # 相似度阈值

# 相似度权重
SIMILARITY_WEIGHTS:
  semantic: 0.6      # 语义相似度权重
  keyword: 0.2       # 关键词匹配权重
  importance: 0.1    # 重要性权重
  freshness: 0.1     # 时间新鲜度权重

# 检索策略
SEARCH_STRATEGY:
  exact_match_boost: 1.5     # 精确匹配加成
  verified_boost: 1.2        # 已验证记忆加成
  high_usage_boost: 1.1      # 高使用频率加成
```

### 保存配置

```yaml
# 自动保存配置
MEMORY_AUTO_SAVE: true
MEMORY_AUTO_SUMMARIZE: true            # 自动生成摘要

# 保存条件
SAVE_CONDITIONS:
  min_answer_length: 50                # 最小回答长度
  require_verification: true           # 需要用户验证
  require_sources: true                # 需要引用来源

# 重要性评分
IMPORTANCE_SCORING:
  user_marked: 5                       # 用户标记为重要
  complex_ruling: 4                    # 复杂裁定
  common_question: 3                   # 常见问题
  simple_ruling: 2                     # 简单裁定
  default: 1                           # 默认重要性
```

### 维护配置

```yaml
# 记忆维护
MEMORY_MAINTENANCE:
  auto_cleanup: true
  cleanup_interval: 7d                 # 每7天清理一次
  min_usage_threshold: 0               # 最小使用次数
  max_age_days: 365                    # 最大保存时间

# 质量控制
QUALITY_CONTROL:
  min_similarity_for_reuse: 0.85       # 复用记忆的最小相似度
  max_memories_per_question: 3         # 每个问题最多参考的记忆数
  enable_quality_check: true           # 启用质量检查
```

## LLM配置

### 模型配置

```yaml
# LLM模型选择
LLM_MODEL: gemini                      # gemini | openai | local
LLM_MODEL_NAME: gemini-2.0-flash-exp   # 具体模型名称

# API配置
GOOGLE_API_KEY: ${GOOGLE_API_KEY}      # 从环境变量读取
PROXY_PORT: 7890                       # 代理端口

# 生成参数
GENERATION_CONFIG:
  temperature: 0.3                     # 较低温度，更确定的回答
  top_p: 0.9
  top_k: 40
  max_output_tokens: 2048
```

### 提示词配置

```yaml
# 系统提示词
SYSTEM_PROMPT_PATH: .judge/IDENTITY.md

# 提示词模板
PROMPT_TEMPLATES:
  with_memory: |
    你是数码宝贝卡牌对战的顶级裁判。
    
    以下是相关的已验证记忆：
    {memories}
    
    用户问题：{question}
    
    请基于记忆和规则给出准确的裁定。
    
  without_memory: |
    你是数码宝贝卡牌对战的顶级裁判。
    
    用户问题：{question}
    
    请查询规则和卡牌信息，给出准确的裁定。
```

## RAG配置

### 检索配置

```yaml
# RAG检索配置
RAG_ENABLED: true
RAG_TOP_K: 5                           # 检索前5个最相关的文档

# 数据源
RAG_SOURCES:
  - type: rules
    path: ./数码宝贝卡牌对战_综合规则_嵌入版.txt
    weight: 1.0
  - type: qa
    path: ./card_game_QA_manger/official_qa_cn.json
    weight: 0.9
  - type: cards
    path: ./data/cards/
    weight: 0.8

# 向量数据库
RAG_VECTOR_DB:
  type: chromadb
  path: ./data/vectordb
  collection_name: digimon_rules
```

### 检索策略

```yaml
# 混合检索
HYBRID_SEARCH:
  enabled: true
  dense_weight: 0.7                    # 密集向量权重
  sparse_weight: 0.3                   # 稀疏向量权重

# 重排序
RERANKING:
  enabled: true
  model: cross-encoder                 # 重排序模型
  top_k: 3                             # 重排序后保留的数量
```

## Web界面配置

### 服务器配置

```yaml
# FastAPI服务器
SERVER_HOST: 0.0.0.0
SERVER_PORT: 8000
SERVER_RELOAD: false                   # 生产环境关闭自动重载

# CORS配置
CORS_ORIGINS:
  - http://localhost:8000
  - http://127.0.0.1:8000
```

### 界面配置

```yaml
# 界面功能
UI_FEATURES:
  enable_memory_feedback: true         # 启用记忆反馈按钮
  enable_memory_search: true           # 启用记忆搜索
  enable_memory_stats: true            # 启用记忆统计
  show_sources: true                   # 显示信息来源
  show_relevance_scores: true          # 显示相关度分数

# 显示配置
DISPLAY_CONFIG:
  max_answer_length: 5000              # 最大显示长度
  show_thinking_process: false         # 不显示思考过程
  highlight_sources: true              # 高亮显示来源
```

## 日志配置

### 日志级别

```yaml
# 日志配置
LOG_LEVEL: INFO                        # DEBUG | INFO | WARNING | ERROR

# 日志输出
LOG_OUTPUT:
  console: true
  file: true
  file_path: ./logs/judge.log

# 日志内容
LOG_CONTENT:
  log_queries: true                    # 记录查询
  log_memories: true                   # 记录记忆操作
  log_rag_retrieval: true              # 记录RAG检索
  log_llm_calls: true                  # 记录LLM调用
```

### 性能监控

```yaml
# 性能监控
PERFORMANCE_MONITORING:
  enabled: true
  log_response_time: true              # 记录响应时间
  log_memory_usage: true               # 记录内存使用
  log_cache_hits: true                 # 记录缓存命中

# 统计报告
STATISTICS:
  enable_stats: true
  stats_interval: 1h                   # 每小时生成统计
  stats_path: ./logs/stats/
```

## 高级配置

### 缓存配置

```yaml
# 缓存配置
CACHE_ENABLED: true
CACHE_TYPE: memory                     # memory | redis
CACHE_TTL: 3600                        # 缓存过期时间（秒）

# 缓存策略
CACHE_STRATEGY:
  cache_memories: true                 # 缓存记忆搜索结果
  cache_rag_results: true              # 缓存RAG检索结果
  cache_llm_responses: false           # 不缓存LLM响应
```

### 并发配置

```yaml
# 并发控制
CONCURRENCY:
  max_concurrent_queries: 10           # 最大并发查询数
  max_concurrent_llm_calls: 3          # 最大并发LLM调用数
  queue_size: 100                      # 队列大小
```

### 安全配置

```yaml
# 安全配置
SECURITY:
  enable_rate_limiting: true           # 启用速率限制
  rate_limit: 60/minute                # 每分钟60次请求
  enable_input_validation: true        # 启用输入验证
  max_input_length: 1000               # 最大输入长度
```

## 配置文件位置

### 环境变量文件
```
card_game_judge/.env                   # 主配置文件
```

### 配置文件
```
card_game_judge/.judge/CONFIG.md       # 本文件
card_game_judge/app/memory_config.py   # Python配置模块
```

## 配置优先级

```
1. 环境变量（最高优先级）
2. .env 文件
3. CONFIG.md 默认值
4. 代码中的硬编码默认值（最低优先级）
```

## 配置更新

### 如何更新配置

1. **修改 .env 文件** - 修改环境变量
2. **重启服务** - 使配置生效
3. **验证配置** - 检查日志确认配置已加载

### 配置验证

```bash
# 检查配置
python -c "from app.memory_config import MemoryConfig; print(MemoryConfig())"

# 测试记忆系统
python test_memory_system.py
```

---

_这个配置文件定义了系统的技术参数。根据实际需求调整这些配置。_
