from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import List
import time
import os
import httpx

from app.config import LLM_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY

# 通义千问 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 如果需要代理访问 Google API
if os.getenv("USE_PROXY", "").lower() == "true":
    os.environ["HTTP_PROXY"] = f"http://{os.getenv('PROXY_HOST', '127.0.0.1')}:{os.getenv('PROXY_PORT', '7897')}"
    os.environ["HTTPS_PROXY"] = f"http://{os.getenv('PROXY_HOST', '127.0.0.1')}:{os.getenv('PROXY_PORT', '7897')}"


SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（DTCG）裁判助手。

【重要提醒】
- 卡牌效果已在界面上单独显示，你不需要列出卡牌效果
- 你的分析仅供参考，复杂情况请以官方裁定为准
- 如果规则参考中没有直接相关的规则，请明确说明"规则参考中未找到直接相关条款"

【你的任务】
根据下方【规则参考】分析玩家的问题，重点关注：
1. 效果的触发时机（什么时候触发）
2. 效果的处理顺序（先处理什么，后处理什么）
3. 给出裁定建议

【规则参考】
{context}

如果规则参考不足以回答问题，请诚实说明。
"""

USER_PROMPT = """【问题】
{question}

请根据规则参考分析。如果规则参考不足，请说明。"""


class LLMService:
    def __init__(self):
        self.llm = self._init_llm()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT)
        ])
        self.timeout = 60  # 超时时间（秒）
    
    def _init_llm(self):
        if LLM_MODEL == "local":
            return Ollama(model="qwen2:7b", temperature=0)
        elif LLM_MODEL == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                temperature=0,
                google_api_key=GOOGLE_API_KEY,
                timeout=60,
                max_retries=2
            )
        elif LLM_MODEL == "qwen":
            # 通义千问 - 使用 OpenAI 兼容接口
            return ChatOpenAI(
                model="qwen-flash",  # 可选: qwen-turbo, qwen-plus, qwen-max
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
                openai_api_key=OPENAI_API_KEY,
                timeout=60,
                max_retries=2
            )
    
    def _call_llm(self, context: str, question: str) -> str:
        """实际调用 LLM 的方法"""
        chain = self.prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    def generate_answer(self, question: str, context_docs: List[dict], log_callback=None) -> str:
        """根据检索到的文档生成回答，带日志"""
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[LLM] {msg}")
        
        start_time = time.time()
        
        # 步骤1: 构建上下文
        log("📝 步骤1/3: 构建上下文...")
        context_parts = []
        for i, doc in enumerate(context_docs, 1):
            title = doc['metadata'].get('title', '未知来源')
            doc_type = doc.get('doc_type', '')
            type_label = {"rule": "规则", "ruling": "官方裁定", "case": "判例"}.get(doc_type, "文档")
            
            # 提取卡牌编号（如果有）
            content = doc['content']
            card_no = ""
            if "card_no:" in content.lower():
                import re
                match = re.search(r'card_no:\s*([A-Z0-9-_]+)', content, re.IGNORECASE)
                if match:
                    card_no = f" [{match.group(1)}]"
            
            context_parts.append(
                f"【参考{i}】{card_no}\n"
                f"来源：{title}（{type_label}）\n"
                f"内容：{content}\n"
            )
        
        context = "\n\n".join(context_parts)
        log(f"✅ 上下文构建完成，共 {len(context_docs)} 个参考文档，{len(context)} 字符")
        
        # 调试：打印实际传给 LLM 的上下文
        print("=" * 60)
        print("【调试】传给 LLM 的参考资料内容：")
        print("=" * 60)
        print(context[:2000])  # 只打印前2000字符
        if len(context) > 2000:
            print(f"... (共 {len(context)} 字符)")
        print("=" * 60)
        
        # 步骤2: 调用 LLM
        log(f"🤖 步骤2/3: 调用 LLM ({LLM_MODEL})...")
        
        try:
            result = self._call_llm(context, question)
            elapsed = time.time() - start_time
            log(f"✅ LLM 响应完成，耗时 {elapsed:.1f}s")
            
            # 步骤3: 返回结果
            log(f"📤 步骤3/3: 返回结果，共 {len(result)} 字符")
            return result
                    
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            log(f"❌ LLM 调用失败，耗时 {elapsed:.1f}s")
            log(f"❌ 错误详情: {error_msg}")
            
            # 检查常见错误
            if "API key" in error_msg.lower() or "invalid" in error_msg.lower():
                log("💡 提示: 请检查 GOOGLE_API_KEY 是否正确设置")
            elif "quota" in error_msg.lower():
                log("💡 提示: API 配额已用完，请稍后重试")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                log("💡 提示: 网络连接问题，可能需要代理")
            
            raise


llm_service = LLMService()
