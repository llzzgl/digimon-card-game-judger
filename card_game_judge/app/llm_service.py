from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import List
import time
import os
import httpx

from app.config import LLM_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY

# 如果需要代理访问 Google API，取消下面的注释并修改代理地址
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

# 配置更短的超时时间
DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（DTCG）裁判。

【关于卡牌效果 - 严格要求】
1. 引用卡牌效果时，必须从【参考资料】中原文复制，一字不改
2. 绝对禁止编造、翻译、猜测或修改卡牌效果文本
3. 如果参考资料中没有某张卡牌的数据，明确说"参考资料中未提供该卡牌数据"
4. 卡牌效果必须用中文（参考资料是中文的）

【关于规则裁定 - 你可以分析】
1. 根据参考资料中的规则文档分析效果处理顺序
2. 判断效果的发动时机和条件
3. 解释规则的适用情况
4. 给出裁定结论

【回答格式】
1. 先列出涉及的卡牌效果（直接复制参考资料原文）
2. 分析效果发动时机和处理顺序
3. 给出裁定结论

【参考资料】
{context}
"""

USER_PROMPT = """【问题】
{question}

请根据参考资料回答。引用卡牌效果时必须原文复制，不要改写或翻译。"""


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
                temperature=0,  # 降到0，减少编造
                google_api_key=GOOGLE_API_KEY,
                timeout=60,
                max_retries=2
            )
        else:
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
