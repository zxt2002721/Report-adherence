# -*- coding: utf-8 -*-
"""
药物信息处理器 - 处理药物相关数据
"""


def build_current_medications(memory: dict) -> dict:
    """
    汇总 memory['prescription']['medications']：
    返回 {"list":[{...}], "text":"药名 剂量 频次（途径）；..."}；无则 {"list":[], "text":"—"}
    """
    meds = (memory.get("prescription", {}) or {}).get("medications", []) or []
    if not isinstance(meds, list) or not meds:
        return {"list": [], "text": "—"}
    
    parts = []
    clean_list = []
    
    for m in meds:
        if not isinstance(m, dict):
            continue
        
        name = (m.get("drug_name") or m.get("name") or "").strip()
        dose = (m.get("dose") or "").strip()
        freq = (m.get("frequency") or "").strip()
        route = (m.get("route") or "").strip()
        
        seg = " ".join(x for x in [name, dose, freq] if x).strip()
        if route:
            seg = f"{seg}（{route}）"
        
        if seg:
            parts.append(seg)
        
        clean_list.append({
            "drug_name": name, 
            "dose": dose, 
            "frequency": freq, 
            "route": route
        })
    
    text = "；".join(parts) if parts else "—"
    return {"list": clean_list, "text": text}


def process_disease_info_medications(memory: dict) -> dict:
    """处理疾病信息中的药物数据"""
    disease_info = memory.get("disease_info", {"primary_diseases": []})
    
    # 汇总处方药物并注入
    try:
        _meds = build_current_medications(memory)
        disease_info["current_medications"] = _meds.get("list", [])
        disease_info["current_medications_text"] = _meds.get("text", "—")
    except Exception:
        disease_info["current_medications"] = []
        disease_info["current_medications_text"] = "—"
    
    # 为每个主要疾病添加药物文本
    try:
        for _d in disease_info.get("primary_diseases", []) or []:
            if isinstance(_d, dict) and "current_medications_text" not in _d:
                _d["current_medications_text"] = disease_info.get("current_medications_text", "—")
    except Exception:
        pass
    
    return disease_info
