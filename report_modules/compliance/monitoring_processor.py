# -*- coding: utf-8 -*-
"""
监测数据处理器 - 处理生理监测数据
"""

import pandas as pd


def build_monitoring_from_df(df_patient: pd.DataFrame) -> dict:
    """从DataFrame构建监测数据"""
    last = df_patient.iloc[-1].to_dict()
    
    def v(key, unit):
        return f"{last[key]} {unit}" if key in last and pd.notna(last[key]) else "—"
    
    bp = "—"
    if "sbp" in last and "dbp" in last and pd.notna(last["sbp"]) and pd.notna(last["dbp"]):
        bp = f"{int(last['sbp'])}/{int(last['dbp'])} mmHg"
    
    return {
        "bp": bp,
        "bg": v("fbg", "mmol/L"),
        "hba1c": f"{last['hba1c']}%" if "hba1c" in last and pd.notna(last["hba1c"]) else "—",
        "ldl": v("ldl", "mmol/L"),
        "bmi": v("bmi", "kg/m²"),
        "hr": v("hr", "bpm"),
        "kidney": f"eGFR {int(last['egfr'])} ml/min/1.73m²" if "egfr" in last and pd.notna(last["egfr"]) else "—",
    }


def compute_status(monitoring: dict) -> dict:
    """计算各项指标的达标状态"""
    def _ok_bp(bp_txt: str):
        try:
            s, d = bp_txt.split(" ")[0].split("/")
            return int(s) < 140 and int(d) < 90
        except Exception:
            return False
    
    def _get_numeric_value(text: str) -> float:
        """从文本中提取数值"""
        try:
            if text == "—":
                return None
            # 提取数字部分
            return float(text.split()[0].rstrip('%'))
        except (ValueError, IndexError):
            return None
    
    m = monitoring
    
    # 血压状态
    bp_status = "—"
    if m.get("bp", "—") != "—":
        bp_status = "达标" if _ok_bp(m["bp"]) else "未达标"
    
    # 血糖状态
    bg_status = "—"
    bg_val = _get_numeric_value(m.get("bg", "—"))
    if bg_val is not None:
        bg_status = "达标" if bg_val < 7.0 else "未达标"
    
    # 糖化血红蛋白状态
    hba1c_status = "—"
    hba1c_val = _get_numeric_value(m.get("hba1c", "—"))
    if hba1c_val is not None:
        hba1c_status = "达标" if hba1c_val < 7.0 else "未达标"
    
    # LDL状态
    ldl_status = "—"
    ldl_val = _get_numeric_value(m.get("ldl", "—"))
    if ldl_val is not None:
        ldl_status = "达标" if ldl_val < 2.6 else "未达标"
    
    # BMI状态
    bmi_status = "—"
    bmi_val = _get_numeric_value(m.get("bmi", "—"))
    if bmi_val is not None:
        bmi_status = "达标" if 18.5 <= bmi_val <= 24.9 else "未达标"
    
    return {
        "bp": bp_status,
        "bg": bg_status,
        "hba1c": hba1c_status,
        "ldl": ldl_status,
        "bmi": bmi_status,
        "hr": "达标" if m.get("hr", "—") != "—" else "—",
        "kidney": "达标" if m.get("kidney", "—") != "—" else "—",
    }


def get_report_period(df_patient: pd.DataFrame) -> str:
    """获取报告周期"""
    if ("date" in df_patient.columns) and (df_patient["date"].notna().any()):
        period_start = pd.to_datetime(df_patient["date"].min()).date().isoformat()
        period_end = pd.to_datetime(df_patient["date"].max()).date().isoformat()
        return f"{period_start} 至 {period_end}"
    else:
        return "—"
