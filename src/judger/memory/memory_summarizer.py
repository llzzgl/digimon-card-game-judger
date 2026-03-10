# -*- coding: utf-8 -*-
"""
记忆总结器 - 使用LLM总结问答对
"""
from typing import Optional, List
from langchain.prompts import ChatPromptTemplate

from .memory_config import MemoryConfig, default_memory_config
from .llm_service import llm_service


class MemorySummarizer:
    """记忆总结器"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or default_memory_config
        
        # 总结提示词模板
        self.summarize_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的知识总结助手。
你的任务是将问答对总结为简洁、结构化的知识点，便于后续检索和使用。

总结要求：
1. 提炼核心规则或裁定
2. 标注关键卡牌编号和效果
3. 说明适用场景和条件
4. 使用简洁、专业的语言
5. 保持客观和准确

总结格式：
【核心内容】一句话概括
【关键信息】列出要点
【适用场景】说明使用条件"""),
            ("human", """请总结以下问答对：

问题：{question}

答案：{answer}

请按照要求格式进行总结：""")
        ])
        
        # 修正总结提示词模板（学习规律）
        self.correction_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的知识学习助手。
你的任务是从错误答案和正确答案的对比中，提取通用的知识规律和判断原则。

重要：不要只是复述正确答案，而是要：
1. 分析错误的原因（理解偏差、规则遗漏、时序错误等）
2. 提炼正确的判断原则和规律
3. 总结可以应用到类似场景的通用知识
4. 标注关键的规则引用和卡牌机制

总结格式：
【错误原因】分析为什么会出错
【正确原则】提炼通用的判断规律
【关键规则】列出相关的核心规则
【适用场景】说明这个规律适用的场景类型"""),
            ("human", """请分析以下修正案例，提取知识规律：

【原始问题】
{question}

【错误答案】
{wrong_answer}

【正确答案】
{correct_answer}

{user_explanation_section}

请按照要求格式进行分析和总结：""")
        ])
    
    def summarize_correction(
        self,
        question: str,
        wrong_answer: str,
        correct_answer: str,
        user_explanation: Optional[str] = None
    ) -> str:
        """
        总结修正案例，提取知识规律
        
        Args:
            question: 原始问题
            wrong_answer: 错误答案
            correct_answer: 正确答案
            user_explanation: 用户的额外说明
        
        Returns:
            总结文本（包含知识规律）
        """
        try:
            # 如果禁用自动总结，返回简单摘要
            if not self.config.enable_auto_summarize:
                return self._simple_correction_summary(
                    question, wrong_answer, correct_answer, user_explanation
                )
            
            # 使用LLM分析和总结
            print("🧠 正在分析修正案例，提取知识规律...")
            
            # 构建用户说明部分
            user_explanation_section = ""
            if user_explanation:
                user_explanation_section = f"""【用户说明】
{user_explanation}"""
            
            chain = self.correction_prompt | llm_service.llm
            response = chain.invoke({
                "question": question,
                "wrong_answer": wrong_answer,
                "correct_answer": correct_answer,
                "user_explanation_section": user_explanation_section
            })
            
            if hasattr(response, 'content'):
                summary = response.content
            else:
                summary = str(response)
            
            print("✅ 知识规律提取完成")
            return summary
            
        except Exception as e:
            print(f"⚠️  LLM分析失败，使用简单摘要: {e}")
            return self._simple_correction_summary(
                question, wrong_answer, correct_answer, user_explanation
            )
    
    def _simple_correction_summary(
        self,
        question: str,
        wrong_answer: str,
        correct_answer: str,
        user_explanation: Optional[str] = None
    ) -> str:
        """简单修正摘要（不使用LLM）"""
        summary_parts = [
            f"【修正案例】",
            f"问题：{question[:100]}...",
            f"正确答案：{correct_answer[:200]}..."
        ]
        
        if user_explanation:
            summary_parts.append(f"用户说明：{user_explanation[:100]}...")
        
        return "\n".join(summary_parts)
    
    def summarize(
        self,
        question: str,
        answer: str,
        card_numbers: Optional[List[str]] = None
    ) -> str:
        """
        总结问答对
        
        Args:
            question: 问题
            answer: 答案
            card_numbers: 相关卡牌编号
        
        Returns:
            总结文本
        """
        try:
            # 如果禁用自动总结，返回简单摘要
            if not self.config.enable_auto_summarize:
                return self._simple_summary(question, answer, card_numbers)
            
            # 使用LLM总结
            print("🤔 正在生成记忆总结...")
            
            chain = self.summarize_prompt | llm_service.llm
            response = chain.invoke({
                "question": question,
                "answer": answer
            })
            
            if hasattr(response, 'content'):
                summary = response.content
            else:
                summary = str(response)
            
            print("✅ 记忆总结完成")
            return summary
            
        except Exception as e:
            print(f"⚠️  LLM总结失败，使用简单摘要: {e}")
            return self._simple_summary(question, answer, card_numbers)
    
    def _simple_summary(
        self,
        question: str,
        answer: str,
        card_numbers: Optional[List[str]] = None
    ) -> str:
        """简单摘要（不使用LLM）"""
        # 提取答案的前200字符
        answer_excerpt = answer[:200] + "..." if len(answer) > 200 else answer
        
        # 构建摘要
        summary_parts = [f"问题：{question}"]
        
        if card_numbers:
            summary_parts.append(f"涉及卡牌：{', '.join(card_numbers)}")
        
        summary_parts.append(f"答案摘要：{answer_excerpt}")
        
        return "\n".join(summary_parts)
    
    def batch_summarize(
        self,
        qa_pairs: List[dict]
    ) -> List[str]:
        """
        批量总结
        
        Args:
            qa_pairs: 问答对列表 [{"question": "...", "answer": "...", "card_numbers": [...]}, ...]
        
        Returns:
            总结列表
        """
        summaries = []
        for i, qa in enumerate(qa_pairs, 1):
            print(f"总结进度: {i}/{len(qa_pairs)}")
            summary = self.summarize(
                qa["question"],
                qa["answer"],
                qa.get("card_numbers")
            )
            summaries.append(summary)
        
        return summaries


# 全局实例
memory_summarizer = MemorySummarizer()
