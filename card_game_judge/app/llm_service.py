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


SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（Digimon Card Game）的专业裁判助手。

【重要】你只回答数码宝贝卡牌游戏相关的问题，不是网络安全、不是其他游戏！

【关键提醒】
参考资料中如果包含规则编号（如"11-1-3"），这些就是数码宝贝卡牌游戏的官方规则，必须使用！

【重要原则】
1. 仔细阅读【参考资料】中的每一条内容
2. 如果看到规则编号（如"11-1-3"、"8.1"等），这就是数码宝贝卡牌游戏的官方规则
3. 必须基于这些规则给出明确的裁定
4. 引用具体的规则条款编号

【你的任务】
1. 逐条检查【参考资料】
2. 找出包含规则编号的内容
3. 基于这些数码宝贝卡牌游戏规则回答问题
4. 引用规则编号

【参考资料】
{context}

【回答格式】
根据数码宝贝卡牌游戏规则[编号]，[回答内容]...

【特别注意】
- 这是数码宝贝卡牌游戏（Digimon Card Game），不是网络安全或其他领域
- 规则编号通常是数字加点号，如"11-1-3"、"8.1"
- 只要参考资料中有规则编号，就一定要使用
- 不要说"未找到"，除非真的完全没有相关内容
"""

USER_PROMPT = """【数码宝贝卡牌游戏问题】
{question}

请根据上方【参考资料】中的数码宝贝卡牌游戏规则回答。"""


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
                model="qwen3.5-plus",  # 可选: qwen-turbo, qwen-plus, qwen-max
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
    
    def _call_llm(self, context: str, question: str, system_prompt: str = None) -> str:
        """实际调用 LLM 的方法
        
        Args:
            context: 上下文信息
            question: 用户问题
            system_prompt: 自定义系统提示词（可选）
        """
        # 如果提供了自定义系统提示词，将其放在最前面作为身份定义
        # 然后是默认的任务说明
        if system_prompt:
            # 配置的系统提示词定义身份和原则
            # 默认的SYSTEM_PROMPT定义具体任务
            combined_prompt = f"""{system_prompt}

---

{SYSTEM_PROMPT}"""
            prompt = ChatPromptTemplate.from_messages([
                ("system", combined_prompt),
                ("human", USER_PROMPT)
            ])
        else:
            prompt = self.prompt
        
        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": question})
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    def generate_answer(self, question: str, context_docs: List[dict], system_prompt: str = None, log_callback=None) -> str:
        """根据检索到的文档生成回答，带日志
        
        Args:
            question: 用户问题
            context_docs: 上下文文档列表
            system_prompt: 自定义系统提示词（可选，如果不提供则使用默认的）
            log_callback: 日志回调函数
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            print(f"[LLM] {msg}")
        
        start_time = time.time()
        
        # 步骤1: 构建上下文
        log("📝 步骤1/3: 构建上下文...")
        context_parts = []
        card_count = 0
        rule_count = 0
        
        for i, doc in enumerate(context_docs, 1):
            title = doc['metadata'].get('title', '未知来源')
            doc_type = doc.get('doc_type', '')
            
            # 区分卡牌数据和规则数据
            if doc_type == 'card':
                card_count += 1
                type_label = "卡牌效果"
                # 提取卡牌编号
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
        if system_prompt:
            log(f"   使用自定义系统提示词（{len(system_prompt)} 字符）")
        
        try:
            result = self._call_llm(context, question, system_prompt)
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
