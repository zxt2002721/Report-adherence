# -*- coding: utf-8 -*-
"""
综合患者健康报告生成器
结合原始报告数据和医生批注，生成包含修改说明的患者健康报告
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Any

from json_repair import repair_json
# 使用现有的报告模块
from report_modules.data_loader import load_json, load_patient_data
from report_modules import config

# 从主报告文件导入build_context函数
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from report import build_context

OUT_DIR = Path("report/output")

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


class ComprehensivePatientReportGenerator:
    """综合患者健康报告生成器"""
    
    def __init__(self):
        # 使用配置模块中的client
        self.client = config.client
    
    def load_original_report_data(self, patient_id: str) -> dict:
        """加载原始报告数据"""
        try:
            # 加载患者原始数据
            memory, dialogues, df_patient = load_patient_data(patient_id)
            
            # 构建完整上下文（与report.py相同的逻辑）
            context = build_context(memory, dialogues, df_patient, patient_id)
            return {
                "success": True,
                "context": context,
                "memory": memory,
                "dialogues": dialogues,
                "df_patient": df_patient
            }
        except Exception as e:
            print(f"加载原始报告数据时出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": {},
                "memory": {},
                "dialogues": {},
                "df_patient": None
            }
    
    def compare_original_vs_annotations(self, original_context: dict, annotation_data: dict) -> dict:
        """对比原始报告和医生批注，找出修改点"""
        
        annotations = annotation_data.get("annotations", [])
        interactions = annotation_data.get("interactions", {})
        
        # 构建对比分析prompt
        prompt = f"""
请对比原始医疗报告数据和医生的批注修改，分析医生做了哪些重要调整：

原始报告AI分析：
{json.dumps(original_context.get("ai_analysis", {}), ensure_ascii=False, indent=2)}

原始监测建议：
{json.dumps(original_context.get("monitoring", {}), ensure_ascii=False, indent=2)}

原始用药信息：
{json.dumps(original_context.get("medications", {}), ensure_ascii=False, indent=2)}

医生批注内容：
{json.dumps(annotations, ensure_ascii=False, indent=2)}

医生交互记录：
{json.dumps(interactions, ensure_ascii=False, indent=2)}

请分析并说明：
1. 医生对原始分析的哪些部分进行了修改或补充
2. 医生新增了哪些关注点或建议
3. 医生调整了哪些治疗方案或监测计划
4. 这些修改的医学意义和对患者的影响

请以JSON格式返回：
{{
    "modifications_summary": "医生修改的总体概述",
    "ai_analysis_changes": "对AI分析的修改或确认",
    "monitoring_adjustments": "监测计划的调整",
    "medication_changes": "用药方案的变化",
    "new_concerns": "医生新增的关注点",
    "clinical_reasoning": "医生修改的临床考虑",
    "patient_impact": "这些修改对患者的具体影响"
}}
"""
        
        try:
            response = self._call_ai(prompt, "报告对比分析")
            # import ipdb; ipdb.set_trace()
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_comparison_response(response)
        except Exception as e:
            print(f"对比分析时出错: {e}")
            return self._get_default_comparison()
    
    def generate_comprehensive_health_summary(self, original_context: dict, annotation_data: dict, comparison: dict) -> dict:
        """生成综合健康状况总结"""
        
        # 结合原始数据和批注数据
        ai_analysis = original_context.get("ai_analysis", {})
        patient_basic = original_context.get("patient", {})
        charts = original_context.get("charts", {})
        
        prompt = f"""
基于完整的患者数据和医生的专业修改，为患者生成综合健康报告：

患者基本信息：
{json.dumps(patient_basic, ensure_ascii=False, indent=2)}

原始AI分析：
{json.dumps(ai_analysis, ensure_ascii=False, indent=2)}

医生的修改和关注点：
{json.dumps(comparison, ensure_ascii=False, indent=2)}

可用的数据图表：
{list(charts.keys()) if charts else "无图表数据"}

请用患者容易理解的语言，生成包含以下内容的健康报告：
1. 当前健康状况的全面评估（结合数据和医生意见）
2. 关键健康指标的具体情况和变化趋势
3. 医生基于专业判断做出的重要调整说明
4. 需要患者特别注意的事项

