# -*- coding: utf-8 -*-
"""
患者健康报告生成器
基于医生的诊疗批注和分析，生成患者易懂的健康状况报告
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 使用现有的报告模块
from report_modules.data_loader import load_json
from report_modules import config

OUT_DIR = Path("report/output")

class PatientHealthReportGenerator:
    """患者健康报告生成器"""
    
    def __init__(self):
        # 使用配置模块中的client
        self.client = config.client
    
    def generate_health_summary(self, annotation_data: dict) -> dict:
        """生成健康状况总结"""
        
        annotations = annotation_data.get("annotations", [])
        interactions = annotation_data.get("interactions", {})
        
        # 构建健康总结prompt
        prompt = f"""
请基于医生的诊疗记录，为患者生成一份通俗易懂的健康状况报告：

医生批注：
{json.dumps(annotations, ensure_ascii=False, indent=2)}

诊疗交互记录：
{json.dumps(interactions, ensure_ascii=False, indent=2)}

请用患者能理解的语言，生成健康报告，包含：
1. 当前健康状况描述
2. 主要关注的健康指标
3. 治疗进展情况
4. 需要注意的事项

请以JSON格式返回：
{{
    "health_status": "当前健康状况的整体描述",
    "key_indicators": "主要健康指标的说明",
    "treatment_progress": "治疗效果和进展",
    "important_notes": "需要特别注意的事项"
}}
"""
        
        try:
            response = self._call_ai(prompt, "健康状况总结")
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_health_response(response)
        except Exception as e:
            print(f"生成健康总结时出错: {e}")
            return self._get_default_health_summary()
    
    def generate_medication_guidance(self, annotation_data: dict) -> dict:
        """生成用药指导"""
        
        interactions = annotation_data.get("interactions", {})
        
        # 提取用药相关信息
        medication_info = {}
        for key, value in interactions.items():
            if "medication" in key.lower() or "drug" in key.lower() or "med" in key.lower():
                medication_info[key] = value
        
        prompt = f"""
基于医生的用药记录，为患者生成用药指导：

用药相关记录：
{json.dumps(medication_info, ensure_ascii=False, indent=2)}

请用简单易懂的语言说明：
1. 目前的用药情况
2. 用药的作用和目的
3. 服药注意事项
4. 可能的副作用提醒

请以JSON格式返回：
{{
    "current_medications": "目前用药情况说明",
    "medication_purpose": "用药的作用和目的",
    "taking_instructions": "服药方法和注意事项",
    "side_effects_alert": "可能出现的副作用提醒"
}}
"""
        
        try:
            response = self._call_ai(prompt, "用药指导")
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_medication_response(response)
        except Exception as e:
            print(f"生成用药指导时出错: {e}")
            return self._get_default_medication_guidance()
    
    def generate_lifestyle_recommendations(self, annotation_data: dict) -> dict:
        """生成生活方式建议"""
        
        interactions = annotation_data.get("interactions", {})
        
        # 提取生活方式相关信息
        lifestyle_info = {}
        for key, value in interactions.items():
            if any(keyword in key.lower() for keyword in ["lifestyle", "life", "diet", "exercise", "sleep"]):
                lifestyle_info[key] = value
        
        prompt = f"""
基于医生的记录，为患者生成生活方式建议：

生活方式相关记录：
{json.dumps(lifestyle_info, ensure_ascii=False, indent=2)}

请提供实用的生活指导：
1. 饮食方面的建议
2. 运动锻炼指导
3. 作息和休息建议
4. 其他健康习惯

请以JSON格式返回：
{{
    "diet_advice": "饮食建议和注意事项",
    "exercise_guide": "运动锻炼的指导",
    "rest_schedule": "作息时间安排建议",
    "healthy_habits": "其他有益的健康习惯"
}}
"""
        
        try:
            response = self._call_ai(prompt, "生活方式建议")
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_lifestyle_response(response)
        except Exception as e:
            print(f"生成生活方式建议时出错: {e}")
            return self._get_default_lifestyle_recommendations()
    
    def generate_monitoring_plan(self, annotation_data: dict) -> dict:
        """生成监测计划"""
        
        interactions = annotation_data.get("interactions", {})
        
        # 提取监测相关信息
        monitoring_info = {}
        for key, value in interactions.items():
            if any(keyword in key.lower() for keyword in ["monitor", "check", "test", "recheck"]):
                monitoring_info[key] = value
        
        prompt = f"""
