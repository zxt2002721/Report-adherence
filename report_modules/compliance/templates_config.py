# -*- coding: utf-8 -*-
"""
默认健康管理提示模板配置
"""

# 默认健康管理提示模板
DEFAULT_TIPS_TEMPLATES = {
    "medication": {
        "state_templates": {
            "low_adherence": "依从性一般",  # rate < 60%
            "good_adherence": "依从性尚可"  # rate >= 60%
        },
        "advice": "使用分药器/手机闹钟固定时程；漏服>2次/周需随访复评。",
        "doctor": "必要时简化方案或调整给药时程。",
        "risk": "长期漏服将增加波动与并发症风险。"
    },
    
    "monitoring": {
        "state_templates": {
            "has_uncontrolled": "指标部分未达标",
            "all_controlled": "指标总体达标"
        },
        "advice": "按医嘱规律监测并记录，出现异常值及时就医/复诊。",
        "doctor": "结合居家监测与化验指标综合评估干预效果。",
        "risk_templates": {
            "with_issues": "未达标项：{risk_items}",
            "no_issues": "无"
        }
    },
    
    "exercise": {
        "state": "建议规律运动",
        "advice": "每周≥150分钟中等强度有氧 + 2次抗阻训练；避免久坐。",
        "doctor": "合并慢病者循序渐进，运动前做好热身与血压自测。",
        "risk": "运动不足可致体重上升、胰岛素抵抗、血压控制变差。"
    },
    
    "diet": {
        "state": "建议清淡少盐、控糖控脂",
        "advice": "优先全谷物/蔬果；每日盐<5g；限制含糖饮料与油炸。",
        "doctor": "合并肾病/高钾者定制个体化膳食。",
        "risk": "不合理饮食会影响血糖/血脂/血压控制。"
    },
    
    "psychology": {
        "state": "关注睡眠与压力管理",
        "advice": "固定作息，睡前避免咖啡因与电子屏；可练习冥想/呼吸。",
        "doctor": "持续焦虑/失眠建议心理门诊或睡眠评估。",
        "risk": "长期压力与睡眠障碍会降低依从性并升高心血管风险。"
    }
}

# 风险评估项目映射
RISK_MAPPING = {
    "bp": "血压控制欠佳",
    "bg": "空腹血糖偏高", 
    "hba1c": "糖化血红蛋白未达标",
    "ldl": "LDL-C 偏高",
    "bmi": "体重/BMI 超标"
}