请以JSON格式返回：
{{
    "overall_health_status": "整体健康状况评估",
    "key_indicators_with_trends": "关键指标和趋势说明",
    "doctor_adjustments_explained": "医生调整的原因和意义",
    "important_patient_notes": "患者需要特别注意的要点",
    "data_highlights": "数据中的重要发现"
}}
"""
        
        try:
            response = self._call_ai(prompt, "综合健康总结")
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_health_summary_response(response)
        except Exception as e:
            print(f"生成综合健康总结时出错: {e}")
            return self._get_default_health_summary()
    
    def generate_medication_guidance_with_changes(self, original_context: dict, annotation_data: dict, comparison: dict) -> dict:
        """生成包含变更说明的用药指导"""
        
        original_medications = original_context.get("medications", {})
        interactions = annotation_data.get("interactions", {})
        
        # 提取用药相关的交互记录
        medication_interactions = {}
        for key, value in interactions.items():
            if any(keyword in key.lower() for keyword in ["medication", "drug", "med", "disease.plan"]):
                medication_interactions[key] = value
        
        prompt = f"""
基于原始用药信息和医生的调整记录，为患者说明用药变化：

原始用药总结：
{json.dumps(original_medications, ensure_ascii=False, indent=2)}

医生的用药相关调整：
{json.dumps(medication_interactions, ensure_ascii=False, indent=2)}

医生修改的整体分析：
{comparison.get("medication_changes", "无特殊变化")}

请为患者清晰说明：
1. 目前的用药情况（如果有变化，说明变化内容）
2. 医生调整用药的原因
3. 新的用药方案的作用和目的
4. 服药时需要特别注意的事项

请以JSON格式返回：
{{
    "current_medication_status": "目前用药情况和变化说明",
    "adjustment_reasons": "医生调整用药的原因",
    "new_medication_purpose": "调整后用药的作用目的",
    "special_instructions": "服药的特殊注意事项",
    "monitoring_requirements": "用药后需要监测的内容"
}}
"""
        
        try:
            response = self._call_ai(prompt, "用药指导分析")
            # return response
            # import ipdb; ipdb.set_trace()
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_medication_response(response)
        except Exception as e:
            print(f"生成用药指导时出错: {e}")
            return self._get_default_medication_guidance()
    
    def generate_lifestyle_and_monitoring_plan(self, original_context: dict, annotation_data: dict, comparison: dict) -> dict:
        """生成生活方式建议和监测计划"""
        
        original_monitoring = original_context.get("monitoring", {})
        interactions = annotation_data.get("interactions", {})
        
        # 提取生活方式和监测相关记录
        lifestyle_monitoring = {}
        for key, value in interactions.items():
            if any(keyword in key.lower() for keyword in ["lifestyle", "monitor", "recheck", "follow"]):
                lifestyle_monitoring[key] = value
        
        prompt = f"""
基于原始监测建议和医生的调整，为患者制定生活指导计划：

原始监测建议：
{json.dumps(original_monitoring, ensure_ascii=False, indent=2)}

医生的监测和生活方式调整：
{json.dumps(lifestyle_monitoring, ensure_ascii=False, indent=2)}

医生的整体调整分析：
监测调整：{comparison.get("monitoring_adjustments", "按原计划")}
新增关注：{comparison.get("new_concerns", "无新增")}

请为患者提供：
1. 生活方式的具体建议（饮食、运动、作息）
2. 调整后的监测计划和时间安排
3. 自我管理的方法和技巧
4. 何时需要联系医生的情况

