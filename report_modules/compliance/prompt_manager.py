# -*- coding: utf-8 -*-
"""
Prompt配置管理器 - 统一管理所有prompt模板
"""

import json
from pathlib import Path
from typing import Dict, Any
from .templates_config import DEFAULT_TIPS_TEMPLATES, RISK_MAPPING


class PromptManager:
    """Prompt模板管理器"""
    
    def __init__(self, prompts_dir: str = None):
        """初始化prompt管理器
        
        Args:
            prompts_dir: prompt模板目录路径，默认为当前模块下的prompts目录
        """
        if prompts_dir is None:
            current_dir = Path(__file__).parent
            self.prompts_dir = current_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._prompt_cache = {}
    
    def load_prompt(self, prompt_name: str) -> str:
        """加载prompt模板
        
        Args:
            prompt_name: prompt文件名（不含扩展名）
            
        Returns:
            prompt模板字符串
        """
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        prompt_file = self.prompts_dir / f"{prompt_name}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt文件不存在: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        self._prompt_cache[prompt_name] = prompt
        return prompt
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """格式化prompt模板
        
        Args:
            prompt_name: prompt文件名
            **kwargs: 模板参数
            
        Returns:
            格式化后的prompt字符串
        """
        prompt_template = self.load_prompt(prompt_name)
        
        # 将字典类型的参数转换为JSON字符串
        formatted_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                formatted_kwargs[key] = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                formatted_kwargs[key] = str(value)
        
        try:
            return prompt_template.format(**formatted_kwargs)
        except KeyError as e:
            raise ValueError(f"Prompt模板 {prompt_name} 缺少参数: {e}")
    
    def get_default_tips_template(self) -> Dict[str, Dict[str, str]]:
        """获取默认的健康管理提示模板
        
        Returns:
            默认提示模板字典
        """
        return {
            "medication": {
                "state": DEFAULT_TIPS_TEMPLATES["medication"]["state_templates"]["low_adherence"],
                "advice": DEFAULT_TIPS_TEMPLATES["medication"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["medication"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["medication"]["risk"]
            },
            "monitoring": {
                "state": DEFAULT_TIPS_TEMPLATES["monitoring"]["state_templates"]["all_controlled"], 
                "advice": DEFAULT_TIPS_TEMPLATES["monitoring"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["monitoring"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["monitoring"]["risk_templates"]["no_issues"]
            },
            "exercise": {
                "state": DEFAULT_TIPS_TEMPLATES["exercise"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["exercise"]["advice"], 
                "doctor": DEFAULT_TIPS_TEMPLATES["exercise"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["exercise"]["risk"]
            },
            "diet": {
                "state": DEFAULT_TIPS_TEMPLATES["diet"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["diet"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["diet"]["doctor"], 
                "risk": DEFAULT_TIPS_TEMPLATES["diet"]["risk"]
            },
            "psychology": {
                "state": DEFAULT_TIPS_TEMPLATES["psychology"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["psychology"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["psychology"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["psychology"]["risk"]
            }
        }
    
    def generate_contextual_tips(self, monitoring: dict, status: dict, adherence: dict) -> Dict[str, Dict[str, str]]:
        """根据上下文生成个性化的提示模板
        
        Args:
            monitoring: 监测数据
            status: 状态数据
            adherence: 依从性数据
            
        Returns:
            个性化提示字典
        """
        # 动态生成风险评估
        risk_parts = []
        for key, description in RISK_MAPPING.items():
            if status.get(key) != "达标":
                risk_parts.append(description)
        
        # 计算依从性状态
        hist = (adherence or {}).get("history", [])
        total = len(hist)
        compliant = sum(1 for a in hist if a.get("overall_status") == "完全遵从")
        rate = (compliant/total*100) if total else 0.0
        
        # 选择依从性状态模板
        adh_state = (DEFAULT_TIPS_TEMPLATES["medication"]["state_templates"]["low_adherence"] 
                    if rate < 60 else 
                    DEFAULT_TIPS_TEMPLATES["medication"]["state_templates"]["good_adherence"])
        
        # 选择监测状态模板
        monitoring_state = (DEFAULT_TIPS_TEMPLATES["monitoring"]["state_templates"]["has_uncontrolled"] 
                           if risk_parts else 
                           DEFAULT_TIPS_TEMPLATES["monitoring"]["state_templates"]["all_controlled"])
        
        # 选择风险提示模板
        risk_text = (DEFAULT_TIPS_TEMPLATES["monitoring"]["risk_templates"]["with_issues"].format(
                        risk_items="、".join(risk_parts))
                    if risk_parts else 
                    DEFAULT_TIPS_TEMPLATES["monitoring"]["risk_templates"]["no_issues"])
        
        return {
            "medication": {
                "state": adh_state,
                "advice": DEFAULT_TIPS_TEMPLATES["medication"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["medication"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["medication"]["risk"]
            },
            "monitoring": {
                "state": monitoring_state,
                "advice": DEFAULT_TIPS_TEMPLATES["monitoring"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["monitoring"]["doctor"],
                "risk": risk_text
            },
            "exercise": {
                "state": DEFAULT_TIPS_TEMPLATES["exercise"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["exercise"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["exercise"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["exercise"]["risk"]
            },
            "diet": {
                "state": DEFAULT_TIPS_TEMPLATES["diet"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["diet"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["diet"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["diet"]["risk"]
            },
            "psychology": {
                "state": DEFAULT_TIPS_TEMPLATES["psychology"]["state"],
                "advice": DEFAULT_TIPS_TEMPLATES["psychology"]["advice"],
                "doctor": DEFAULT_TIPS_TEMPLATES["psychology"]["doctor"],
                "risk": DEFAULT_TIPS_TEMPLATES["psychology"]["risk"]
            }
        }
    
    def list_available_prompts(self) -> list:
        """列出所有可用的prompt文件
        
        Returns:
            prompt文件名列表（不含扩展名）
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = list(self.prompts_dir.glob("*.md"))
        return [f.stem for f in prompt_files]


# 创建全局prompt管理器实例
prompt_manager = PromptManager()