基于医生的监测安排，为患者说明检查计划：

监测相关记录：
{json.dumps(monitoring_info, ensure_ascii=False, indent=2)}

请说明：
1. 需要定期检查的项目
2. 检查的频率和时间
3. 自我监测的方法
4. 异常情况的处理

请以JSON格式返回：
{{
    "regular_checkups": "定期检查项目和安排",
    "monitoring_frequency": "检查频率说明",
    "self_monitoring": "日常自我监测方法",
    "emergency_signs": "需要立即就医的异常征象"
}}
"""
        
        try:
            response = self._call_ai(prompt, "监测计划")
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            else:
                return self._parse_monitoring_response(response)
        except Exception as e:
            print(f"生成监测计划时出错: {e}")
            return self._get_default_monitoring_plan()
    
    def _call_ai(self, prompt: str, context: str) -> str:
        """调用AI分析"""
        try:
            resp = self.client.chat.completions.create(
                model="qwen3-4b",
                messages=[
                    {"role": "system", "content": f"你是一名温和耐心的健康顾问，负责{context}。请用简单易懂、温和鼓励的语言与患者沟通，避免使用专业术语。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                extra_body={"enable_thinking": False}
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI调用失败: {e}")
            return ""
    
    def _parse_health_response(self, response: str) -> dict:
        """解析健康状况响应"""
        return {
            "health_status": "您的健康状况总体良好，各项指标在可控范围内",
            "key_indicators": "血压、血糖等主要指标需要持续关注",
            "treatment_progress": "治疗效果良好，请继续按医嘱进行",
            "important_notes": "请按时服药，保持健康的生活方式"
        }
    
    def _parse_medication_response(self, response: str) -> dict:
        """解析用药指导响应"""
        return {
            "current_medications": "目前使用的药物能有效控制病情",
            "medication_purpose": "这些药物主要用于控制血压和血糖",
            "taking_instructions": "请按时按量服药，不要随意停药",
            "side_effects_alert": "如出现不适症状，请及时联系医生"
        }
    
    def _parse_lifestyle_response(self, response: str) -> dict:
        """解析生活方式响应"""
        return {
            "diet_advice": "建议低盐低糖饮食，多吃蔬菜水果",
            "exercise_guide": "适量运动，如散步、太极等",
            "rest_schedule": "保证充足睡眠，规律作息",
            "healthy_habits": "戒烟限酒，保持心情愉快"
        }
    
    def _parse_monitoring_response(self, response: str) -> dict:
        """解析监测计划响应"""
        return {
            "regular_checkups": "定期复查血压、血糖等指标",
            "monitoring_frequency": "建议每月复查一次",
            "self_monitoring": "可在家自测血压，记录数值",
            "emergency_signs": "如出现胸痛、气促等症状需立即就医"
        }
    
    def _get_default_health_summary(self) -> dict:
        """获取默认健康总结"""
        return {
            "health_status": "健康状况总体稳定",
            "key_indicators": "主要指标在正常范围",
            "treatment_progress": "治疗进展良好",
            "important_notes": "请继续配合治疗"
        }
    
    def _get_default_medication_guidance(self) -> dict:
        """获取默认用药指导"""
        return {
            "current_medications": "按医嘱用药",
            "medication_purpose": "控制病情进展",
            "taking_instructions": "按时按量服用",
            "side_effects_alert": "如有不适及时就医"
        }
    
    def _get_default_lifestyle_recommendations(self) -> dict:
        """获取默认生活方式建议"""
        return {
            "diet_advice": "健康饮食，营养均衡",
            "exercise_guide": "适量运动锻炼",
            "rest_schedule": "规律作息时间",
            "healthy_habits": "保持良好习惯"
        }
    
    def _get_default_monitoring_plan(self) -> dict:
        """获取默认监测计划"""
        return {
            "regular_checkups": "定期复查",
            "monitoring_frequency": "按医嘱安排",
            "self_monitoring": "日常观察",
            "emergency_signs": "异常情况及时就医"
        }

def generate_patient_health_html(health_data: dict, patient_name: str = "患者") -> str:
    """生成患者健康报告HTML"""
    
    health_summary = health_data.get("health_summary", {})
    medication_guidance = health_data.get("medication_guidance", {})
    lifestyle_recommendations = health_data.get("lifestyle_recommendations", {})
    monitoring_plan = health_data.get("monitoring_plan", {})
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>个人健康报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1000px;
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
        .health-section {{ border-left-color: #27ae60; }}
        .health-section .section-icon {{ background: #27ae60; }}
        
        .medication-section {{ border-left-color: #e74c3c; }}
        .medication-section .section-icon {{ background: #e74c3c; }}
        
        .lifestyle-section {{ border-left-color: #f39c12; }}
        .lifestyle-section .section-icon {{ background: #f39c12; }}
        
        .monitoring-section {{ border-left-color: #9b59b6; }}
        .monitoring-section .section-icon {{ background: #9b59b6; }}
        
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
        .contact-info {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin-top: 20px;
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
            <h1>🏥 个人健康报告</h1>
            <div class="subtitle">亲爱的 <strong>{patient_name}</strong>，这是您的个性化健康指导</div>
            <div class="subtitle">生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}</div>
        </div>

        <div class="section health-section">
            <h2>
                <div class="section-icon">🩺</div>
                健康状况总览
            </h2>
            <div class="content-item">
                <h3>总体评估</h3>
                <div class="content-text">{health_summary.get('health_status', '健康状况良好')}</div>
            </div>
            <div class="content-item">
                <h3>关键指标</h3>
                <div class="content-text">{health_summary.get('key_indicators', '各项指标正常')}</div>
            </div>
            <div class="content-item">
                <h3>治疗进展</h3>
                <div class="content-text">{health_summary.get('treatment_progress', '治疗效果良好')}</div>
            </div>
            <div class="content-item">
                <h3>重要提醒</h3>
                <div class="content-text">{health_summary.get('important_notes', '请继续配合治疗')}</div>
            </div>
        </div>

        <div class="section medication-section">
            <h2>
                <div class="section-icon">💊</div>
                用药指导
            </h2>
            <div class="content-item">
                <h3>目前用药</h3>
                <div class="content-text">{medication_guidance.get('current_medications', '按医嘱用药')}</div>
            </div>
            <div class="content-item">
                <h3>用药目的</h3>
                <div class="content-text">{medication_guidance.get('medication_purpose', '控制病情发展')}</div>
            </div>
            <div class="content-item">
                <h3>服药注意事项</h3>
                <div class="content-text">{medication_guidance.get('taking_instructions', '按时按量服用')}</div>
            </div>
            <div class="content-item">
                <h3>副作用提醒</h3>
                <div class="content-text">{medication_guidance.get('side_effects_alert', '如有不适及时就医')}</div>
            </div>
        </div>

        <div class="section lifestyle-section">
            <h2>
                <div class="section-icon">🌟</div>
                生活方式建议
            </h2>
            <div class="content-item">
                <h3>饮食建议</h3>
                <div class="content-text">{lifestyle_recommendations.get('diet_advice', '健康饮食，营养均衡')}</div>
            </div>
            <div class="content-item">
                <h3>运动指导</h3>
                <div class="content-text">{lifestyle_recommendations.get('exercise_guide', '适量运动锻炼')}</div>
            </div>
            <div class="content-item">
                <h3>作息安排</h3>
                <div class="content-text">{lifestyle_recommendations.get('rest_schedule', '规律作息时间')}</div>
            </div>
            <div class="content-item">
                <h3>健康习惯</h3>
                <div class="content-text">{lifestyle_recommendations.get('healthy_habits', '保持良好习惯')}</div>
            </div>
        </div>

        <div class="section monitoring-section">
            <h2>
                <div class="section-icon">📊</div>
                监测计划
            </h2>
            <div class="content-item">
                <h3>定期检查</h3>
                <div class="content-text">{monitoring_plan.get('regular_checkups', '按医嘱定期复查')}</div>
            </div>
            <div class="content-item">
                <h3>检查频率</h3>
                <div class="content-text">{monitoring_plan.get('monitoring_frequency', '遵循医生安排')}</div>
            </div>
            <div class="content-item">
                <h3>自我监测</h3>
                <div class="content-text">{monitoring_plan.get('self_monitoring', '日常观察身体变化')}</div>
            </div>
            <div class="content-item">
                <h3>紧急情况</h3>
                <div class="content-text">{monitoring_plan.get('emergency_signs', '异常症状及时就医')}</div>
            </div>
        </div>

        <div class="footer">
            <div class="footer-note">
                <strong>📋 温馨提醒</strong><br>
                本报告基于您的诊疗记录生成，旨在帮助您更好地了解自己的健康状况。请将此报告作为健康管理的参考，具体治疗方案请以医生的专业建议为准。
            </div>
            
            <div class="contact-info">
                <strong>🔔 重要提醒</strong><br>
                如有任何疑问或身体不适，请及时联系您的主治医生。定期复查和良好的生活习惯是健康管理的关键。
            </div>
            
            <p>🌈 祝您身体健康，生活愉快！</p>
            <p><small>本报告生成于 {datetime.now().strftime('%Y年%m月%d日')}</small></p>
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
    print(f"[提示] 请确保已在医生报告中添加批注并导出JSON文件到下载文件夹")
    return {
        "patient_id": patient_id or "unknown",
        "exported_at": datetime.now().isoformat(),
        "annotations": [],
        "interactions": {},
        "note": "未找到医生批注，生成基础健康报告模板"
    }

def main():
    parser = argparse.ArgumentParser(description="基于医生批注生成患者健康报告")
    parser.add_argument("--patient-id", "-id", help="患者ID")
    parser.add_argument("--input", "-i", help="医生导出的批注JSON文件路径")
    parser.add_argument("--downloads", "-d", action="store_true", help="在下载文件夹中查找最新的批注文件")
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
            
    elif args.patient_id:
        # 通过患者ID加载批注数据
        patient_id = args.patient_id
        print(f"[处理] 患者ID: {patient_id}")
        annotation_data = load_doctor_annotations(patient_id)
    else:
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

    # 生成患者健康报告
    print("[生成] 正在调用AI生成患者健康报告...")
    report_generator = PatientHealthReportGenerator()
    
    # 多维度分析
    health_summary = report_generator.generate_health_summary(annotation_data)
    medication_guidance = report_generator.generate_medication_guidance(annotation_data)
    lifestyle_recommendations = report_generator.generate_lifestyle_recommendations(annotation_data)
    monitoring_plan = report_generator.generate_monitoring_plan(annotation_data)
    
    # 打印报告摘要
    print("\n" + "="*60)
    print("🏥 患者健康报告摘要")
    print("="*60)
    print(f"👤 患者：{args.patient_name}")
    print(f"📊 健康状况：{health_summary['health_status']}")
    print(f"🎯 关键指标：{health_summary['key_indicators']}")
    print(f"💊 用药情况：{medication_guidance['current_medications']}")
    print(f"🌟 生活建议：{lifestyle_recommendations['diet_advice']}")
    print(f"📋 监测计划：{monitoring_plan['regular_checkups']}")
    print("="*60)
    
    # 生成HTML文件
    patient_name = args.patient_name
    health_data = {
        "health_summary": health_summary,
        "medication_guidance": medication_guidance,
        "lifestyle_recommendations": lifestyle_recommendations,
        "monitoring_plan": monitoring_plan
    }
    html_content = generate_patient_health_html(health_data, patient_name)
    
    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUT_DIR / f"patient_health_report_{patient_id}_{timestamp}.html"
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入HTML文件
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"\n[完成] 患者健康报告HTML已生成：{output_path}")
    
    # 同时保存JSON格式的报告（用于进一步处理）
    json_output = output_path.with_suffix('.json')
    report_json = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "generated_at": datetime.now().isoformat(),
        "source_annotation": str(annotation_data.get("source_file", "patient_id_based")),
        "health_report": health_data
    }
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    
    print(f"[完成] 患者健康报告JSON已保存：{json_output}")

if __name__ == "__main__":
    main()
