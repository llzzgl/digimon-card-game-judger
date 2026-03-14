#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
裁判系统集成模块 - 图片识别 + 裁定询问功能

功能:
1. 卡牌图片识别 (OCR + 视觉理解)
2. 图片 + 文字混合询问
3. 统一的 API 接口
4. Web UI 支持

作者：管理者
创建时间：2026-03-14
"""

import os
import sys
import base64
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import io

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"


class CardImageRecognizer:
    """卡牌图片识别器"""
    
    def __init__(self, use_vision_llm: bool = True):
        """
        初始化识别器
        
        Args:
            use_vision_llm: 是否使用视觉 LLM 进行识别
        """
        self.use_vision_llm = use_vision_llm
        self.vision_model = None
        self._init_vision_model()
    
    def _init_vision_model(self):
        """初始化视觉模型"""
        if not self.use_vision_llm:
            return
        
        try:
            # 尝试使用 Google Gemini Vision API
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
                print("[OK] 视觉模型初始化成功 (Gemini 1.5 Flash)")
            else:
                print("[WARN] 未设置 GEMINI_API_KEY，使用备用识别方案")
                self.vision_model = None
        except Exception as e:
            print(f"[WARN] 视觉模型初始化失败：{e}")
            self.vision_model = None
    
    def recognize_card(self, image_data: bytes) -> Dict[str, Any]:
        """
        识别卡牌图片
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            识别结果字典，包含:
            - card_number: 卡牌编号 (如果识别到)
            - card_name: 卡牌名称
            - confidence: 置信度
            - raw_text: 原始识别文本
            - analysis: 分析结果
        """
        result = {
            "card_number": None,
            "card_name": None,
            "confidence": 0.0,
            "raw_text": "",
            "analysis": "",
            "error": None
        }
        
        try:
            # 使用视觉 LLM 识别
            if self.vision_model:
                return self._recognize_with_vision(image_data, result)
            else:
                # 备用方案：返回基础信息
                result["error"] = "视觉模型未初始化"
                result["analysis"] = "请通过文字描述卡牌或提供卡牌编号"
                return result
                
        except Exception as e:
            result["error"] = str(e)
            import traceback
            result["analysis"] = f"识别失败：{traceback.format_exc()}"
            return result
    
    def _recognize_with_vision(self, image_data: bytes, result: Dict) -> Dict:
        """使用视觉 LLM 识别卡牌"""
        try:
            # 创建 PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # 构建提示词
            prompt = """
请分析这张数码宝贝卡牌图片，提取以下信息：

1. 卡牌编号 (格式如 BT1-001, ST1-001 等)
2. 卡牌名称 (日文和中文，如果能识别)
3. 卡牌类型 (数码兽/选项卡等)
4. 主要效果文本

请以 JSON 格式返回，例如：
{
    "card_number": "BT1-001",
    "card_name_jp": "アグモン",
    "card_name_cn": "亚古兽",
    "card_type": "数码兽",
    "effect_summary": "登场时效果...",
    "confidence": 0.95
}

