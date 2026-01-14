from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import List
import time
import os

from app.config import LLM_MODEL, OPENAI_API_KEY, GOOGLE_API_KEY

# 如果需要代理访问 Google API，取消下面的注释并修改代理地址
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"


SYSTEM_PROMPT = """你是一位专业的数码宝贝卡牌游戏（DTCG）裁判。你的职责是根据玩家描述的游戏场面，结合规则和卡牌效果，给出准确的裁定。

【你的工作方式】
1. 仔细分析玩家描述的场面状况
2. 识别涉及的卡牌及其效果
3. 根据规则判断效果的发动条件和处理顺序
4. 给出清晰、有条理的裁定说明

【回答格式要求】
1. 先列出涉及的卡牌及其关键效果
2. 分析效果的发动时机和条件
3. 按照正确的处理顺序说明每一步
4. 如有多种可能的处理方式，分别说明
5. 引用规则时标注来源，如「根据【参考1】...」

【重要规则提醒】
- 效果处理遵循"先发动先处理"原则
- 同时满足发动条件的效果，回合玩家优先选择处理顺序
- 【登场时】【进化时】等时机效果在对应动作完成后发动
- 连锁效果需要按照正确顺序逐一处理

【参考资料】
{context}
"""

USER_PROMPT = """【玩家提问】
{question}

请作为裁判，分析上述场面并给出裁定。要求：
1. 列出涉及的卡牌效果
2. 说明效果处理顺序
3. 给出最终裁定结果"""


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
            return Ollama(model="qwen2:7b", temperature=0.1)
        elif LLM_MODEL == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                google_api_key=GOOGLE_API_KEY
            )
        else:
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                openai_api_key=OPENAI_API_KEY
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
            
            context_parts.append(
                f"【参考{i}】\n"
                f"来源：{title}（{type_label}）\n"
                f"内容：{doc['content']}\n"
            )
        
        context = "\n\n".join(context_parts)
        log(f"✅ 上下文构建完成，共 {len(context_docs)} 个参考文档，{len(context)} 字符")
        
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
