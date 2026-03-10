"""
使用大模型智能提取中日文关键词对照
支持多种LLM：Qwen (通义千问)、Gemini、OpenAI
利用LLM的语义理解能力来识别真正的游戏机制关键词
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import os
from dotenv import load_dotenv
import time
from openai import OpenAI


class LLMKeywordExtractor:
    def __init__(self, base_dir, llm_type="qwen"):
        """
        初始化提取器
        
        Args:
            base_dir: 数据目录
            llm_type: LLM类型，可选 "qwen", "gemini", "openai"
        """
        self.base_dir = Path(base_dir)
        self.cn_cards = {}
        self.jp_cards = {}
        self.keywords = defaultdict(set)
        self.llm_type = llm_type
        
        # 加载环境变量
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent
        env_path = project_root / "card_game_judge" / ".env"
        
        print(f"尝试加载环境变量: {env_path}")
        print(f"文件存在: {env_path.exists()}")
        
        if env_path.exists():
            load_dotenv(env_path)
            print("环境变量已加载")
        else:
            print("未找到.env文件")
        
        # 初始化LLM客户端
        self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if self.llm_type == "qwen":
            self._init_qwen()
        elif self.llm_type == "gemini":
            self._init_gemini()
        elif self.llm_type == "openai":
            self._init_openai()
        else:
            raise ValueError(f"不支持的LLM类型: {self.llm_type}")
    
    def _init_qwen(self):
        """初始化通义千问"""
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            raise ValueError("请在.env文件中设置DASHSCOPE_API_KEY")
        
        print(f"API Key已加载: {api_key[:10]}...")
        
        # 使用OpenAI兼容接口
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://coding.dashscope.aliyuncs.com/v1"
        )
        self.model_name = "qwen3.5-plus"  # 或 "qwen-turbo", "qwen-max"
        
        print(f"已初始化通义千问模型: {self.model_name}")
    
    def _init_gemini(self):
        """初始化Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("请安装google-generativeai: pip install google-generativeai")
        
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("请在.env文件中设置GEMINI_API_KEY或GOOGLE_API_KEY")
        
        print(f"API Key已加载: {api_key[:10]}...")
        
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print("已初始化Gemini模型")
    
    def _init_openai(self):
        """初始化OpenAI"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("请在.env文件中设置OPENAI_API_KEY")
        
        print(f"API Key已加载: {api_key[:10]}...")
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"  # 或 "gpt-4", "gpt-3.5-turbo"
        
        print(f"已初始化OpenAI模型: {self.model_name}")
    
    def _call_llm(self, prompt):
        """
        统一的LLM调用接口
        
        Args:
            prompt: 提示词
            
        Returns:
            str: LLM响应文本
        """
        if self.llm_type == "qwen":
            return self._call_qwen(prompt)
        elif self.llm_type == "gemini":
            return self._call_gemini(prompt)
        elif self.llm_type == "openai":
            return self._call_openai(prompt)
    
    def _call_qwen(self, prompt):
        """调用通义千问"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一个数码宝贝卡牌游戏的专家，擅长识别游戏机制关键词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, prompt):
        """调用Gemini"""
        response = self.client.generate_content(prompt)
        return response.text
    
    def _call_openai(self, prompt):
        """调用OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一个数码宝贝卡牌游戏的专家，擅长识别游戏机制关键词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def load_chinese_cards(self):
        """加载中文卡牌数据"""
        cn_file = self.base_dir / "digimon_card_data_chiness" / "digimon_cards_cn.json"
        
        print(f"加载中文卡牌数据: {cn_file}")
        
        with open(cn_file, 'r', encoding='utf-8') as f:
            cards = json.load(f)
            for card in cards:
                card_no = card.get('card_no', '').upper()
                if card_no:
                    self.cn_cards[card_no] = card
        
        print(f"已加载 {len(self.cn_cards)} 张中文卡牌")
    
    def load_japanese_cards(self):
        """加载所有日文卡包数据"""
        print("加载日文卡牌数据...")
        
        jp_files = list(self.base_dir.glob("digimon_cards_*_cards.json"))
        
        for jp_file in jp_files:
            if "chiness" in str(jp_file):
                continue
                
            try:
                with open(jp_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_no = card.get('card_no', '').upper()
                        card_no = re.sub(r'_P\d+$', '', card_no)
                        if card_no and card_no not in self.jp_cards:
                            self.jp_cards[card_no] = card
            except Exception as e:
                print(f"读取文件 {jp_file.name} 时出错: {e}")
        
        print(f"已加载 {len(self.jp_cards)} 张日文卡牌")
    
    def collect_effect_samples(self, sample_size=100):
        """收集效果文本样本"""
        print(f"\n收集效果文本样本（目标: {sample_size}）...")
        
        samples = []
        
        for card_no, cn_card in self.cn_cards.items():
            if len(samples) >= sample_size:
                break
            
            normalized_no = card_no.replace('-', '').upper()
            
            jp_card = None
            if card_no in self.jp_cards:
                jp_card = self.jp_cards[card_no]
            elif normalized_no in self.jp_cards:
                jp_card = self.jp_cards[normalized_no]
            
            if not jp_card:
                continue
            
            # 收集效果文本
            for field in ['effect', 'inherited_effect', 'security_effect']:
                if len(samples) >= sample_size:
                    break
                    
                cn_text = cn_card.get(field, '') or ''
                jp_text = jp_card.get(field, '') or ''
                
                cn_text = cn_text.strip() if isinstance(cn_text, str) else ''
                jp_text = jp_text.strip() if isinstance(jp_text, str) else ''
                
                if cn_text and jp_text and len(cn_text) > 20:
                    samples.append({
                        'card_no': card_no,
                        'field': field,
                        'cn_text': cn_text,
                        'jp_text': jp_text
                    })
        
        print(f"收集到 {len(samples)} 个样本")
        return samples
    
    def extract_keywords_with_llm(self, samples, batch_size=10):
        """使用LLM批量提取关键词"""
        print(f"\n使用LLM提取关键词（每批 {batch_size} 个样本）...")
        print(f"总样本数: {len(samples)}")
        print(f"预计API调用: {(len(samples) + batch_size - 1) // batch_size} 次")
        
        all_keywords = defaultdict(set)
        
        # 检查是否有中间结果
        checkpoint_file = Path(__file__).parent / "llm_extraction_checkpoint.json"
        start_batch = 0
        
        if checkpoint_file.exists():
            print(f"\n发现检查点文件，加载已有结果...")
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    for cn_kw, jp_kws in checkpoint.get('keywords', {}).items():
                        all_keywords[cn_kw].update(jp_kws)
                    start_batch = checkpoint.get('last_batch', 0) + 1
                    print(f"已加载 {len(all_keywords)} 个关键词")
                    print(f"从批次 {start_batch + 1} 继续...")
            except Exception as e:
                print(f"加载检查点失败: {e}，从头开始")
                start_batch = 0
        
        total_batches = (len(samples) + batch_size - 1) // batch_size
        
        for i in range(start_batch, total_batches):
            batch_start = i * batch_size
            batch_end = min(batch_start + batch_size, len(samples))
            batch = samples[batch_start:batch_end]
            
            print(f"\n处理批次 {i + 1}/{total_batches} (样本 {batch_start + 1}-{batch_end})...")
            
            try:
                # 调用LLM（统一接口）
                response_text = self._call_llm(self._build_extraction_prompt(batch))
                
                # 解析响应
                keywords = self._parse_llm_response(response_text)
                
                # 合并结果
                for cn_kw, jp_kw in keywords:
                    all_keywords[cn_kw].add(jp_kw)
                
                print(f"  本批提取: {len(keywords)} 个关键词对")
                print(f"  累计总数: {len(all_keywords)} 个唯一关键词")
                
                # 保存检查点
                checkpoint = {
                    'last_batch': i,
                    'total_batches': total_batches,
                    'keywords': {cn: list(jp) for cn, jp in all_keywords.items()}
                }
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, ensure_ascii=False, indent=2)
                
                # 避免API限流
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print(f"\n\n用户中断！已保存进度到批次 {i}")
                print(f"下次运行将从批次 {i + 1} 继续")
                break
            except Exception as e:
                print(f"  处理批次时出错: {e}")
                import traceback
                traceback.print_exc()
                # 保存当前进度
                checkpoint = {
                    'last_batch': i,
                    'total_batches': total_batches,
                    'keywords': {cn: list(jp) for cn, jp in all_keywords.items()}
                }
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, ensure_ascii=False, indent=2)
                print(f"  已保存进度，可以重新运行继续")
                continue
        
        # 完成后删除检查点
        if checkpoint_file.exists() and i == total_batches - 1:
            checkpoint_file.unlink()
            print(f"\n提取完成，已删除检查点文件")
        
        print(f"\n总共提取到 {len(all_keywords)} 个唯一关键词")
        return all_keywords
    
    def _build_extraction_prompt(self, samples):
        """构建提取prompt"""
        prompt = """你是一个数码宝贝卡牌游戏的专家。请从以下中日文卡牌效果文本中提取游戏机制关键词的对照关系。

