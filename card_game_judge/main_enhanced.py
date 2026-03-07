# -*- coding: utf-8 -*-
"""
数码宝贝卡牌智能裁判 - 增强版
改进的 RAG 检索 + 场面分析 + 结构化 Prompt 拼接

主要改进：
1. 分层检索策略 - 根据问题类型智能选择检索源
2. 增强查询处理 - 识别效果时机、处理顺序等关键信息
3. 场面分析器 - 专门处理复杂场面的效果诱发和处理顺序
4. 结构化 Prompt - 改进上下文组织和 prompt 拼接
5. 引用溯源 - 答案标注来源

使用方法：
    python main_enhanced.py --port 8000
    python main_enhanced.py --test "我方联展了 bt23-032 土偶兽..."
"""
import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import LLM_MODEL
from app.vector_store import vector_store
from app.llm_service import LLMService
from app.enhanced_query_processor import enhanced_query_processor
from app.enhanced_vector_store import create_enhanced_vector_store
from app.enhanced_llm_service import create_enhanced_llm_service
from app.scenario_analyzer import scenario_analyzer


class EnhancedCardGameJudge:
    """增强版卡牌游戏裁判"""
    
    def __init__(self):
        print("🚀 初始化增强版裁判系统...")
        
        # 基础服务
        self.base_llm = LLMService()
        self.base_vector_store = vector_store
        
        # 增强服务
        self.enhanced_vs = create_enhanced_vector_store(self.base_vector_store)
        self.enhanced_llm = create_enhanced_llm_service(self.base_llm)
        
        # 将增强向量存储注入到 LLM 服务（用于上下文构建）
        self.base_llm.vector_store = self.enhanced_vs
        
        print("✅ 初始化完成")
        print(f"   LLM 模型：{LLM_MODEL}")
        print(f"   检索策略：分层检索 + 卡牌感知")
        print(f"   场面分析：启用")
    
    def query(self, question: str, use_scenario_analysis: bool = False) -> str:
        """
        查询裁判
        
        Args:
            question: 用户问题
            use_scenario_analysis: 是否使用专门的场面分析
        
        Returns:
            裁判回答
        """
        start_time = time.time()
        
        # 步骤 1: 分析查询
        print("\n📊 步骤 1/4: 分析查询...")
        query_analysis = enhanced_query_processor.analyze_scenario(question)
        card_numbers = query_analysis["involved_cards"]
        
        print(f"   问题类型：{query_analysis['question_type']}")
        print(f"   涉及卡牌：{card_numbers}")
        print(f"   需要顺序分析：{query_analysis['needs_sequence_analysis']}")
        print(f"   需要连锁分析：{query_analysis['needs_chain_analysis']}")
        
        # 步骤 2: 智能检索
        print("\n🔍 步骤 2/4: 智能检索...")
        search_results = self.enhanced_vs.context_aware_search(
            query=question,
            query_analysis=query_analysis,
            card_numbers=card_numbers,
            top_k=12
        )
        print(f"   检索到 {len(search_results)} 条结果")
        
        # 步骤 3: 生成回答
        print("\n🤖 步骤 3/4: 生成回答...")
        
        def log_callback(msg):
            print(f"   {msg}")
        
        if use_scenario_analysis or query_analysis["needs_sequence_analysis"]:
            # 使用专门的场面分析
            answer = self.enhanced_llm.generate_scenario_analysis(
                question=question,
                search_results=search_results,
                query_analysis=query_analysis,
                log_callback=log_callback
            )
        else:
            # 使用增强版回答生成
            answer = self.enhanced_llm.generate_enhanced_answer(
                question=question,
                search_results=search_results,
                query_analysis=query_analysis,
                log_callback=log_callback
            )
        
        # 步骤 4: 后处理和引用标注
        print("\n📝 步骤 4/4: 后处理...")
        answer = self._add_citations(answer, search_results)
        
        elapsed = time.time() - start_time
        print(f"\n✅ 完成，总耗时：{elapsed:.2f}s")
        
        return answer
    
    def _add_citations(self, answer: str, search_results: List[Dict]) -> str:
        """添加引用标注"""
        # 简单实现：在答案末尾添加参考来源
        if not search_results:
            return answer
        
        citations = ["\n\n---", "【参考来源】"]
        seen_titles = set()
        
        for i, result in enumerate(search_results[:5], 1):
            title = result['metadata'].get('title', '未知')
            doc_type = result.get('doc_type', 'rule')
            type_label = {"rule": "规则", "ruling": "裁定", "case": "判例", "card": "卡牌"}.get(doc_type, doc_type)
            
            if title not in seen_titles:
                citations.append(f"{i}. {title} ({type_label})")
                seen_titles.add(title)
        
        return answer + "\n".join(citations)
    
    def test_scenario(self, scenario_text: str) -> str:
        """测试场面分析"""
        print("=" * 80)
        print("场面分析测试")
        print("=" * 80)
        return self.query(scenario_text, use_scenario_analysis=True)


def main():
    parser = argparse.ArgumentParser(description="数码宝贝卡牌智能裁判 - 增强版")
    parser.add_argument("--port", type=int, default=8000, help="Web UI 端口")
    parser.add_argument("--no-ui", action="store_true", help="仅启动 API 服务")
    parser.add_argument("--test", type=str, help="测试问题")
    parser.add_argument("--test-file", type=str, help="从文件读取测试问题")
    args = parser.parse_args()
    
    # 创建裁判实例
    judge = EnhancedCardGameJudge()
    
    # 测试模式
    if args.test:
        answer = judge.test_scenario(args.test)
        print("\n" + "=" * 80)
        print("【裁判回答】")
        print("=" * 80)
        print(answer)
        print("=" * 80)
        return
    
    if args.test_file:
        test_file = Path(args.test_file)
        if test_file.exists():
            test_question = test_file.read_text(encoding='utf-8').strip()
            answer = judge.test_scenario(test_question)
            print("\n" + "=" * 80)
            print("【裁判回答】")
            print("=" * 80)
            print(answer)
            print("=" * 80)
            return
        else:
            print(f"错误：文件不存在 - {test_file}")
            return
    
    # 启动 Web UI 或 API
    if args.no_ui:
        print(f"\n🚀 启动 API 服务，端口：{args.port}")
        print(f"📖 API 文档：http://localhost:{args.port}/docs")
        # TODO: 实现 API 启动逻辑
        print("⚠️ API 服务实现中，请先使用 --test 参数测试")
    else:
        print(f"\n🚀 启动 Web UI，端口：{args.port}")
        print(f"🌐 访问地址：http://localhost:{args.port}")
        # TODO: 实现 Web UI 启动逻辑
        print("⚠️ Web UI 实现中，请先使用 --test 参数测试")


if __name__ == "__main__":
    main()
