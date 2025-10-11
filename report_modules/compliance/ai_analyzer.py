# -*- coding: utf-8 -*-
"""
AI分析器 - 调用LLM生成分析报告

将raise部分的中文翻译为英文
"""

# from repair_json import repair_json
from json_repair import repair_json
import json
# from . import config
from report_modules.common import config
from .prompt_manager import prompt_manager
import re


# -------------------- Utils --------------------
def extract_json_from_llm_output(text: str):
    """从 LLM 输出中提取 JSON（支持 ```json ... ``` 块；失败返回 None）"""
    try:
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, text)
        if match:
            json_str = match.group(1)
            return json.dumps(repair_json(json_str, ensure_ascii=False, return_objects=True), ensure_ascii=False, indent=2)
        return json.dumps(repair_json(text, ensure_ascii=False, return_objects=True), ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"JSON提取失败: {str(e)}")
        return None



def generate_ai_analysis(monitoring: dict, adherence: dict, lifestyle: dict = None, patient_info: dict = None) -> dict:
    """
    调用 Qwen 模型生成完整的 AI 分析（健康管理提示 + 综合分析）
    """
    # 构建完整的患者上下文
    lifestyle = lifestyle or {}
    patient_info = patient_info or {}
    
    # 使用外部prompt模板
    try:
        prompt = prompt_manager.format_prompt(
            "ai_analysis_prompt",
            patient_info=patient_info,
            monitoring=monitoring,
            adherence=adherence,
            lifestyle=lifestyle
        )
    except Exception as e:
        print(f"Warning: Failed to load prompt template: {e}")
        # 降级到简化的默认prompt
        prompt = f"""
        基于以下患者数据生成健康管理分析：
        患者信息：{json.dumps(patient_info, ensure_ascii=False)}
        监测数据：{json.dumps(monitoring, ensure_ascii=False)}
        依从性：{json.dumps(adherence, ensure_ascii=False)}
        生活方式：{json.dumps(lifestyle, ensure_ascii=False)}
        
        请按JSON格式输出包含tips、summary、risk_assessment、recommendations的分析结果。
        """

    try:
        resp = config.client.chat.completions.create(
            model="qwen3-4b",
            # model = "/home/jyu7/models/Qwen3-32B-AWQ",
            messages=[
                {"role": "system", "content": "你是一名临床医生助手，输出简洁清晰的中文段落。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            extra_body={"enable_thinking": False}
        )
        # import ipdb;ipdb.set_trace()

        text = resp.choices[0].message.content.strip()
        # import ipdb; ipdb.set_trace()
        data = extract_json_from_llm_output(text)
        data = json.loads(data)
        
        # 返回完整的分析结果，包括tips和综合分析
        return {
            "tips": data.get("tips", {
                "medication": {"state": "（LLM未返回）", "advice": "（LLM未返回）", "doctor": "（LLM未返回）", "risk": "（LLM未返回）"},
                "monitoring": {"state": "（LLM未返回）", "advice": "（LLM未返回）", "doctor": "（LLM未返回）", "risk": "（LLM未返回）"},
                "exercise": {"state": "（LLM未返回）", "advice": "（LLM未返回）", "doctor": "（LLM未返回）", "risk": "（LLM未返回）"},
                "diet": {"state": "（LLM未返回）", "advice": "（LLM未返回）", "doctor": "（LLM未返回）", "risk": "（LLM未返回）"},
                "psychology": {"state": "（LLM未返回）", "advice": "（LLM未返回）", "doctor": "（LLM未返回）", "risk": "（LLM未返回）"}
            }),
            "summary": data.get("summary", "（LLM未返回）"),
            "risk_assessment": data.get("risk_assessment", "（LLM未返回）"),
            "recommendations": data.get("recommendations", "（LLM未返回）")
        }
    except Exception as e:
        # print(f"AI分析生成失败: {e}")
        print(f"AI analysis generation failed. {e}")

        # 使用默认模板作为fallback
        default_tips = prompt_manager.get_default_tips_template()
        
        return {
            "tips": default_tips,
            "summary": "（系统生成）整体控制尚可，建议继续监测。",
            "risk_assessment": "（系统生成）饮食与用药依从性是主要风险点。",
            "recommendations": "（系统生成）建议加强用药管理，改善生活方式，定期复查。"
        }