**提取规则：**
1. 只提取游戏机制相关的关键词，如：
   - 效果触发时机：登场时、进化时、攻击时等
   - 游戏动作：登场、进化、攻击、消灭、休眠等
   - 游戏区域：手牌、卡组、废弃区、安防区等
   - 关键词能力：贯通、突进、干扰、阻挡者等
   - 数值相关：DP、Lv、费用、内存值等

2. 不要提取：
   - 卡牌名称（如"亚古兽"、"暴龙兽"等）
   - 特征/种族名称（如"恐龙型"、"病毒种"等）
   - 完整的效果描述
   - 数字

3. 关键词应该是2-8个字的短词

4. 输出格式为JSON数组，每个元素是一个对象：{"cn": "中文关键词", "jp": "日文关键词"}

**卡牌效果文本样本：**

"""
        
        for idx, sample in enumerate(samples, 1):
            prompt += f"\n样本 {idx}:\n"
            prompt += f"中文: {sample['cn_text'][:200]}\n"
            prompt += f"日文: {sample['jp_text'][:200]}\n"
        
        prompt += """

请提取所有游戏机制关键词，输出JSON格式：
```json
[
  {"cn": "登场时", "jp": "登場時"},
  {"cn": "攻击", "jp": "アタック"},
  ...
]
```
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text):
        """解析LLM响应"""
        keywords = []
        
        try:
            # 尝试提取JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response_text
            
            data = json.loads(json_str)
            
            for item in data:
                cn = item.get('cn', '').strip()
                jp = item.get('jp', '').strip()
                
                if cn and jp and 2 <= len(cn) <= 8:
                    keywords.append((cn, jp))
        
        except Exception as e:
            print(f"    解析响应时出错: {e}")
            # 尝试逐行解析
            for line in response_text.split('\n'):
                if '"cn"' in line and '"jp"' in line:
                    try:
                        cn_match = re.search(r'"cn":\s*"([^"]+)"', line)
                        jp_match = re.search(r'"jp":\s*"([^"]+)"', line)
                        if cn_match and jp_match:
                            cn = cn_match.group(1).strip()
                            jp = jp_match.group(1).strip()
                            if cn and jp and 2 <= len(cn) <= 8:
                                keywords.append((cn, jp))
                    except:
                        continue
        
        return keywords
    
    def refine_keywords_with_llm(self, keywords):
        """使用LLM精炼和分类关键词"""
        print("\n使用LLM精炼和分类关键词...")
        
        # 构建关键词列表
        keyword_list = []
        for cn_kw, jp_kws in keywords.items():
            for jp_kw in jp_kws:
                keyword_list.append({"cn": cn_kw, "jp": jp_kw})
        
        prompt = f"""你是一个数码宝贝卡牌游戏的专家。请对以下提取的关键词进行精炼和分类。

**任务：**
1. 去除不是游戏机制关键词的项（如卡牌名称、特征名称等）
2. 合并重复或相似的关键词
3. 将关键词分类为：
   - timing: 效果触发时机
   - action: 游戏动作
   - zone: 游戏区域
   - ability: 关键词能力
   - value: 数值相关
   - card_type: 卡牌类型
   - other: 其他游戏术语

**关键词列表：**
{json.dumps(keyword_list[:100], ensure_ascii=False, indent=2)}

请输出精炼后的分类结果，JSON格式：
```json
{{
  "timing": [
    {{"cn": "登场时", "jp": "登場時"}},
    ...
  ],
  "action": [...],
  ...
}}
```
"""
        
        try:
            response_text = self._call_llm(prompt)
            
            # 解析响应
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                categorized = json.loads(json_str)
                return categorized
            
        except Exception as e:
            print(f"精炼关键词时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def save_keywords(self, keywords, output_file):
        """保存关键词"""
        print(f"\n保存关键词到: {output_file}")
        
        keywords_dict = {}
        for cn_kw, jp_kws in sorted(keywords.items()):
            keywords_dict[cn_kw] = sorted(list(jp_kws))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(keywords_dict, f, ensure_ascii=False, indent=2)
        
        print(f"关键词已保存，共 {len(keywords_dict)} 个词条")
    
    def save_categorized_keywords(self, categorized, output_file):
        """保存分类后的关键词"""
        print(f"\n保存分类关键词到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(categorized, f, ensure_ascii=False, indent=2)
        
        total = sum(len(items) for items in categorized.values())
        print(f"分类关键词已保存，共 {total} 个词条")
    
    def generate_report(self, keywords, output_file):
        """生成报告"""
        print(f"\n生成报告: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# LLM智能提取的中日文关键词对照表\n\n")
            f.write("本表通过大模型智能分析卡牌效果文本自动提取。\n\n")
            
            f.write("## 提取的关键词\n\n")
            f.write("| 中文 | 日文 |\n")
            f.write("|------|------|\n")
            
            for cn_kw in sorted(keywords.keys()):
                jp_terms = ', '.join(sorted(keywords[cn_kw]))
                f.write(f"| {cn_kw} | {jp_terms} |\n")
            
            f.write(f"\n## 总计\n\n")
            f.write(f"共 {len(keywords)} 个关键词\n")
        
        print("报告已生成")


def main():
    # 脚本在 term_mapping 目录，需要上一级到 digimon_card_data
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent
    
    # 尝试加载配置文件
    try:
        from llm_config import LLM_TYPE, MODEL_CONFIG, EXTRACTION_CONFIG
        llm_type = LLM_TYPE
        sample_size = EXTRACTION_CONFIG.get("sample_size", 50)
        batch_size = EXTRACTION_CONFIG.get("batch_size", 5)
        enable_refine = EXTRACTION_CONFIG.get("enable_refine", True)
    except ImportError:
        # 使用默认配置
        llm_type = "qwen"
        sample_size = 50
        batch_size = 5
        enable_refine = True
    
    print("=" * 60)
    print("LLM智能关键词提取工具")
    print("使用大模型的语义理解能力提取游戏机制关键词")
    print("=" * 60)
    print(f"数据目录: {base_dir}")
    print(f"LLM类型: {llm_type}")
    print(f"样本数量: {sample_size}")
    print(f"批次大小: {batch_size}")
    print()
    
    try:
        extractor = LLMKeywordExtractor(base_dir, llm_type=llm_type)
        
        extractor.load_chinese_cards()
        extractor.load_japanese_cards()
        
        # 收集样本
        samples = extractor.collect_effect_samples(sample_size=sample_size)
        
        # 使用LLM提取关键词
        keywords = extractor.extract_keywords_with_llm(samples, batch_size=batch_size)
        
        # 保存结果
        output_dir = script_dir
        extractor.save_keywords(keywords, output_dir / "llm_keywords_cn_jp.json")
        extractor.generate_report(keywords, output_dir / "llm_keywords_report.md")
        
        # 可选：使用LLM精炼和分类
        if len(keywords) > 0 and enable_refine:
            print("\n使用LLM进行精炼和分类...")
            categorized = extractor.refine_keywords_with_llm(keywords)
            if categorized:
                extractor.save_categorized_keywords(categorized, output_dir / "llm_keywords_categorized.json")
        
        print("\n" + "=" * 60)
        print("处理完成！")
        print("生成文件:")
        print("  - llm_keywords_cn_jp.json (LLM提取的关键词)")
        print("  - llm_keywords_report.md (报告)")
        if len(keywords) > 0 and enable_refine:
            print("  - llm_keywords_categorized.json (分类后的关键词)")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
