"""
微调模型 LLM 服务
使用本地微调后的 Qwen2 模型（LoRA 适配器）
"""
from langchain.llms.base import LLM
from langchain.prompts import ChatPromptTemplate
from typing import List, Optional, Any
import time
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


SYSTEM_PROMPT = """你是数码宝贝卡牌游戏（DTCG）的专业裁判助手。

【你的能力】
1. 解释游戏规则和关键词效果
2. 查询卡牌信息和效果
3. 分析复杂的游戏场面
4. 判断效果的触发时机和处理顺序
5. 提供裁定建议

【分析方法】
当面对复杂场面时，请按以下步骤分析：
1. 【涉及的卡牌效果】- 列出所有相关卡牌及其关键效果
2. 【相关规则】- 引用适用的规则条款
3. 【效果时机分析】- 分析各效果的触发时机
4. 【处理顺序】- 说明效果的处理顺序（回合玩家优先）
5. 【场面推导】- 逐步推导场面变化
6. 【结论】- 给出明确的结论

【重要原则】
• 基于官方综合规则进行分析
• 逻辑清晰，步骤明确
• 如果卡牌效果不明确，说明需要查看完整效果文本
• 如果规则有歧义，说明需要官方裁定
• 复杂情况建议参考官方裁定

【规则参考】
{context}

请根据规则参考和你的专业知识，详细分析并回答问题。
"""

USER_PROMPT = """【问题】
{question}

请根据规则参考分析。如果规则参考不足，请说明。"""


class FinetunedQwenLLM(LLM):
    """微调后的 Qwen2 模型"""
    
    model: Any = None
    tokenizer: Any = None
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_length: int = 2048
    temperature: float = 0.1
    top_p: float = 0.9
    
    def __init__(self, lora_path: str, base_model: str = "Qwen/Qwen2-1.5B-Instruct", **kwargs):
        super().__init__(**kwargs)
        self._load_model(lora_path, base_model)
    
    def _load_model(self, lora_path: str, base_model: str):
        """加载微调后的模型"""
        print(f"📥 加载微调模型...")
        print(f"   基础模型: {base_model}")
        print(f"   LoRA 路径: {lora_path}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model,
            trust_remote_code=True,
            padding_side="right"
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 检查是否是合并后的模型（没有 LoRA 路径或路径为空）
        if not lora_path or lora_path.strip() == "":
            print("   检测到合并模型，直接加载...")
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            if self.device == "cuda":
                self.model = self.model.to(self.device)
        else:
            # 加载基础模型 + LoRA
            print("   正在加载基础模型...")
            base_model_obj = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # 手动移动到设备
            if self.device == "cuda":
                base_model_obj = base_model_obj.to(self.device)
            
            # 加载 LoRA 适配器
            print("   正在加载 LoRA 适配器...")
            try:
                self.model = PeftModel.from_pretrained(
                    base_model_obj, 
                    lora_path,
                    is_trainable=False
                )
            except Exception as e:
                print(f"   ⚠️ LoRA 加载失败: {e}")
                print("   💡 建议运行 merge_lora.py 合并权重")
                raise
        
        self.model.eval()
        print(f"✅ 模型加载完成，设备: {self.device}")
    
    @property
    def _llm_type(self) -> str:
        return "finetuned_qwen"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """调用模型生成回答"""
        # 编码输入
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length
        ).to(self.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # 解码输出
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return response.strip()


class FinetunedLLMService:
    """微调模型服务"""
    
    def __init__(self, lora_path: str = None, base_model: str = "Qwen/Qwen2-1.5B-Instruct"):
        # 默认 LoRA 路径
        if lora_path is None:
            lora_path = str(Path(__file__).parent.parent / "finetune" / "output" / "dtcg_qwen_lora")
        
        self.llm = FinetunedQwenLLM(lora_path=lora_path, base_model=base_model)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT)
        ])
        self.timeout = 60
    
    def _call_llm(self, context: str, question: str) -> str:
        """调用 LLM"""
        # 构建完整的 prompt
        messages = self.prompt.format_messages(context=context, question=question)
        
        # 转换为 Qwen2 的格式
        prompt_text = ""
        for msg in messages:
            if msg.type == "system":
                prompt_text += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
            elif msg.type == "human":
                prompt_text += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        prompt_text += "<|im_start|>assistant\n"
        
        # 调用模型
        response = self.llm._call(prompt_text)
        return response
    
    def generate_answer(self, question: str, context_docs: List[dict], log_callback=None) -> str:
        """根据检索到的文档生成回答"""
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
        
        # 步骤2: 调用微调模型
        log(f"🤖 步骤2/3: 调用微调模型...")
        
        try:
            result = self._call_llm(context, question)
            elapsed = time.time() - start_time
            log(f"✅ 模型响应完成，耗时 {elapsed:.1f}s")
            
            # 步骤3: 返回结果
            log(f"📤 步骤3/3: 返回结果，共 {len(result)} 字符")
            return result
                    
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            log(f"❌ 模型调用失败，耗时 {elapsed:.1f}s")
            log(f"❌ 错误详情: {error_msg}")
            raise


# 创建全局实例
llm_service = None

def get_finetuned_llm_service(lora_path: str = None, base_model: str = "Qwen/Qwen2-1.5B-Instruct"):
    """获取微调模型服务实例（单例模式）"""
    global llm_service
    if llm_service is None:
        llm_service = FinetunedLLMService(lora_path=lora_path, base_model=base_model)
    return llm_service
