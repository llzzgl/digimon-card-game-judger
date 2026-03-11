"""
裁判配置加载器
从 .judge/ 目录加载配置文件
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class JudgeConfigLoader:
    """加载和管理 .judge/ 目录中的配置文件"""
    
    def __init__(self, config_dir: str = ".judge"):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置目录路径，默认为 .judge
        """
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, str] = {}
        
        # 配置文件列表
        self.config_files = {
            'identity': 'IDENTITY.md',
            'rules': 'RULES.md',
            'memory': 'MEMORY.md',
            'feedback': 'FEEDBACK.md',
            'config': 'CONFIG.md',
        }
        
    def load_all(self) -> Dict[str, str]:
        """
        加载所有配置文件
        
        Returns:
            包含所有配置内容的字典
        """
        for key, filename in self.config_files.items():
            self.configs[key] = self.load_config(filename)
        
        logger.info(f"已加载 {len(self.configs)} 个配置文件")
        return self.configs
    
    def load_config(self, filename: str) -> str:
        """
        加载单个配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置文件内容
        """
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"配置文件不存在: {filepath}")
            return ""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"已加载配置文件: {filename}")
            return content
        except Exception as e:
            logger.error(f"加载配置文件失败 {filename}: {e}")
            return ""
    
    def get_identity(self) -> str:
        """获取裁判身份定义"""
        return self.configs.get('identity', '')
    
    def get_rules(self) -> str:
        """获取裁判工作规则"""
        return self.configs.get('rules', '')
    
    def get_memory_guide(self) -> str:
        """获取记忆系统说明"""
        return self.configs.get('memory', '')
    
    def get_feedback(self) -> str:
        """获取用户反馈记录"""
        return self.configs.get('feedback', '')
    
    def get_system_prompt(self) -> str:
        """
        生成系统提示词
        结合身份定义和工作规则
        
        Returns:
            完整的系统提示词
        """
        identity = self.get_identity()
        rules = self.get_rules()
        
        # 提取关键部分
        system_prompt = f"""# 你的身份

{self._extract_core_identity(identity)}

# 工作规则

{self._extract_core_rules(rules)}

# 重要提醒

- 每次回答都要引用具体的规则条款或卡牌编号
- 不确定时明确说明，不要猜测
- 优先使用已验证的记忆
- 从用户反馈中持续学习
"""
        return system_prompt
    
    def _extract_core_identity(self, identity_content: str) -> str:
        """提取身份定义的核心部分"""
        if not identity_content:
            return "数码宝贝卡牌对战的顶级裁判"
        
        # 简单提取，可以根据需要优化
        lines = identity_content.split('\n')
        core_lines = []
        in_core_section = False
        
        for line in lines:
            if '## 核心身份' in line:
                in_core_section = True
                continue
            elif line.startswith('## ') and in_core_section:
                break
            elif in_core_section and line.strip():
                core_lines.append(line)
        
        return '\n'.join(core_lines) if core_lines else identity_content[:500]
    
    def _extract_core_rules(self, rules_content: str) -> str:
        """提取工作规则的核心部分"""
        if not rules_content:
            return "遵循综合规则、卡牌效果、官方QA的优先级"
        
        # 简单提取，可以根据需要优化
        lines = rules_content.split('\n')
        core_lines = []
        in_core_section = False
        
        for line in lines:
            if '## 裁定原则' in line:
                in_core_section = True
                continue
            elif line.startswith('## ') and in_core_section:
                break
            elif in_core_section and line.strip():
                core_lines.append(line)
        
        return '\n'.join(core_lines) if core_lines else rules_content[:500]
    
    def add_feedback(self, feedback_entry: str) -> bool:
        """
        添加用户反馈到 FEEDBACK.md
        
        Args:
            feedback_entry: 反馈条目（Markdown格式）
            
        Returns:
            是否添加成功
        """
        filepath = self.config_dir / 'FEEDBACK.md'
        
        if not filepath.exists():
            logger.error(f"反馈文件不存在: {filepath}")
            return False
        
        try:
            # 读取现有内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 找到反馈记录部分
            marker = "## 反馈记录"
            if marker in content:
                # 在反馈记录部分后插入新反馈
                parts = content.split(marker)
                # 跳过格式说明，找到第一个 "---"
                after_marker = parts[1]
                first_separator = after_marker.find("---")
                if first_separator != -1:
                    # 在第一个分隔符后插入
                    second_separator = after_marker.find("---", first_separator + 3)
                    if second_separator != -1:
                        insert_pos = second_separator + 3
                        new_content = (
                            parts[0] + marker + 
                            after_marker[:insert_pos] + 
                            "\n\n" + feedback_entry + "\n" +
                            after_marker[insert_pos:]
                        )
                    else:
                        # 没有找到第二个分隔符，直接追加
                        new_content = content + "\n\n" + feedback_entry + "\n"
                else:
                    # 没有找到分隔符，直接追加
                    new_content = content + "\n\n" + feedback_entry + "\n"
            else:
                # 没有找到标记，直接追加
                new_content = content + "\n\n" + feedback_entry + "\n"
            
            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("已添加用户反馈")
            return True
            
        except Exception as e:
            logger.error(f"添加反馈失败: {e}")
            return False
    
    def update_feedback_stats(self) -> bool:
        """
        更新反馈统计信息
        
        Returns:
            是否更新成功
        """
        filepath = self.config_dir / 'FEEDBACK.md'
        
        if not filepath.exists():
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计各类反馈
            stats = {
                '裁定纠正': content.count('- 裁定纠正'),
                '表达改进': content.count('- 表达改进'),
                '功能建议': content.count('- 功能建议'),
                '规则更新': content.count('- 规则更新'),
            }
            
            status_stats = {
                '待处理': content.count('**状态：** 待处理'),
                '已改进': content.count('**状态：** 已改进'),
                '已验证': content.count('**状态：** 已验证'),
            }
            
            # 更新统计部分
            stats_section = f"""### 按类型统计
- 裁定纠正：{stats['裁定纠正']} 条
- 表达改进：{stats['表达改进']} 条
- 功能建议：{stats['功能建议']} 条
- 规则更新：{stats['规则更新']} 条

### 按状态统计
- 待处理：{status_stats['待处理']} 条
- 已改进：{status_stats['已改进']} 条
- 已验证：{status_stats['已验证']} 条"""
            
            # 替换统计部分
            marker = "## 反馈统计"
            if marker in content:
                parts = content.split(marker)
                next_section = parts[1].find("\n## ")
                if next_section != -1:
                    new_content = (
                        parts[0] + marker + "\n\n" + 
                        stats_section + "\n" +
                        parts[1][next_section:]
                    )
                else:
                    new_content = parts[0] + marker + "\n\n" + stats_section
                
                # 写回文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("已更新反馈统计")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新统计失败: {e}")
            return False