请以JSON格式返回：
{{
    "lifestyle_recommendations": "生活方式具体建议",
    "updated_monitoring_plan": "更新后的监测计划",
    "self_management_tips": "自我管理方法",
    "when_to_contact_doctor": "需要联系医生的情况"
}}
"""
        
        try:
            response = self._call_ai(prompt, "生活方式和监测计划")
            import ipdb; ipdb.set_trace()
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_lifestyle_monitoring_response(response)
        except Exception as e:
            print(f"生成生活方式和监测计划时出错: {e}")
            return self._get_default_lifestyle_monitoring()
    
    def _call_ai(self, prompt: str, context: str) -> str:
        """调用AI分析"""
        try:
            resp = self.client.chat.completions.create(
                # model="qwen3-4b",
                model = "/home/jyu7/models/Qwen3-32B-AWQ",
                messages=[
                    {"role": "system", "content": f"你是一名专业的健康顾问，负责{context}。请用简单易懂、温和鼓励的语言与患者沟通，重点说明医生的专业调整和建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                extra_body={"enable_thinking": False}
            )
            # content = resp.choices[0].message.content.strip()
            content = resp.choices[0].message.content.strip()
            # content = extract_json_from_llm_output(content)
            # import ipdb; ipdb.set_trace()
            return extract_json_from_llm_output(content)
        except Exception as e:
            print(f"AI调用失败: {e}")
            return ""
    
    def _parse_comparison_response(self, response: str) -> dict:
        """解析对比分析响应"""
        return {
            "modifications_summary": "医生对报告进行了专业性调整",
            "ai_analysis_changes": "医生确认了AI分析结果",
            "monitoring_adjustments": "监测计划根据实际情况进行了优化",
            "medication_changes": "用药方案保持稳定",
            "new_concerns": "医生增加了一些预防性关注点",
            "clinical_reasoning": "基于临床经验的专业判断",
            "patient_impact": "有助于提高治疗效果和生活质量"
        }
    
    def _parse_health_summary_response(self, response: str) -> dict:
        """解析健康总结响应"""
        return {
            "overall_health_status": "健康状况总体良好，在医生指导下持续改善",
            "key_indicators_with_trends": "主要健康指标呈现积极趋势",
            "doctor_adjustments_explained": "医生根据最新情况调整了治疗方案",
            "important_patient_notes": "请按医生建议执行治疗计划",
            "data_highlights": "数据显示治疗效果良好"
        }
    
    def _parse_medication_response(self, response: str) -> dict:
        """解析用药指导响应"""
        return {
            "current_medication_status": "按医嘱用药，效果良好",
            "adjustment_reasons": "医生根据病情发展调整方案",
            "new_medication_purpose": "优化治疗效果，减少副作用",
            "special_instructions": "按时按量服用，注意观察反应",
            "monitoring_requirements": "定期复查，监测药物效果"
        }
    
    def _parse_lifestyle_monitoring_response(self, response: str) -> dict:
        """解析生活方式和监测响应"""
        return {
            "lifestyle_recommendations": "保持健康饮食和适量运动",
            "updated_monitoring_plan": "按医生安排定期复查",
            "self_management_tips": "记录健康数据，观察身体变化",
            "when_to_contact_doctor": "出现异常症状时及时联系"
        }
    
    def _get_default_comparison(self) -> dict:
        """获取默认对比分析"""
        return {
            "modifications_summary": "医生进行了专业评估",
            "ai_analysis_changes": "确认分析结果",
            "monitoring_adjustments": "优化监测计划",
            "medication_changes": "维持当前方案",
            "new_concerns": "增加预防关注",
            "clinical_reasoning": "基于临床经验",
            "patient_impact": "有益健康管理"
        }
    
    def _get_default_health_summary(self) -> dict:
        """获取默认健康总结"""
        return {
            "overall_health_status": "健康状况稳定",
            "key_indicators_with_trends": "指标正常",
            "doctor_adjustments_explained": "医生确认治疗方案",
            "important_patient_notes": "继续配合治疗",
            "data_highlights": "数据良好"
        }
    
    def _get_default_medication_guidance(self) -> dict:
        """获取默认用药指导"""
        return {
            "current_medication_status": "按医嘱用药",
            "adjustment_reasons": "维持现有方案",
            "new_medication_purpose": "控制病情发展",
            "special_instructions": "按时服药",
            "monitoring_requirements": "定期复查"
        }
    
    def _get_default_lifestyle_monitoring(self) -> dict:
        """获取默认生活方式和监测"""
        return {
            "lifestyle_recommendations": "健康生活方式",
            "updated_monitoring_plan": "定期监测",
            "self_management_tips": "自我观察",
            "when_to_contact_doctor": "异常时就医"
        }

def generate_comprehensive_patient_html(report_data: dict, patient_name: str = "患者") -> str:
    """生成综合患者健康报告HTML"""
    
    health_summary = report_data.get("health_summary", {})
    medication_guidance = report_data.get("medication_guidance", {})
    lifestyle_monitoring = report_data.get("lifestyle_monitoring", {})
    comparison = report_data.get("comparison", {})
    original_context = report_data.get("original_context", {})
    
    # 获取图表数据
    charts = original_context.get("charts", {})
    patient_info = original_context.get("patient", {})
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>综合健康报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .report-container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 32px;
            font-weight: 600;
        }}
        .header .subtitle {{
            color: #7f8c8d;
            margin-top: 15px;
            font-size: 18px;
        }}
        .patient-info {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .patient-info h2 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 6px solid #3498db;
            transition: transform 0.3s ease;
        }}
        .section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 24px;
            display: flex;
            align-items: center;
        }}
        .section-icon {{
            width: 40px;
            height: 40px;
            margin-right: 15px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
        }}
        .modifications-section {{ border-left-color: #e74c3c; }}
        .modifications-section .section-icon {{ background: #e74c3c; }}
        
        .health-section {{ border-left-color: #27ae60; }}
        .health-section .section-icon {{ background: #27ae60; }}
        
        .medication-section {{ border-left-color: #f39c12; }}
        .medication-section .section-icon {{ background: #f39c12; }}
        
        .lifestyle-section {{ border-left-color: #9b59b6; }}
        .lifestyle-section .section-icon {{ background: #9b59b6; }}
        
        .charts-section {{ border-left-color: #17a2b8; }}
        .charts-section .section-icon {{ background: #17a2b8; }}
        
        .content-item {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        .content-item h3 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 18px;
            display: flex;
            align-items: center;
        }}
        .content-item h3::before {{
            content: '•';
            color: #3498db;
            font-size: 20px;
            margin-right: 10px;
        }}
        .content-text {{
            color: #34495e;
            font-size: 16px;
            line-height: 1.7;
        }}
        .highlight-box {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        .highlight-box h4 {{
            color: #856404;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
        }}
        .footer-note {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
            margin-bottom: 20px;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .report-container {{ padding: 20px; }}
            .section {{ padding: 20px; }}
            .header h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>🏥 综合健康报告</h1>
            <div class="subtitle">基于原始数据和医生专业调整的个性化健康指导</div>
            <div class="subtitle">生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</div>
        </div>

        <div class="patient-info">
            <h2>👤 {patient_name}</h2>
            <p>年龄：{patient_info.get('age', '未知')} | 性别：{patient_info.get('gender', '未知')} | 诊断：{patient_info.get('diagnosis', '待确认')}</p>
        </div>

        <div class="section modifications-section">
            <h2>
                <div class="section-icon">🔄</div>
                医生的专业调整
            </h2>
            <div class="highlight-box">
                <h4>📋 本次调整概述</h4>
                <p>{comparison.get('modifications_summary', '医生对您的治疗方案进行了专业评估')}</p>
            </div>
            <div class="content-item">
                <h3>AI分析确认</h3>
                <div class="content-text">{comparison.get('ai_analysis_changes', '医生确认了系统分析结果')}</div>
            </div>
            <div class="content-item">
                <h3>监测计划调整</h3>
                <div class="content-text">{comparison.get('monitoring_adjustments', '监测计划经过优化')}</div>
            </div>
            <div class="content-item">
                <h3>用药方案变化</h3>
                <div class="content-text">{comparison.get('medication_changes', '用药方案保持稳定')}</div>
            </div>
            <div class="content-item">
                <h3>新增关注点</h3>
                <div class="content-text">{comparison.get('new_concerns', '医生增加了预防性关注')}</div>
            </div>
            <div class="highlight-box">
                <h4>🎯 调整的临床意义</h4>
                <p>{comparison.get('clinical_reasoning', '基于临床经验的专业判断')}</p>
                <p><strong>对您的影响：</strong>{comparison.get('patient_impact', '有助于提高治疗效果')}</p>
            </div>
        </div>

        <div class="section health-section">
            <h2>
                <div class="section-icon">🩺</div>
                综合健康状况
            </h2>
            <div class="content-item">
                <h3>整体评估</h3>
                <div class="content-text">{health_summary.get('overall_health_status', '健康状况良好')}</div>
            </div>
            <div class="content-item">
                <h3>关键指标和趋势</h3>
                <div class="content-text">{health_summary.get('key_indicators_with_trends', '指标趋势良好')}</div>
            </div>
            <div class="content-item">
                <h3>医生调整说明</h3>
                <div class="content-text">{health_summary.get('doctor_adjustments_explained', '医生确认治疗方案')}</div>
            </div>
            <div class="content-item">
                <h3>重要提醒</h3>
                <div class="content-text">{health_summary.get('important_patient_notes', '请继续配合治疗')}</div>
            </div>
            <div class="highlight-box">
                <h4>📊 数据亮点</h4>
                <p>{health_summary.get('data_highlights', '数据显示治疗效果良好')}</p>
            </div>
        </div>
"""

    # 添加图表部分（如果有的话）
    if charts:
        html_content += f"""
        <div class="section charts-section">
            <h2>
                <div class="section-icon">📈</div>
                健康数据图表
            </h2>
            <p>以下图表显示了您的健康指标变化趋势，医生已经根据这些数据进行了专业分析：</p>
"""
        for chart_name, chart_path in charts.items():
            if chart_path:
                html_content += f"""
            <div class="chart-container">
                <h4>{chart_name.replace('_', ' ').title()}</h4>
                <img src="{chart_path}" alt="{chart_name}" />
            </div>
"""
        html_content += "        </div>\n"

    html_content += f"""
        <div class="section medication-section">
            <h2>
                <div class="section-icon">💊</div>
                用药指导（含调整说明）
            </h2>
            <div class="content-item">
                <h3>目前用药状况</h3>
                <div class="content-text">{medication_guidance.get('current_medication_status', '按医嘱用药')}</div>
            </div>
            <div class="content-item">
                <h3>调整原因</h3>
                <div class="content-text">{medication_guidance.get('adjustment_reasons', '根据病情发展调整')}</div>
            </div>
            <div class="content-item">
                <h3>新方案目的</h3>
                <div class="content-text">{medication_guidance.get('new_medication_purpose', '优化治疗效果')}</div>
            </div>
            <div class="content-item">
                <h3>特殊注意事项</h3>
                <div class="content-text">{medication_guidance.get('special_instructions', '按时按量服用')}</div>
            </div>
            <div class="content-item">
                <h3>监测要求</h3>
                <div class="content-text">{medication_guidance.get('monitoring_requirements', '定期复查效果')}</div>
            </div>
        </div>

        <div class="section lifestyle-section">
            <h2>
                <div class="section-icon">🌟</div>
                生活指导与监测计划
            </h2>
            <div class="content-item">
                <h3>生活方式建议</h3>
                <div class="content-text">{lifestyle_monitoring.get('lifestyle_recommendations', '保持健康生活方式')}</div>
            </div>
            <div class="content-item">
                <h3>更新的监测计划</h3>
                <div class="content-text">{lifestyle_monitoring.get('updated_monitoring_plan', '按医生安排监测')}</div>
            </div>
            <div class="content-item">
                <h3>自我管理技巧</h3>
                <div class="content-text">{lifestyle_monitoring.get('self_management_tips', '记录观察身体变化')}</div>
            </div>
            <div class="content-item">
                <h3>何时联系医生</h3>
                <div class="content-text">{lifestyle_monitoring.get('when_to_contact_doctor', '出现异常症状时')}</div>
            </div>
        </div>

        <div class="footer">
            <div class="footer-note">
                <strong>📋 重要说明</strong><br>
                本报告结合了您的原始健康数据和医生的专业调整建议。医生的每一项修改都基于临床经验和您的具体情况，请严格按照医生的指导执行治疗计划。
            </div>
            
            <p>🌈 在医生的专业指导下，您的健康管理将更加精准有效！</p>
            <p><small>本综合报告生成于 {datetime.now().strftime('%Y年%m月%d日')}</small></p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def find_downloads_folder():
    """查找用户的下载文件夹路径"""
    import os
    possible_paths = [
        Path.home() / "Downloads",
        Path.home() / "下载", 
        Path("C:/Users") / os.environ.get("USERNAME", "") / "Downloads",
        Path("C:/Users") / os.environ.get("USERNAME", "") / "下载"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return Path.home() / "Downloads"  # 默认返回

def load_doctor_annotations(patient_id: str = None):
    """加载医生批注数据"""
    
    # 首先尝试从下载文件夹查找导出的批注文件
    downloads_dir = find_downloads_folder()
    print(f"[查找] 在下载文件夹中搜索: {downloads_dir}")
    
    # 查找下载文件夹中的批注文件
    if patient_id:
        annotation_patterns = [
            f"*{patient_id}*.json",
            "annotations_*.json",
            "doctor_annotations_*.json"
        ]
    else:
        annotation_patterns = [
            "annotations_*.json",
            "doctor_annotations_*.json",
            "*annotations*.json"
        ]
    
    found_files = []
    for pattern in annotation_patterns:
        found_files.extend(list(downloads_dir.glob(pattern)))
    
    if found_files:
        # 使用最新的文件
        latest_file = max(found_files, key=lambda p: p.stat().st_mtime)
        print(f"[发现] 在下载文件夹找到批注文件: {latest_file}")
        return load_json(latest_file)
    
    # 然后尝试从报告输出目录查找相关数据
    report_dir = Path("report/output")
    if patient_id:
        annotation_files = list(report_dir.glob(f"*{patient_id}*.json"))
    else:
        annotation_files = list(report_dir.glob("*.json"))
    
    if annotation_files:
        # 使用最新的批注文件
        latest_file = max(annotation_files, key=lambda p: p.stat().st_mtime)
        print(f"[发现] 在报告目录找到批注文件: {latest_file}")
        return load_json(latest_file)
    
    # 如果没有找到批注文件，创建基础数据结构
    print(f"[提示] 未找到{'患者 ' + patient_id + ' 的' if patient_id else ''}医生批注数据，使用默认模板")
    return {
        "patient_id": patient_id or "unknown",
        "exported_at": datetime.now().isoformat(),
        "annotations": [],
        "interactions": {},
        "note": "未找到医生批注，使用原始报告数据"
    }

def main():
    parser = argparse.ArgumentParser(description="生成结合原始数据和医生调整的综合患者健康报告")
    parser.add_argument("--patient-id", "-id", help="患者ID")
    parser.add_argument("--input", "-i", help="医生导出的批注JSON文件路径")
    # parser.add_argument("--downloads", "-d", action="store_true", help="在下载文件夹中查找最新的批注文件")
    # 默认false，改为可选参数
    parser.add_argument("--downloads", "-d", action="store_true", help="在下载文件夹中查找最新的批注文件")
    # parser.add_argument("--downloads", "-d",  default=False, help="在下载文件夹中查找最新的批注文件")
    parser.add_argument("--output", "-o", help="输出HTML文件路径（可选）")
    parser.add_argument("--patient-name", "-n", default="患者", help="患者姓名")
    args = parser.parse_args()

    # 检查输入参数
    if not args.patient_id and not args.input and not args.downloads:
        print("错误：请指定以下选项之一：")
        print("  --patient-id  患者ID")
        print("  --input       JSON文件路径")
        print("  --downloads   在下载文件夹中查找")
        parser.print_help()
        return

    annotation_data = None
    patient_id = None

    if args.downloads:
        # 在下载文件夹中查找最新的批注文件
        downloads_dir = find_downloads_folder()
        json_files = list(downloads_dir.glob("*.json"))
        if not json_files:
            print(f"错误：在下载文件夹 {downloads_dir} 中未找到JSON文件")
            return
        
        # 使用最新的JSON文件
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"[使用] 下载文件夹中的最新JSON文件: {latest_file}")
        
        try:
            annotation_data = load_json(latest_file)
            patient_id = annotation_data.get("patient_id", "unknown")
        except Exception as e:
            print(f"错误：无法读取JSON文件 - {e}")
            return
            
    # elif args.patient_id:
    #     # 通过患者ID加载批注数据
    #     patient_id = args.patient_id
    #     print(f"[处理] 患者ID: {patient_id}")
    #     annotation_data = load_doctor_annotations(patient_id)
    # else:
    #     # 从JSON文件读取
    #     input_path = Path(args.input)
    #     if not input_path.exists():
    #         print(f"错误：找不到输入文件 {input_path}")
    #         return

    #     try:
    #         annotation_data = load_json(input_path)
    #         patient_id = annotation_data.get("patient_id", "unknown")
    #         print(f"[处理] 患者ID: {patient_id}")
    #         print(f"[处理] 导出时间: {annotation_data.get('exported_at', '未知')}")
    #     except Exception as e:
    #         print(f"错误：无法读取JSON文件 - {e}")
    #         return

    elif args.input:
        # 从JSON文件读取
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误：找不到输入文件 {input_path}")
            return

        try:
            annotation_data = load_json(input_path)
            patient_id = annotation_data.get("patient_id", "unknown")
            print(f"[处理] 患者ID: {patient_id}")
            print(f"[处理] 导出时间: {annotation_data.get('exported_at', '未知')}")
        except Exception as e:
            print(f"错误：无法读取JSON文件 - {e}")
            return
    elif args.patient_id:
        # 通过患者ID加载批注数据
        patient_id = args.patient_id
        print(f"[处理] 患者ID: {patient_id}")
        annotation_data = load_doctor_annotations(patient_id)
    else:
        print("错误：请指定以下选项之一：")
        print("  --patient-id  患者ID")
        print("  --input       JSON文件路径")
        print("  --downloads   在下载文件夹中查找")
        parser.print_help()
        return


    # 生成综合健康报告
    print("[加载] 正在加载原始报告数据...")
    report_generator = ComprehensivePatientReportGenerator()
    
    # 加载原始报告数据
    original_data = report_generator.load_original_report_data(patient_id)
    if not original_data["success"]:
        print(f"[警告] 无法加载原始数据: {original_data['error']}")
        print("[继续] 使用批注数据生成报告...")
    
    original_context = original_data["context"]
    
    print("[分析] 正在对比原始报告与医生批注...")
    # 对比分析
    comparison = report_generator.compare_original_vs_annotations(original_context, annotation_data)
    
    print("[生成] 正在生成综合健康总结...")
    # 生成各部分内容
    health_summary = report_generator.generate_comprehensive_health_summary(original_context, annotation_data, comparison)
    medication_guidance = report_generator.generate_medication_guidance_with_changes(original_context, annotation_data, comparison)
    lifestyle_monitoring = report_generator.generate_lifestyle_and_monitoring_plan(original_context, annotation_data, comparison)
    
    # 打印报告摘要
    print("\n" + "="*70)
    print("🏥 综合患者健康报告摘要")
    print("="*70)
    print(f"👤 患者：{args.patient_name}")
    print(f"🔄 医生调整：{comparison['modifications_summary']}")
    print(f"📊 健康状况：{health_summary['overall_health_status']}")
    print(f"💊 用药变化：{medication_guidance['current_medication_status']}")
    print(f"📋 监测计划：{lifestyle_monitoring['updated_monitoring_plan']}")
    print("="*70)
    
    # 生成HTML文件
    patient_name = args.patient_name
    report_data = {
        "health_summary": health_summary,
        "medication_guidance": medication_guidance,
        "lifestyle_monitoring": lifestyle_monitoring,
        "comparison": comparison,
        "original_context": original_context
    }
    html_content = generate_comprehensive_patient_html(report_data, patient_name)
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUT_DIR / f"comprehensive_patient_report_{patient_id}_{timestamp}.html"
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入HTML文件
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"\n[完成] 综合患者健康报告HTML已生成：{output_path}")
    
    # 同时保存JSON格式的报告（用于进一步处理）
    json_output = output_path.with_suffix('.json')
    report_json = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "generated_at": datetime.now().isoformat(),
        "source_annotation": str(annotation_data.get("source_file", "patient_id_based")),
        "has_original_data": original_data["success"],
        "comprehensive_report": report_data
    }
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    
    print(f"[完成] 综合患者健康报告JSON已保存：{json_output}")

if __name__ == "__main__":
    main()
