import pdfplumber
from pypdf import PdfReader
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import json


def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 提取文本，优先使用 pdfplumber（对中文支持更好）"""
    text_parts = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception:
        # 回退到 pypdf
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def format_terminology_json(data: Dict[str, Any]) -> str:
    """
    将术语对照表 JSON 转换为适合嵌入的文本格式
    支持格式：
    1. 简单键值对: {"日文": "中文", ...}
    2. 分类结构: {"category": {"日文": "中文", ...}, ...}
    """
    lines = []
    
    for key, value in data.items():
        if isinstance(value, dict):
            # 分类结构
            lines.append(f"【{key}】术语对照：")
            for orig, trans in value.items():
                if trans:  # 跳过空翻译
                    lines.append(f"  {orig} → {trans}")
            lines.append("")
        elif isinstance(value, str):
            # 简单键值对
            if value:
                lines.append(f"{key} → {value}")
        elif isinstance(value, list):
            # 列表格式
            lines.append(f"【{key}】：")
            for item in value:
                if isinstance(item, dict):
                    # 列表中的对象
                    item_parts = [f"{k}: {v}" for k, v in item.items() if v]
                    lines.append(f"  - {', '.join(item_parts)}")
                else:
                    lines.append(f"  - {item}")
            lines.append("")
    
    return "\n".join(lines)


def format_card_data(card: Dict[str, Any]) -> str:
    """
    将单张卡牌数据转换为适合嵌入的文本格式
    """
    lines = []
    
    # 基本信息
    card_no = card.get("card_no", "")
    card_name = card.get("card_name", "")
    card_type = card.get("card_type", "")
    
    lines.append(f"【{card_no}】{card_name}")
    lines.append(f"卡牌类型: {card_type}")
    
    # 颜色
    color = card.get("color", "")
    color2 = card.get("color2")
    if color:
        color_str = f"{color}" + (f"/{color2}" if color2 and color2 != color else "")
        lines.append(f"颜色: {color_str}")
    
    # 等级和费用
    level = card.get("level")
    cost = card.get("cost")
    dp = card.get("dp")
    if level:
        lines.append(f"等级: Lv.{level}")
    if cost is not None:
        lines.append(f"费用: {cost}")
    if dp:
        lines.append(f"DP: {dp}")
    
    # 进化费用
    digivolve_cost1 = card.get("digivolve_cost1")
    digivolve_color1 = card.get("digivolve_color1")
    if digivolve_cost1 is not None and digivolve_color1:
        lines.append(f"进化费用: {digivolve_cost1} (从{digivolve_color1})")
    
    # 形态和属性
    form = card.get("form")
    attribute = card.get("attribute")
    digimon_type = card.get("digimon_type")
    if form:
        lines.append(f"形态: {form}")
    if attribute:
        lines.append(f"属性: {attribute}")
    if digimon_type:
        lines.append(f"类型: {digimon_type}")
    
    # 效果
    effect = card.get("effect")
    inherited_effect = card.get("inherited_effect")
    security_effect = card.get("security_effect")
    if effect:
        lines.append(f"效果: {effect}")
    if inherited_effect and inherited_effect != effect:
        lines.append(f"进化源效果: {inherited_effect}")
    if security_effect:
        lines.append(f"安防效果: {security_effect}")
    
    # 稀有度和卡包
    rarity = card.get("rarity")
    pack_name = card.get("pack_name")
    if rarity:
        lines.append(f"稀有度: {rarity}")
    if pack_name:
        lines.append(f"卡包: {pack_name}")
    
    return "\n".join(lines)


def format_card_list_json(cards: List[Dict[str, Any]]) -> str:
    """
    将卡牌列表 JSON 转换为适合嵌入的文本格式
    """
    card_texts = []
    for card in cards:
        card_text = format_card_data(card)
        card_texts.append(card_text)
    
    return "\n\n---\n\n".join(card_texts)


def extract_text_from_json(content: bytes) -> str:
    """
    从 JSON 文件提取文本，智能处理术语对照表和卡牌数据格式
    """
    text = content.decode("utf-8")
    try:
        data = json.loads(text)
        
        if isinstance(data, list):
            # 检查是否是卡牌数据格式
            if data and isinstance(data[0], dict) and "card_no" in data[0]:
                return format_card_list_json(data)
            # 处理普通数组格式
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    item_text = format_terminology_json(item)
                    lines.append(f"--- 条目 {i+1} ---\n{item_text}")
                else:
                    lines.append(str(item))
            return "\n\n".join(lines)
        elif isinstance(data, dict):
            return format_terminology_json(data)
        else:
            return str(data)
    except json.JSONDecodeError:
        # JSON 解析失败，返回原始文本
        return text


def extract_text_from_bytes(content: bytes, filename: str) -> str:
    """从上传的文件字节流提取文本"""
    import tempfile
    import os
    
    suffix = Path(filename).suffix.lower()
    
    # JSON 文件特殊处理
    if suffix == ".json":
        return extract_text_from_json(content)
    
    # PDF 文件
    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            return extract_text_from_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    # TXT 和其他文本文件
    return content.decode("utf-8")
