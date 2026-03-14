"""
爬取中文官网 AD-01 卡包元数据
使用 requests + 正则表达式解析
"""

import sys
import logging
import time
import json
import re
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.error("requests 未安装")


def parse_card_data(html_content: str) -> list:
    """从 HTML 内容中解析卡牌数据"""
    cards_data = []
    
    # 查找所有卡牌编号模式：AD1-XXX
    card_pattern = r'AD1-(\d{3})'
    
    # 查找所有卡牌信息块
    # 格式：颜色 + 编号 + 稀有度 + LV + 类型 + 效果
    lines = html_content.split('\n')
    
    current_card = None
    card_numbers_seen = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 查找卡牌编号
        match = re.search(r'AD1-(\d{3})', line)
        if match:
            card_no = f"AD1-{match.group(1)}"
            
            # 避免重复
            if card_no in card_numbers_seen:
                continue
            card_numbers_seen.add(card_no)
            
            # 提取稀有度
            rarity_match = re.search(r'\b(R|SR|SP|SEC|U|C)\b', line)
            rarity = rarity_match.group(1) if rarity_match else ''
            
            # 提取等级
            level_match = re.search(r'LV(\d+)', line)
            level = level_match.group(1) if level_match else ''
            
            # 提取颜色
            color_match = re.search(r'(红 | 蓝 | 绿 | 黄 | 紫 | 黑 | 白)(\s*/\s*(红 | 蓝 | 绿 | 黄 | 紫 | 黑 | 白))*', line)
            color = color_match.group(0).replace(' ', '') if color_match else ''
            
            current_card = {
                'card_no': card_no,
                'card_name': card_no,  # 暂时用编号作为名称
                'pack_name': 'AD-01 数码兽世代',
                'rarity': rarity,
                'card_type': '数码兽卡' if '数码兽卡' in line else '驯兽师卡' if '驯兽师卡' in line else '',
                'color': color,
                'level': level,
                'card_url': f'https://app.digicamoe.cn/Cards/{card_no}',
                'image_url': '',
                'effect': '',
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            cards_data.append(current_card)
            logger.info(f"找到卡牌：{card_no} (稀有度：{rarity}, 等级：{level})")
    
    return cards_data


def scrape_ad01_cards():
    """爬取中文官网 AD-01 卡包数据"""
    logger.info("🎯 开始爬取 AD-01 卡包元数据（中文官网）")
    
    ad01_url = "https://app.digicamoe.cn/package/AD-01"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        logger.info(f"访问：{ad01_url}")
        response = requests.get(ad01_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        logger.info(f"页面大小：{len(html_content)} 字节")
        
        cards_data = parse_card_data(html_content)
        
        logger.info(f"爬取完成，共 {len(cards_data)} 张卡牌")
        return cards_data
        
    except Exception as e:
        logger.error(f"爬取失败：{e}")
        import traceback
        traceback.print_exc()
        return []


def save_cards_data(cards_data: list, output_path: Path):
    """保存卡牌数据"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取现有数据（如果有）
    existing_data = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            logger.info(f"读取到现有数据 {len(existing_data)} 条")
        except:
            pass
    
    # 合并数据（去重）
    existing_ids = {c.get('card_no') for c in existing_data}
    new_cards = [c for c in cards_data if c.get('card_no') not in existing_ids]
    
    merged_data = existing_data + new_cards
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"保存完成：{len(merged_data)} 条记录 (新增 {len(new_cards)} 条)")
    
    return len(new_cards)


def main():
    """主函数"""
    print("=" * 60)
    print("DTCG AD-01 卡包元数据爬取（requests 模式）")
    print("=" * 60)
    print()
    
    if not REQUESTS_AVAILABLE:
        print("❌ requests 未安装")
        print("   请运行：pip install requests")
        return 0
    
    # 爬取数据
    cards_data = scrape_ad01_cards()
    
    if not cards_data:
        print("\n⚠️ 未爬取到任何数据")
        return 0
    
    # 保存数据
    output_path = project_root / "digimon_card_data" / "digimon_cards_AD-01_cards.json"
    new_count = save_cards_data(cards_data, output_path)
    
    print()
    print("=" * 60)
    print("爬取完成")
    print("=" * 60)
    print(f"爬取卡牌：{len(cards_data)} 张")
    print(f"新增记录：{new_count} 条")
    print(f"输出文件：{output_path}")
    
    return len(cards_data)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