如果某些信息无法识别，对应字段设为 null。
"""
            
            # 调用视觉模型
            response = self.vision_model.generate_content([prompt, image])
            
            # 解析响应
            response_text = response.text.strip()
            result["raw_text"] = response_text
            
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                result["card_number"] = parsed.get("card_number")
                result["card_name"] = parsed.get("card_name_cn") or parsed.get("card_name_jp")
                result["confidence"] = parsed.get("confidence", 0.8)
                result["analysis"] = f"识别到卡牌：{result['card_number']} {result['card_name']}"
            else:
                result["analysis"] = response_text
                result["confidence"] = 0.5
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            result["analysis"] = f"视觉识别失败：{e}"
            return result
    
    def recognize_with_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """
        使用 OCR 识别卡牌文字 (备用方案)
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            识别结果
        """
        result = {
            "text_lines": [],
            "card_number": None,
            "analysis": ""
        }
        
        try:
            # 尝试使用 EasyOCR
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en', 'ja'])
            
            image = Image.open(io.BytesIO(image_data))
            ocr_result = reader.readtext(image)
            
            for (bbox, text, prob) in ocr_result:
                result["text_lines"].append({
                    "text": text,
                    "confidence": prob,
                    "bbox": bbox
                })
                
                # 尝试提取卡牌编号
                import re
                card_no_match = re.search(
                    r'(BT|ST|EX|P|RB|LM)-?\d{1,2}-?\d{2,3}',
                    text,
                    re.IGNORECASE
                )
                if card_no_match:
                    result["card_number"] = card_no_match.group().upper()
            
            result["analysis"] = f"OCR 识别到 {len(result['text_lines'])} 行文字"
            if result["card_number"]:
                result["analysis"] += f"，卡牌编号：{result['card_number']}"
            
            return result
            
        except ImportError:
            result["analysis"] = "未安装 OCR 库，请运行：pip install easyocr"
            return result
        except Exception as e:
            result["analysis"] = f"OCR 识别失败：{e}"
            return result


class JudgeIntegrationService:
    """裁判系统集成服务"""
    
    def __init__(self):
        """初始化集成服务"""
        self.recognizer = CardImageRecognizer()
        
        # 导入裁判系统组件
        try:
            from app.vector_store import vector_store
            from app.llm_service import llm_service
            from app.query_processor import query_processor
            from app.memory_manager import memory_manager
            
            self.vector_store = vector_store
            self.llm_service = llm_service
            self.query_processor = query_processor
            self.memory_manager = memory_manager
            
            print("[OK] 裁判系统集成服务初始化成功")
        except Exception as e:
            print(f"[WARN] 裁判系统组件加载失败：{e}")
            self.vector_store = None
            self.llm_service = None
            self.query_processor = None
            self.memory_manager = None
    
    def process_image_query(
        self,
        image_data: bytes,
        user_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理图片 + 询问请求
        
        Args:
            image_data: 图片二进制数据
            user_question: 用户文字问题 (可选)
            
        Returns:
            处理结果，包含:
            - recognition: 图片识别结果
            - answer: 裁定回答
            - sources: 参考来源
            - memory_updates: 记忆更新
        """
        result = {
            "recognition": None,
            "answer": "",
            "sources": [],
            "memory_updates": [],
            "error": None
        }
        
        try:
            # 步骤 1: 识别图片
            print("\n[步骤 1] [INFO] 识别卡牌图片...")
            recognition = self.recognizer.recognize_card(image_data)
            result["recognition"] = recognition
            
            if recognition.get("error"):
                print(f"  [WARN] 识别警告：{recognition['error']}")
            
            # 步骤 2: 构建查询
            print("\n[步骤 2] [INFO] 构建查询...")
            query_parts = []
            
            # 添加识别到的卡牌信息
            if recognition.get("card_number"):
                query_parts.append(f"卡牌编号：{recognition['card_number']}")
            if recognition.get("card_name"):
                query_parts.append(f"卡牌名称：{recognition['card_name']}")
            if recognition.get("analysis"):
                query_parts.append(f"识别分析：{recognition['analysis']}")
            
            # 添加用户问题
            if user_question:
                query_parts.append(f"问题：{user_question}")
            else:
                query_parts.append("问题：请分析这张卡牌的效果和相关裁定")
            
            full_query = "\n".join(query_parts)
            print(f"  查询：{full_query[:100]}...")
            
            # 步骤 3: 执行检索和回答
            print("\n[步骤 3] [INFO] 检索和生成回答...")
            if self.query_processor and self.llm_service:
                answer_result = self._generate_answer(full_query, recognition)
                result["answer"] = answer_result["answer"]
                result["sources"] = answer_result["sources"]
            else:
                result["answer"] = "裁判系统未完全初始化，无法生成裁定"
            
            return result
            
        except Exception as e:
            import traceback
            result["error"] = f"处理失败：{e}"
            result["answer"] = traceback.format_exc()
            return result
    
    def _generate_answer(
        self,
        query: str,
        recognition: Dict
    ) -> Dict[str, Any]:
        """生成裁定回答"""
        from app.models import DocumentType
        
        result = {
            "answer": "",
            "sources": []
        }
        
        try:
            # 1. 如果识别到卡牌编号，精确检索
            card_docs = []
            if recognition.get("card_number"):
                card_numbers = [recognition["card_number"]]
                for card_no in card_numbers:
                    results = self.vector_store.search_by_card_number(
                        card_no,
                        translate_result=True
                    )
                    card_docs.extend(results)
            
            # 2. 语义检索规则和裁定
            rule_results = self.vector_store.search(
                query=query,
                doc_types=[DocumentType.RULE, DocumentType.RULING, DocumentType.CASE],
                top_k=5,
                translate_result=True
            )
            
            # 3. 搜索记忆
            memory_results = []
            if self.memory_manager.config.enable_memory_search:
                memory_results = self.memory_manager.search_memories(
                    query=query,
                    top_k=3
                )
            
            # 4. 构建上下文
            context_parts = []
            
            # 添加记忆
            for mem in memory_results:
                context_parts.append(
                    f"【已验证记忆】\n问题：{mem['question']}\n答案：{mem['answer']}"
                )
            
            # 添加卡牌效果
            for card_doc in card_docs:
                context_parts.append(
                    f"【卡牌效果】\n{card_doc['content']}"
                )
            
            # 添加规则/裁定
            for rule_doc in rule_results:
                context_parts.append(
                    f"【参考】{rule_doc['metadata'].get('title', '未知')}\n{rule_doc['content'][:500]}"
                )
            
            context = "\n\n".join(context_parts)
            
            # 5. 生成回答
            system_prompt = """你是一名专业的数码宝贝卡牌裁判。
请基于提供的参考资料，公正、准确地回答用户的问题。

要求:
1. 引用具体的规则来源
2. 区分卡牌效果和通用规则
3. 如果信息不足，说明需要补充的信息
4. 使用清晰的结构化格式
"""
            
            full_prompt = f"""{system_prompt}

参考资料:
{context}

用户问题:
{query}

请给出裁定:"""
            
            answer = self.llm_service.llm.generate(full_prompt)
            
            result["answer"] = answer
            result["sources"] = [
                {"title": doc["metadata"].get("title"), "type": doc.get("doc_type")}
                for doc in rule_results[:5]
            ]
            
            return result
            
        except Exception as e:
            result["answer"] = f"生成回答失败：{e}"
            return result


