# -*- coding: utf-8 -*-
"""
增强版 LLM 服务 - 改进 prompt 拼接和上下文组织
支持场面分析和效果处理顺序推导
"""
from typing import List, Dict, Optional
import time
from pathlib import Path


# ========== 改进的 System Prompt ==========
ENHANCED_SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（DTCG）的专业智能裁判。

【核心能力】
1. 解释游戏规则和关键词效果
2. 查询卡牌信息和效果
3. 分析复杂的游戏场面
4. 判断效果的触发时机和处理顺序
5. 提供准确的裁定建议

【分析方法论】
面对复杂场面时，必须按以下步骤分析：

## 1. 涉及的卡牌效果
- 列出所有相关卡牌及其关键效果
- 标注卡牌编号和名称
- 说明效果类型（诱发/启动/被动）

## 2. 相关规则引用
- 引用适用的规则条款
- 标注规则来源（综合规则/官方裁定）
- 如果规则不足，明确说明

## 3. 效果时机分析
- 识别各效果的触发时机
- 判断是否有同时触发的效果
- 分析效果类型（诱发/启动/被动）

## 4. 处理顺序推导
- 应用"回合玩家优先"原则
- 说明连锁结构（如有）
- 逐步推导处理顺序

## 5. 场面推导
- 逐步推导场面变化
- 说明每一步的结果
- 注意状态检查和再触发

## 6. 结论
- 给出明确的裁定结论
- 标注引用来源
- 如有歧义，说明需要官方裁定

【重要原则】
• 基于官方综合规则进行分析
• 逻辑清晰，步骤明确，引用具体
• 如果卡牌效果不明确，说明需要查看完整效果文本
• 如果规则有歧义，说明需要官方裁定
• 复杂情况建议参考官方裁定
• 答案必须标注引用来源

【上下文组织】
下方提供的检索结果已按类型组织：
- 【卡牌信息】相关卡牌的效果文本
- 【相关规则】适用的规则条款
- 【官方裁定】相关官方裁定
- 【参考判例】类似情况的判例

请基于这些信息进行专业分析。"""


ENHANCED_USER_PROMPT = """【玩家问题】
{question}

【检索到的上下文】
{context}

【分析要求】
请按照上述分析方法论，详细分析并回答玩家的问题。
如果上下文信息不足，请明确说明需要补充哪些信息。
回答必须结构化，使用标题和列表使逻辑清晰。"""


class EnhancedLLMService:
    """增强版 LLM 服务"""
    
    def __init__(self, base_llm_service):
        """
        Args:
            base_llm_service: 基础 LLMService 实例
        """
        self.base = base_llm_service
        self.system_prompt = ENHANCED_SYSTEM_PROMPT
        self.user_prompt_template = ENHANCED_USER_PROMPT
    
    def generate_enhanced_answer(
        self,
        question: str,
        search_results: List[Dict],
        query_analysis: Optional[Dict] = None,
        log_callback=None
    ) -> str:
        """
        生成增强版回答 - 使用改进的 prompt 拼接
        
        Args:
            question: 用户问题
            search_results: 检索结果
            query_analysis: 查询分析结果（可选）
            log_callback: 日志回调函数
        
        Returns:
            模型回答
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[EnhancedLLM] {msg}")
        
        start_time = time.time()
        
        # 步骤 1: 构建结构化上下文
        log("📝 步骤 1/3: 构建结构化上下文...")
        
        if hasattr(self.base, 'vector_store') and self.base.vector_store:
            # 使用增强版向量存储构建上下文
            from app.enhanced_vector_store import EnhancedVectorStore
            if isinstance(self.base.vector_store, EnhancedVectorStore):
                context = self.base.vector_store.build_structured_context(
                    search_results,
                    query_analysis or {}
                )
            else:
                context = self._build_simple_context(search_results)
        else:
            context = self._build_simple_context(search_results)
        
        log(f"✅ 上下文构建完成，{len(context)} 字符")
        
        # 步骤 2: 构建完整 Prompt
        log("📝 步骤 2/3: 构建 Prompt...")
        
        prompt = self.user_prompt_template.format(
            question=question,
            context=context
        )
        
        # 步骤 3: 调用 LLM
        log("📝 步骤 3/3: 调用 LLM 生成回答...")
        
        if self.base.is_finetuned:
            # 微调模型
            answer = self.base.llm._call_llm(
                context=self.system_prompt + "\n\n" + context,
                question=question
            )
        else:
            # 其他模型
            from langchain.prompts import ChatPromptTemplate
            prompt_obj = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", self.user_prompt_template)
            ])
            chain = prompt_obj | self.base.llm
            response = chain.invoke({"context": context, "question": question})
            answer = response.content if hasattr(response, 'content') else str(response)
        
        elapsed = time.time() - start_time
        log(f"✅ 回答生成完成，耗时 {elapsed:.2f}s")
        
        return answer
    
    def _build_simple_context(self, search_results: List[Dict]) -> str:
        """简单的上下文构建（回退方案）"""
        if not search_results:
            return "未找到相关文档。"
        
        parts = []
        
        # 按类型分组
        grouped = {"card": [], "rule": [], "ruling": [], "case": []}
        for result in search_results:
            doc_type = result.get("doc_type", "rule")
            if doc_type in grouped:
                grouped[doc_type].append(result)
        
        # 卡牌信息
        if grouped["card"]:
            parts.append("【卡牌信息】")
            for i, card in enumerate(grouped["card"][:5], 1):
                title = card['metadata'].get('title', '未知')
                content = card['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title}: {content}...")
        
        # 相关规则
        if grouped["rule"]:
            parts.append("\n【相关规则】")
            for i, rule in enumerate(grouped["rule"][:5], 1):
                title = rule['metadata'].get('title', '未知')
                content = rule['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title}: {content}...")
        
        # 官方裁定
        if grouped["ruling"]:
            parts.append("\n【官方裁定】")
            for i, ruling in enumerate(grouped["ruling"][:3], 1):
                title = ruling['metadata'].get('title', '未知')
                content = ruling['content'][:300].replace('\n', ' ')
                parts.append(f"{i}. {title}: {content}...")
        
        return "\n".join(parts)
    
    def generate_scenario_analysis(
        self,
        question: str,
        search_results: List[Dict],
        query_analysis: Dict,
        log_callback=None
    ) -> str:
        """
        生成专门的场面分析报告
        
        Args:
            question: 用户问题
            search_results: 检索结果
            query_analysis: 查询分析结果
            log_callback: 日志回调函数
        
        Returns:
            场面分析报告
        """
        from app.scenario_analyzer import scenario_analyzer
        
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[ScenarioAnalysis] {msg}")
        
        log("🔍 开始场面分析...")
        
        # 使用场面分析器生成报告
        report = scenario_analyzer.generate_scenario_analysis(
            question=question,
            retrieved_context=search_results
        )
        
        log("✅ 场面分析完成")
        
        return report


def create_enhanced_llm_service(base_llm_service) -> EnhancedLLMService:
    """创建增强版 LLM 服务实例"""
    return EnhancedLLMService(base_llm_service)
