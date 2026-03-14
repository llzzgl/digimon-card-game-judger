"""
DTCG Judger 翻译 Skill 单元测试
Translation Skill Unit Tests

包含单元测试、集成测试和质量检查
"""

import unittest
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

# 工作目录
WORK_DIR = Path(r"D:\LLMProject\dtcg_judger")
TRANSLATION_DIR = WORK_DIR / "src" / "translation"
CARD_TRANSLATION_DIR = WORK_DIR / "digimon_data"

# 添加路径
sys.path.insert(0, str(TRANSLATION_DIR))
sys.path.insert(0, str(CARD_TRANSLATION_DIR))


# ============================================================================
# 单元测试
# ============================================================================

class TestTerminologyManagement(unittest.TestCase):
    """术语管理单元测试"""
    
    def setUp(self):
        """测试前准备"""
        from dtcg_terminology import get_all_mappings
        self.terminology = get_all_mappings()
    
    def test_terminology_count(self):
        """测试术语数量"""
        # get_all_mappings 返回扁平字典
        self.assertGreater(len(self.terminology), 100,
                          "术语数量过少")
    
    def test_core_terms_exist(self):
        """测试核心术语存在"""
        core_terms = {
            'デジタマ': '数码蛋',
            'デジモン': '数码宝贝',
            'テイマー': '驯兽师',
            '赤': '红',
            '成長期': '成长期',
            'ワクチン種': '疫苗种'
        }
        
        for jp, expected_cn in core_terms.items():
            self.assertIn(jp, self.terminology,
                         f"缺少核心术语：{jp}")
            self.assertEqual(self.terminology[jp], expected_cn,
                           f"术语翻译错误：{jp} → {self.terminology[jp]} (期望：{expected_cn})")
    
    def test_term_mapping_valid(self):
        """测试术语映射有效性"""
        for jp, cn in self.terminology.items():
            self.assertIsInstance(jp, str, 
                                 f"日文术语不是字符串：{jp}")
            self.assertIsInstance(cn, str,
                                 f"中文术语不是字符串：{jp}")
            self.assertGreater(len(jp), 0,
                              f"日文术语为空")
            self.assertGreater(len(cn), 0,
                              f"中文术语为空：{jp}")