# 全局配置加载器实例
_config_loader: Optional[JudgeConfigLoader] = None


def get_config_loader() -> JudgeConfigLoader:
    """
    获取全局配置加载器实例
    
    Returns:
        配置加载器实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = JudgeConfigLoader()
        _config_loader.load_all()
    return _config_loader


def get_system_prompt() -> str:
    """
    获取系统提示词
    
    Returns:
        系统提示词
    """
    loader = get_config_loader()
    return loader.get_system_prompt()


def add_user_feedback(
    question: str,
    current_answer: str,
    user_feedback: str,
    feedback_type: str = "裁定纠正",
    improvement: str = "",
    status: str = "待处理"
) -> bool:
    """
    添加用户反馈
    
    Args:
        question: 用户的问题
        current_answer: 当前的回答
        user_feedback: 用户的反馈
        feedback_type: 反馈类型
        improvement: 改进措施
        status: 状态
        
    Returns:
        是否添加成功
    """
    from datetime import datetime
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    feedback_entry = f"""### {date_str} - {feedback_type}

**问题：** {question}

**当前处理：** {current_answer}

**用户反馈：** {user_feedback}

**改进措施：** {improvement if improvement else "待确定"}

**状态：** {status}

---"""
    
    loader = get_config_loader()
    success = loader.add_feedback(feedback_entry)
    
    if success:
        # 更新统计
        loader.update_feedback_stats()
    
    return success


if __name__ == "__main__":
    # 测试配置加载
    logging.basicConfig(level=logging.INFO)
    
    loader = JudgeConfigLoader()
    configs = loader.load_all()
    
    print("=== 配置加载测试 ===\n")
    
    print("1. 身份定义（前200字符）:")
    print(loader.get_identity()[:200])
    print("\n")
    
    print("2. 工作规则（前200字符）:")
    print(loader.get_rules()[:200])
    print("\n")
    
    print("3. 系统提示词（前300字符）:")
    print(loader.get_system_prompt()[:300])
    print("\n")
    
    print("=== 测试完成 ===")
