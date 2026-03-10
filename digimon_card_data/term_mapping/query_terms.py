"""
词汇对照表查询工具
提供便捷的中日文词汇查询功能
"""

import json
from pathlib import Path


class TermQuery:
    def __init__(self, mapping_file):
        self.mapping_file = Path(mapping_file)
        self.cn_to_jp = {}
        self.jp_to_cn = {}
        self.load_mapping()
    
    def load_mapping(self):
        """加载词汇对照表"""
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            self.cn_to_jp = json.load(f)
        
        # 构建反向索引（日文到中文）
        for cn_term, jp_terms in self.cn_to_jp.items():
            for jp_term in jp_terms:
                if jp_term not in self.jp_to_cn:
                    self.jp_to_cn[jp_term] = []
                self.jp_to_cn[jp_term].append(cn_term)
        
        print(f"已加载 {len(self.cn_to_jp)} 个中文词条")
        print(f"已加载 {len(self.jp_to_cn)} 个日文词条")
    
    def query_cn_to_jp(self, cn_term):
        """查询中文对应的日文"""
        if cn_term in self.cn_to_jp:
            return self.cn_to_jp[cn_term]
        return None
    
    def query_jp_to_cn(self, jp_term):
        """查询日文对应的中文"""
        if jp_term in self.jp_to_cn:
            return self.jp_to_cn[jp_term]
        return None
    
    def search_cn(self, keyword):
        """模糊搜索中文词汇"""
        results = {}
        for cn_term, jp_terms in self.cn_to_jp.items():
            if keyword in cn_term:
                results[cn_term] = jp_terms
        return results
    
    def search_jp(self, keyword):
        """模糊搜索日文词汇"""
        results = {}
        for jp_term, cn_terms in self.jp_to_cn.items():
            if keyword in jp_term:
                results[jp_term] = cn_terms
        return results
    
    def get_category_terms(self, category):
        """获取特定类别的词汇"""
        categories = {
            '颜色': ['红', '蓝', '黄', '绿', '黑', '紫', '白'],
            '形态': ['幼年期', '成长期', '成熟期', '完全体', '究极体', '应用兽'],
            '属性': ['疫苗', '数据', '病毒', '自由', '可变', '不明', '系统'],
            '卡牌类型': ['数码兽卡', '数码蛋卡', '驯兽师卡', '选项卡'],
            '稀有度': ['C', 'U', 'R', 'SR', 'SEC', 'P'],
        }
        
        if category not in categories:
            return None
        
        result = {}
        for term in categories[category]:
            if term in self.cn_to_jp:
                result[term] = self.cn_to_jp[term]
        
        return result
    
    def export_category(self, category, output_file):
        """导出特定类别的词汇到文件"""
        terms = self.get_category_terms(category)
        if not terms:
            print(f"未找到类别: {category}")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(terms, f, ensure_ascii=False, indent=2)
        
        print(f"已导出 {category} 类别的 {len(terms)} 个词条到 {output_file}")


def interactive_query():
    """交互式查询模式"""
    mapping_file = Path(__file__).parent / "term_mapping_cn_jp.json"
    
    if not mapping_file.exists():
        print("错误: 词汇对照表文件不存在，请先运行 extract_terms.py")
        return
    
    query = TermQuery(mapping_file)
    
    print("\n" + "=" * 60)
    print("数码宝贝卡牌中日文词汇查询工具")
    print("=" * 60)
    print("\n命令说明:")
    print("  cn <词汇>     - 查询中文对应的日文")
    print("  jp <词汇>     - 查询日文对应的中文")
    print("  search-cn <关键词> - 模糊搜索中文词汇")
    print("  search-jp <关键词> - 模糊搜索日文词汇")
    print("  category <类别> - 查看特定类别词汇（颜色/形态/属性/卡牌类型/稀有度）")
    print("  quit          - 退出程序")
    print()
    
    while True:
        try:
            user_input = input("请输入命令: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            
            if len(parts) < 2:
                print("错误: 请提供查询词汇或关键词")
                continue
            
            keyword = parts[1]
            
            if command == 'cn':
                result = query.query_cn_to_jp(keyword)
                if result:
                    print(f"\n中文: {keyword}")
                    print(f"日文: {', '.join(result)}\n")
                else:
                    print(f"\n未找到中文词汇: {keyword}\n")
            
            elif command == 'jp':
                result = query.query_jp_to_cn(keyword)
                if result:
                    print(f"\n日文: {keyword}")
                    print(f"中文: {', '.join(result)}\n")
                else:
                    print(f"\n未找到日文词汇: {keyword}\n")
            
            elif command == 'search-cn':
                results = query.search_cn(keyword)
                if results:
                    print(f"\n搜索结果 (包含 '{keyword}' 的中文词汇):")
                    for cn_term, jp_terms in sorted(results.items())[:20]:
                        print(f"  {cn_term} -> {', '.join(jp_terms)}")
                    if len(results) > 20:
                        print(f"  ... 还有 {len(results) - 20} 个结果")
                    print()
                else:
                    print(f"\n未找到包含 '{keyword}' 的中文词汇\n")
            
            elif command == 'search-jp':
                results = query.search_jp(keyword)
                if results:
                    print(f"\n搜索结果 (包含 '{keyword}' 的日文词汇):")
                    for jp_term, cn_terms in sorted(results.items())[:20]:
                        print(f"  {jp_term} -> {', '.join(cn_terms)}")
                    if len(results) > 20:
                        print(f"  ... 还有 {len(results) - 20} 个结果")
                    print()
                else:
                    print(f"\n未找到包含 '{keyword}' 的日文词汇\n")
            
            elif command == 'category':
                results = query.get_category_terms(keyword)
                if results:
                    print(f"\n{keyword} 类别词汇:")
                    for cn_term, jp_terms in sorted(results.items()):
                        print(f"  {cn_term} -> {', '.join(jp_terms)}")
                    print()
                else:
                    print(f"\n未找到类别: {keyword}")
                    print("可用类别: 颜色, 形态, 属性, 卡牌类型, 稀有度\n")
            
            else:
                print(f"\n未知命令: {command}\n")
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")


if __name__ == "__main__":
    interactive_query()
