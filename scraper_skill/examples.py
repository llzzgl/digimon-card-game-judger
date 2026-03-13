"""
Scraper Skill 使用示例
演示如何使用爬虫技能包爬取卡牌和 QA 数据
"""
import sys
import logging
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scraper_skill"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_jp_scraper():
    """示例 1: 爬取日文卡牌"""
    logger.info("\n" + "="*60)
    logger.info("示例 1: 爬取日文卡牌")
    logger.info("="*60)
    
    from src.utils.jp_scraper import JapaneseCardScraper
    
    # 配置
    config = {
        "headless": True,
        "output_dir": str(PROJECT_ROOT / "scraper_skill" / "data" / "output"),
    }
    
    scraper = JapaneseCardScraper(config)
    
    try:
        # 爬取指定卡包（示例：BT-24）
        # 注意：实际使用时需要正确的 category ID
        logger.info("准备爬取日文卡牌...")
        logger.info("提示：此示例仅演示 API 使用，不实际执行爬取")
        
        # 实际爬取代码（取消注释以执行）:
        # pack, cards = scraper.scrape_pack("503035")
        # scraper.save_to_json(cards)
        
        logger.info("✓ 示例代码完成")
        
    except Exception as e:
        logger.error(f"✗ 爬取失败：{e}")
    finally:
        scraper.close()


def example_cn_scraper():
    """示例 2: 爬取中文卡牌"""
    logger.info("\n" + "="*60)
    logger.info("示例 2: 爬取中文卡牌")
    logger.info("="*60)
    
    from src.utils.cn_scraper import ChineseCardScraper
    
    # 配置
    config = {
        "headless": True,
        "output_path": str(PROJECT_ROOT / "scraper_skill" / "data" / "output" / "digimon_cards_cn.json"),
    }
    
    scraper = ChineseCardScraper(config)
    
    try:
        logger.info("准备爬取中文卡牌...")
        logger.info("提示：此示例仅演示 API 使用，不实际执行爬取")
        
        # 实际爬取代码（取消注释以执行）:
        # new_count = scraper.scrape_all_cards(max_pages=5)
        
        logger.info("✓ 示例代码完成")
        
    except Exception as e:
        logger.error(f"✗ 爬取失败：{e}")
    finally:
        scraper.close()


def example_digimon_scraper():
    """示例 3: 爬取数码兽名称"""
    logger.info("\n" + "="*60)
    logger.info("示例 3: 爬取数码兽名称")
    logger.info("="*60)
    
    from src.utils.digimon_scraper import DigimonNameScraper
    
    # 配置
    config = {
        "output_path": str(PROJECT_ROOT / "scraper_skill" / "data" / "output" / "digimon_name_mapping.json"),
        "delay": 0.2,
    }
    
    scraper = DigimonNameScraper(config)
    
    try:
        logger.info("准备爬取数码兽名称...")
        logger.info("提示：此示例仅演示 API 使用，不实际执行爬取")
        
        # 实际爬取代码（取消注释以执行）:
        # mapping = scraper.scrape_all()
        # scraper.save_mapping()
        
        # 查询示例
        # chinese_name = scraper.get_chinese_name("アグモン")
        # logger.info(f"アグモン -> {chinese_name}")
        
        logger.info("✓ 示例代码完成")
        
    except Exception as e:
        logger.error(f"✗ 爬取失败：{e}")


def example_qa_scraper():
    """示例 4: 爬取 QA 裁定"""
    logger.info("\n" + "="*60)
    logger.info("示例 4: 爬取 QA 裁定")
    logger.info("="*60)
    
    from src.qa_scraper import QAScraper
    
    # 配置
    config = {
        "headless": True,
        "output_path": str(PROJECT_ROOT / "scraper_skill" / "data" / "output" / "rulings.json"),
    }
    
    scraper = QAScraper(config)
    
    try:
        logger.info("准备爬取 QA 裁定...")
        logger.info("提示：此示例仅演示 API 使用，不实际执行爬取")
        
        # 实际爬取代码（取消注释以执行）:
        # new_count = scraper.scrape_japanese_official()
        
        # 搜索示例
        # results = scraper.search_qa("安防")
        # logger.info(f"找到 {len(results)} 条相关 QA")
        
        logger.info("✓ 示例代码完成")
        
    except Exception as e:
        logger.error(f"✗ 爬取失败：{e}")
    finally:
        scraper.close()


def example_card_scraper_unified():
    """示例 5: 使用统一接口"""
    logger.info("\n" + "="*60)
    logger.info("示例 5: 使用统一接口爬取卡牌")
    logger.info("="*60)
    
    from src.card_scraper import CardScraper
    
    # 配置
    config = {
        "output_path": str(PROJECT_ROOT / "scraper_skill" / "data" / "output" / "cards.json"),
    }
    
    scraper = CardScraper(config)
    
    try:
        logger.info("准备使用统一接口爬取卡牌...")
        logger.info("提示：此示例仅演示 API 使用，不实际执行爬取")
        
        # 实际爬取代码（取消注释以执行）:
        # jp_cards = scraper.scrape_japanese(category_ids=["503035"])
        # cn_new = scraper.scrape_chinese(max_pages=5)
        
        # 合并数据
        # scraper.merge_cards(
        #     jp_path=Path("output/cards_jp.json"),
        #     cn_path=Path("digimon_cards_cn.json")
        # )
        
        # 保存
        # scraper.save_merged()
        
        # 验证
        # report = scraper.validate_cards()
        # logger.info(f"验证结果：{report['valid']} 有效 / {report['invalid']} 无效")
        
        logger.info("✓ 示例代码完成")
        
    except Exception as e:
        logger.error(f"✗ 爬取失败：{e}")


def example_load_existing_data():
    """示例 6: 加载现有数据"""
    logger.info("\n" + "="*60)
    logger.info("示例 6: 加载现有数据")
    logger.info("="*60)
    
    import json
    
    # 加载卡牌数据
    cards_path = PROJECT_ROOT / "skill" / "data" / "cards.json"
    if cards_path.exists():
        with open(cards_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        logger.info(f"✓ 加载卡牌数据：{len(cards)} 张")
        
        # 查询示例
        for card in cards[:3]:  # 显示前 3 张
            logger.info(f"  - {card.get('card_no')}: {card.get('card_name', '')}")
    else:
        logger.warning(f"⚠ 卡牌数据文件不存在：{cards_path}")
        logger.info(f"   提示：请从正确的项目目录运行此脚本")
    
    # 加载 QA 数据
    rulings_path = PROJECT_ROOT / "skill" / "data" / "rulings.json"
    if rulings_path.exists():
        with open(rulings_path, 'r', encoding='utf-8') as f:
            rulings = json.load(f)
        logger.info(f"✓ 加载 QA 数据：{len(rulings)} 条")
    else:
        logger.warning(f"⚠ QA 数据文件不存在：{rulings_path}")
        logger.info(f"   提示：请从正确的项目目录运行此脚本")


def main():
    """运行所有示例"""
    logger.info("\n" + "="*60)
    logger.info("DTCG Scraper Skill 使用示例")
    logger.info("="*60)
    
    examples = [
        ("爬取日文卡牌", example_jp_scraper),
        ("爬取中文卡牌", example_cn_scraper),
        ("爬取数码兽名称", example_digimon_scraper),
        ("爬取 QA 裁定", example_qa_scraper),
        ("统一接口", example_card_scraper_unified),
        ("加载现有数据", example_load_existing_data),
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            logger.error(f"示例 {name} 异常：{e}")
    
    logger.info("\n" + "="*60)
    logger.info("所有示例运行完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