# 测试函数
def test_image_recognition(image_path: str):
    """测试图片识别功能"""
    print("=" * 60)
    print("测试卡牌图片识别")
    print("=" * 60)
    
    # 读取图片
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # 创建识别器
    recognizer = CardImageRecognizer()
    
    # 识别
    result = recognizer.recognize_card(image_data)
    
    print("\n识别结果:")
    print(f"  卡牌编号：{result.get('card_number')}")
    print(f"  卡牌名称：{result.get('card_name')}")
    print(f"  置信度：{result.get('confidence', 0):.2f}")
    print(f"  分析：{result.get('analysis')}")
    if result.get('error'):
        print(f"  错误：{result['error']}")
    
    return result


def test_integration_query(image_path: str, question: str = None):
    """测试完整集成查询"""
    print("\n" + "=" * 60)
    print("测试集成查询 (图片 + 询问)")
    print("=" * 60)
    
    # 读取图片
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # 创建服务
    service = JudgeIntegrationService()
    
    # 处理查询
    result = service.process_image_query(image_data, question)
    
    print("\n处理结果:")
    print(f"  识别：{result.get('recognition', {}).get('analysis', 'N/A')}")
    print(f"  回答：{result.get('answer', 'N/A')[:200]}...")
    print(f"  来源数量：{len(result.get('sources', []))}")
    if result.get('error'):
        print(f"  错误：{result['error']}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="裁判系统集成测试")
    parser.add_argument("--test-image", type=str, help="测试图片路径")
    parser.add_argument("--question", type=str, default=None, help="询问问题")
    
    args = parser.parse_args()
    
    if args.test_image:
        if os.path.exists(args.test_image):
            test_integration_query(args.test_image, args.question)
        else:
            print(f"错误：图片文件不存在 - {args.test_image}")
    else:
        print("请提供测试图片路径：python judge_integration.py --test-image <path>")