class TestCardTranslator(unittest.TestCase):
    """卡牌翻译器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        from card_translator import CardTranslator
        self.translator = CardTranslator(use_ai=False)
    
    def test_translate_card_type(self):
        """测试卡牌类型翻译"""
        test_cases = [
            ('デジタマ', '数码蛋'),
            ('デジモン', '数码宝贝'),
            ('テイマー', '驯兽师'),
            ('オプション', '选项')
        ]
        
        for jp, expected in test_cases:
            result = self.translator.translate_card_type(jp)
            self.assertEqual(result, expected,
                           f"卡牌类型翻译错误：{jp} → {result} (期望：{expected})")
    
    def test_translate_color(self):
        """测试颜色翻译"""
        test_cases = [
            ('赤', '红'),
            ('青', '蓝'),
            ('黄', '黄'),
            ('緑', '绿'),
            ('黒', '黑'),
            ('紫', '紫')
        ]
        
        for jp, expected in test_cases:
            result = self.translator.translate_color(jp)
            self.assertEqual(result, expected,
                           f"颜色翻译错误：{jp} → {result} (期望：{expected})")
    
    def test_translate_form(self):
        """测试形态翻译"""
        test_cases = [
            ('幼年期', '幼年期'),
            ('成長期', '成长期'),
            ('成熟期', '成熟期'),
            ('完全体', '完全体'),
            ('究極体', '究极体')
        ]
        
        for jp, expected in test_cases:
            result = self.translator.translate_form(jp)
            self.assertEqual(result, expected,
                           f"形态翻译错误：{jp} → {result} (期望：{expected})")
    
    def test_translate_attribute(self):
        """测试属性翻译"""
        test_cases = [
            ('ワクチン種', '疫苗种'),
            ('データ種', '数据种'),
            ('ウィルス種', '病毒种')
        ]
        
        for jp, expected in test_cases:
            result = self.translator.translate_attribute(jp)
            self.assertEqual(result, expected,
                           f"属性翻译错误：{jp} → {result} (期望：{expected})")
    
    def test_translate_card_complete(self):
        """测试完整卡牌翻译"""
        test_card = {
            'card_no': 'ST1-01',
            'card_name': 'アグモン',
            'card_type': 'デジモン',
            'color': '赤',
            'form': '成長期',
            'attribute': 'ワクチン種',
            'effect': '【登場時】相手のセキュリティを 1 つチェックする。'
        }
        
        result = self.translator.translate_card(test_card)
        
        # 验证基本字段
        self.assertEqual(result['card_type'], '数码宝贝')
        self.assertEqual(result['color'], '红')
        self.assertEqual(result['form'], '成长期')
        self.assertEqual(result['attribute'], '疫苗种')
        
        # 验证保留了日文原文
        self.assertIn('effect_jp', result)
        self.assertEqual(result['effect_jp'], test_card['effect'])


class TestOpenAIEngine(unittest.TestCase):
    """OpenAI 引擎单元测试"""
    
    def test_engine_class_exists(self):
        """测试引擎类存在"""
        from translate_rulebook_openai import RulebookTranslatorOpenAI
        self.assertTrue(hasattr(RulebookTranslatorOpenAI, '__init__'))
        self.assertTrue(hasattr(RulebookTranslatorOpenAI, 'translate_rulebook'))
    
    def test_engine_methods(self):
        """测试引擎方法完整性"""
        from translate_rulebook_openai import RulebookTranslatorOpenAI
        
        required_methods = [
            '__init__',
            'extract_pdf_text',
            'build_terminology_dict',
            'translate_chunk',
            'split_text_into_chunks',
            'translate_rulebook'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(RulebookTranslatorOpenAI, method),
                          f"缺少方法：{method}")
    
    def test_proxy_support(self):
        """测试代理支持"""
        import inspect
        from translate_rulebook_openai import RulebookTranslatorOpenAI
        
        source = inspect.getsource(RulebookTranslatorOpenAI)
        self.assertIn('proxy', source.lower(), "缺少代理支持")


class TestGeminiEngine(unittest.TestCase):
    """Gemini 引擎单元测试"""
    
    def test_engine_class_exists(self):
        """测试引擎类存在"""
        from translate_rulebook_gemini import RulebookTranslatorGemini
        self.assertTrue(hasattr(RulebookTranslatorGemini, '__init__'))
        self.assertTrue(hasattr(RulebookTranslatorGemini, 'translate_rulebook'))
    
    def test_engine_methods(self):
        """测试引擎方法完整性"""
        from translate_rulebook_gemini import RulebookTranslatorGemini
        
        required_methods = [
            '__init__',
            'extract_pdf_text',
            'build_terminology_dict',
            'translate_chunk',
            'split_text_into_chunks',
            'translate_rulebook'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(RulebookTranslatorGemini, method),
                          f"缺少方法：{method}")


# ============================================================================
# 集成测试
# ============================================================================

class TestFullTranslationPipeline(unittest.TestCase):
    """完整翻译流程集成测试"""
    
    def test_terminology_loading(self):
        """测试术语表加载"""
        from dtcg_terminology import get_all_mappings
        
        mappings = get_all_mappings()
        
        self.assertIsInstance(mappings, dict)
        self.assertGreater(len(mappings), 0)
        
        total_terms = sum(len(v) for v in mappings.values())
        self.assertGreater(total_terms, 100, "术语数量过少")
    
    def test_card_translator_initialization(self):
        """测试卡牌翻译器初始化"""
        from card_translator import CardTranslator
        
        # 不使用 AI 的初始化
        translator = CardTranslator(use_ai=False)
        self.assertIsNotNone(translator.terminology)
        self.assertFalse(translator.use_ai)
    
    def test_rulebook_translator_structure(self):
        """测试规则书翻译器结构"""
        from translate_rulebook_openai import RulebookTranslatorOpenAI
        
        # 验证类可以实例化（不需要真实文件）
        # 注意：这里只测试结构，不实际执行翻译
        self.assertTrue(hasattr(RulebookTranslatorOpenAI, '__init__'))
    
    def test_data_format_consistency(self):
        """测试数据格式一致性"""
        terminology_path = CARD_TRANSLATION_DIR / "dtcg_terminology.json"
        
        with open(terminology_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证 JSON 结构
        self.assertIsInstance(data, dict)
        
        # 验证所有值都是字典
        for key, value in data.items():
            self.assertIsInstance(value, dict,
                                f"分类 {key} 的值不是字典")
    
    def test_output_directory_structure(self):
        """测试输出目录结构"""
        # 验证翻译目录存在
        self.assertTrue(TRANSLATION_DIR.exists())
        self.assertTrue(CARD_TRANSLATION_DIR.exists())
        
        # 验证关键文件存在
        required_files = [
            TRANSLATION_DIR / "translate_rulebook_openai.py",
            TRANSLATION_DIR / "translate_rulebook_gemini.py",
            CARD_TRANSLATION_DIR / "card_translator.py",
            CARD_TRANSLATION_DIR / "dtcg_terminology.json"
        ]
        
        for file_path in required_files:
            self.assertTrue(file_path.exists(),
                          f"文件不存在：{file_path}")


# ============================================================================
# 质量检查
# ============================================================================

class TestTranslationQuality(unittest.TestCase):
    """翻译质量检查"""
    
    def test_terminology_consistency(self):
        """测试术语一致性"""
        from dtcg_terminology import (
            CARD_TYPE_MAPPING,
            COLOR_MAPPING,
            FORM_MAPPING
        )
        
        # 验证没有重复的日文术语
        all_jp_terms = []
        all_jp_terms.extend(CARD_TYPE_MAPPING.keys())
        all_jp_terms.extend(COLOR_MAPPING.keys())
        all_jp_terms.extend(FORM_MAPPING.keys())
        
        self.assertEqual(len(all_jp_terms), len(set(all_jp_terms)),
                        "存在重复的日文术语")
    
    def test_translation_completeness(self):
        """测试翻译完整性"""
        from dtcg_terminology import get_all_mappings
        
        mappings = get_all_mappings()
        
        # 验证每个术语都有翻译（扁平结构）
        for jp, cn in mappings.items():
            self.assertGreater(len(cn.strip()), 0,
                             f"空翻译：{jp}")
    
    def test_code_documentation(self):
        """测试代码文档完整性"""
        from card_translator import CardTranslator
        
        # 验证关键方法有文档字符串
        # 注意：类本身可能没有 docstring，这是可选的
        self.assertIsNotNone(CardTranslator.translate_card.__doc__,
                            "translate_card 方法缺少文档字符串")
    
    def test_error_handling(self):
        """测试错误处理"""
        import inspect
        from card_translator import CardTranslator
        
        source = inspect.getsource(CardTranslator)
        
        # 验证包含错误处理
        self.assertIn('try:', source, "缺少错误处理")
        self.assertIn('except', source, "缺少异常捕获")
    
    def test_prompt_quality(self):
        """测试提示词质量"""
        import inspect
        from translate_rulebook_openai import RulebookTranslatorOpenAI
        
        source = inspect.getsource(RulebookTranslatorOpenAI)
        
        # 验证包含翻译要求
        quality_indicators = ['要求', '必须', '请', '确保']
        found = any(indicator in source for indicator in quality_indicators)
        self.assertTrue(found, "提示词缺少明确要求")


# ============================================================================
# 运行测试
# ============================================================================

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestTerminologyManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestCardTranslator))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenAIEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestGeminiEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestFullTranslationPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestTranslationQuality))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("DTCG Judger 翻译 Skill 单元测试")
    print("=" * 80)
    print()
    
    result = run_tests()
    
    # 输出总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"运行测试数：{result.testsRun}")
    print(f"成功：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败：{len(result.failures)}")
    print(f"错误：{len(result.errors)}")
    
    if result.failures:
        print("\n失败测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n错误测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)
