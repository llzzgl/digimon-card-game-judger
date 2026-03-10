# -*- coding: utf-8 -*-
"""
LLM Service Module - 合并基础服务和增强版服务
支持多种 LLM 提供商和场面分析
"""
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Optional
import time
import os
import httpx
from pathlib import Path

# 通义千问 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 代理配置
if os.getenv("USE_PROXY", "").lower() == "true":
    os.environ["HTTP_PROXY"] = f"http://{os.getenv('PROXY_HOST', '127.0.0.1')}:{os.getenv('PROXY_PORT', '7897')}"
    os.environ["HTTPS_PROXY"] = f"http://{os.getenv('PROXY_HOST', '127.0.0.1')}:{os.getenv('PROXY_PORT', '7897')}"


# ========== 基础 System Prompt ==========
BASE_SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（Digimon Card Game）的专业裁判助手。

【重要】你只回答数码宝贝卡牌游戏相关的问题，不是网络安全、不是其他游戏！

【关键提醒】
参考资料中如果包含规则编号（如"11-1-3"），这些就是数码宝贝卡牌游戏的官方规则，必须使用！

【重要原则】
1. 仔细阅读【参考资料】中的每一条内容
2. 如果看到规则编号（如"11-1-3"、"8.1"等），这就是数码宝贝卡牌游戏的官方规则
3. 必须基于这些规则给出准确的裁定
4. 引用具体的规则条款编号

【你的任务】
1. 逐条检查【参考资料】
2. 找出包含规则编号的内容
3. 基于这些数码宝贝卡牌游戏规则回答问题
4. 引用规则编号

【参考资料】
{context}

【回答格式】
根据数码宝贝卡牌游戏规则 [编号]，[回答内容]...

【特别注意】
- 这是数码宝贝卡牌游戏（Digimon Card Game），不是网络安全或其他领域
- 规则编号通常是数字加点号，如"11-1-3"、"8.1"
- 只要参考资料中有规则编号，就一定要使用
- 不要说"未找到"，除非真的完全没有相关内容
"""

BASE_USER_PROMPT = """【数码宝贝卡牌游戏问题】
{question}

请根据上方【参考资料】中的数码宝贝卡牌游戏规则回答。"""


# ========== 增强版 System Prompt ==========
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


class LLMService:
    """基础 LLM 服务"""
    
    def __init__(self, model_config: Optional[Dict] = None):
        self.model_config = model_config or {}
        self.llm = self._init_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", BASE_SYSTEM_PROMPT),
            ("human", BASE_USER_PROMPT)
        ])
        self.timeout = 60  # 超时时间（秒）
    
    def _init_llm(self):
        """初始化 LLM"""
        llm_model = self.model_config.get('model', os.getenv('LLM_MODEL', 'qwen'))
        
        if llm_model == "local":
            return Ollama(model="qwen2:7b", temperature=0)
        elif llm_model == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                temperature=0,
                google_api_key=os.getenv('GOOGLE_API_KEY'),
                timeout=60,
                max_retries=2
            )
        elif llm_model == "qwen":
            # 通义千问 - 使用 OpenAI 兼容接口
            return ChatOpenAI(
                model="qwen3.5-plus",
                temperature=0,
                openai_api_key=DASHSCOPE_API_KEY,
                openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                timeout=60,
                max_retries=2
            )
        else:
            # OpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                timeout=60,
                max_retries=2
            )
    
    def _call_llm(self, context: str, question: str, system_prompt: str = None) -> str:
        """实际调用 LLM 的方法"""
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\n{BASE_SYSTEM_PROMPT}"
            prompt = ChatPromptTemplate.from_messages([
                ("system", combined_prompt),
                ("human", BASE_USER_PROMPT)
            ])
        else:
            prompt = self.prompt
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    def generate_answer(self, question: str, context_docs: List[dict], 
                       system_prompt: str = None, log_callback=None) -> str:
        """根据检索到的文档生成回答，带日志"""
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[LLM] {msg}")
        
        start_time = time.time()
        
        # 构建上下文
        log("📝 步骤 1/3: 构建上下文...")
        context_parts = []
        card_count = 0
        rule_count = 0
        
        for i, doc in enumerate(context_docs, 1):
            title = doc['metadata'].get('title', '未知来源')
            doc_type = doc.get('doc_type', '')
            
            if doc_type == 'card':
                card_count += 1
                content = doc['content']
                card_no = ""
                if "card_no:" in content.lower():
                    import re
                    match = re.search(r'card_no:\s*([A-Z0-9-_]+)', content, re.IGNORECASE)
                    if match:
                        card_no = f" [{match.group(1)}]"
                
                context_parts.append(
                    f"【卡牌{card_count}】{card_no}\n"
                    f"名称：{title}\n"
                    f"效果：{content}\n"
                )
            else:
                rule_count += 1
                type_label = {"rule": "规则", "ruling": "官方裁定", "case": "判例"}.get(doc_type, "文档")
                context_parts.append(
                    f"【参考{rule_count}】\n"
                    f"来源：{title}（{type_label}）\n"
                    f"内容：{doc['content']}\n"
                )
        
        context = "\n\n".join(context_parts)
        log(f"✅ 上下文构建完成：{card_count} 张卡牌 + {rule_count} 条规则，共 {len(context)} 字符")
        
        # 调用 LLM
        log(f"🤖 步骤 2/3: 调用 LLM ({self.model_config.get('model', 'default')})...")
        if system_prompt:
            log(f"   使用自定义系统提示词（{len(system_prompt)} 字符）")
        
        try:
            result = self._call_llm(context, question, system_prompt)
            elapsed = time.time() - start_time
            log(f"✅ LLM 响应完成，耗时 {elapsed:.1f}s")
            
            log(f"📤 步骤 3/3: 返回结果，共 {len(result)} 字符")
            return result
                    
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            log(f"❌ LLM 调用失败，耗时 {elapsed:.1f}s")
            log(f"❌ 错误详情：{error_msg}")
            
            if "API key" in error_msg.lower() or "invalid" in error_msg.lower():
                log("💡 提示：请检查 API Key 是否正确设置")
            elif "quota" in error_msg.lower():
                log("💡 提示：API 配额已用完，请稍后重试")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                log("💡 提示：网络连接问题，可能需要代理")
            
            raise


class EnhancedLLMService:
    """增强版 LLM 服务 - 支持场面分析和效果处理顺序推导"""
    
    def __init__(self, base_llm_service: LLMService):
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
        """生成增强版回答 - 使用改进的 prompt 拼接"""
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[EnhancedLLM] {msg}")
        
        start_time = time.time()
        
        # 构建结构化上下文
        log("📝 步骤 1/3: 构建结构化上下文...")
        context = self._build_structured_context(search_results, query_analysis or {})
        log(f"✅ 上下文构建完成，{len(context)} 字符")
        
        # 构建完整 Prompt
        log("📝 步骤 2/3: 构建 Prompt...")
        prompt = self.user_prompt_template.format(
            question=question,
            context=context
        )
        
        # 调用 LLM
        log("📝 步骤 3/3: 调用 LLM 生成回答...")
        
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
    
    def _build_structured_context(self, search_results: List[Dict], 
                                  query_analysis: Dict) -> str:
        """构建结构化上下文"""
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


def create_llm_service(model_config: Optional[Dict] = None) -> LLMService:
    """创建 LLM 服务实例"""
    return LLMService(model_config)


def create_enhanced_llm_service(base_llm_service: LLMService) -> EnhancedLLMService:
    """创建增强版 LLM 服务实例"""
    return EnhancedLLMService(base_llm_service)


# 默认实例
llm_service = LLMService()
