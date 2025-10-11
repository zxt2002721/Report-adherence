# -*- coding: utf-8 -*-
"""
数据构建器 - 构建各种业务数据结构
"""

from collections import defaultdict
from .prompt_manager import prompt_manager


def build_lifestyle(memory: dict) -> dict:
    """构建生活方式数据"""
    ls = memory.get("lifestyle", {})
    if ls:
        return {
            "diet": ls.get("diet", "—"),
            "exercise": ls.get("exercise", "—"),
            "sleep": ls.get("sleep", "—"),
            "psychology": ls.get("psychology", "—"),
        }
    
    mapped = {"diet": "—", "exercise": "—", "sleep": "—", "psychology": "—"}
    for item in memory.get("prescription", {}).get("lifestyle", []) or []:
        t = item.get("recommendation_type")
        desc = item.get("description")
        if not desc:
            continue
        if t == "饮食": 
            mapped["diet"] = desc
        elif t == "运动": 
            mapped["exercise"] = desc
        elif t in ("睡眠", "作息"): 
            mapped["sleep"] = desc
        elif t in ("压力", "心理"): 
            mapped["psychology"] = desc
    
    return mapped


def build_adherence(memory: dict) -> dict:
    """构建依从性数据"""
    hist = memory.get("adherence_history", []) or []
    total = len(hist)
    compliant = sum(1 for a in hist if a.get("overall_status") == "完全遵从")
    noncompliant = sum(1 for a in hist if a.get("overall_status") == "不遵从")
    rate = f"{(compliant/total*100):.1f}%" if total else "0.0%"
    
    summary = memory.get("adherence_summary", {
        "total": total,
        "compliant": compliant,
        "noncompliant": noncompliant,
        "rate": rate
    })
    
    return {"history": hist, "summary": summary}


def build_app(memory: dict, dialogues: dict = None) -> dict:
    """构建应用使用数据"""
    if memory.get("app"):
        app = memory["app"]
        return {
            "checkins": app.get("checkins", "—"),
            "symptoms": app.get("symptoms", "—"),
            "consultations": app.get("consultations", "—"),
            "surveys": app.get("surveys", "—"),
            "adherence": app.get("adherence", "—"),
        }
    
    # 从原始数据计算
    hist = memory.get("adherence_history", []) or []
    sfh = memory.get("suggestion_feedback_history", []) or []
    
    days = len({h.get("date") for h in hist if h.get("date")})
    
    symptoms = (sum(1 for h in hist if "症状" in (h.get("category") or "")) + 
                sum(1 for s in sfh if "症状" in (s.get("suggestion_category") or "")))
    
    consults = 0
    if dialogues:
        msgs = dialogues.get("messages", []) or dialogues.get("records", []) or []
        consults = len(msgs) if isinstance(msgs, list) else 0
    
    surveys = sum(1 for h in hist if "问卷" in (h.get("category") or ""))
    
    adh = build_adherence(memory)
    adherence_txt = f"近{adh['summary']['total']}条记录，完全遵从 {adh['summary']['rate']}"
    
    return {
        "checkins": f"近月打卡 {days} 天",
        "symptoms": f"症状反馈 {symptoms} 次",
        "consultations": f"线上咨询 {consults} 次",
        "surveys": f"问卷 {surveys} 次",
        "adherence": adherence_txt
    }


def build_tips(memory: dict, monitoring: dict, status: dict, adherence: dict) -> dict:
    """构建建议提示数据"""
    def slot(s=None, a=None, d=None, r=None):
        return {
            "state": s or "—", 
            "advice": a or "—", 
            "doctor": d or "—", 
            "risk": r or "—"
        }
    
    tips = memory.get("tips", {})
    out = {
        "medication": slot(), 
        "monitoring": slot(), 
        "exercise": slot(), 
        "diet": slot(), 
        "psychology": slot()
    }
    
    # 从memory中读取已有的tips
    for k in out:
        if isinstance(tips.get(k), dict):
            out[k].update({kk: tips[k].get(kk, out[k][kk]) for kk in out[k]})
    
    # 使用prompt_manager生成上下文相关的默认建议
    contextual_tips = prompt_manager.generate_contextual_tips(monitoring, status, adherence)
    
    # 对于空值的字段，使用上下文相关的模板填充
    for category in out:
        for field in out[category]:
            if out[category][field] in ("—", ""):
                out[category][field] = contextual_tips[category][field]
    
    return out


def build_adherence_stats(memory: dict) -> dict:
    """构建依从性统计数据"""
    adherence = memory.get('adherence_history', []) or []
    
    total = len(adherence)
    compliant = sum(1 for a in adherence if a.get('overall_status') == '完全遵从')
    noncompliant = sum(1 for a in adherence if a.get('overall_status') == '不遵从')
    rate = f"{(compliant/total*100):.1f}%" if total else "0.0%"
    
    return {
        "summary": {
            "total": total, 
            "compliant": compliant, 
            "noncompliant": noncompliant, 
            "rate": rate
        }
    }
