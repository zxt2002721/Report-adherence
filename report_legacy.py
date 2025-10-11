# -*- coding: utf-8 -*-
"""
Markdown 模板 -> HTML（医生版/家属版），带生理数据&依从性可视化 + LLM 总结（Qwen）
目录结构：
  data/template/*.md
  data/output/memory/*_memory.json
  data/output/dialogue_data/*_multiday.json   (可选)
  data/output/patient_physio_timeseries.csv   (含 patient_id 列)
  report/output/*.html  和  report/output/assets/*.png
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from jinja2 import Environment, BaseLoader, ChainableUndefined
from markdown import markdown
from openai import OpenAI

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
        clean_list.append({"drug_name": name, "dose": dose, "frequency": freq, "route": route})
    text = "；".join(parts) if parts else "—"
    return {"list": clean_list, "text": text}

# ======================== 可配置路径 ========================
TPL_DIR = Path("data/template")
MEMORY_DIR = Path("data/output/memory")
DIALOGUE_DIR = Path("data/output/dialogue_data")
PHYSIO_CSV = Path("data/output/patient_physio_timeseries.csv")

OUT_DIR = Path("report/output")
ASSETS_DIR = OUT_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# 注意：沿用你现有的 Dashscope 兼容调用（保持用法一致）
client = OpenAI(
    api_key="sk-0bf69a2ea8374928ba7cadbf998f07ae",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def generate_ai_analysis(monitoring: dict, adherence: dict) -> dict:
    """
    调用 Qwen 模型生成 AI 总结（summary / risk_assessment / recommendations）
    """
    prompt = f"""
患者最新监测数据：
{json.dumps(monitoring, ensure_ascii=False, indent=2)}

患者依从性数据（可包含 history/summary 等）：
{json.dumps(adherence, ensure_ascii=False, indent=2)}

请生成三段中文文本：
1. summary: 总结患者整体情况
2. risk_assessment: 风险评估
3. recommendations: 个性化建议
格式严格为 JSON，键为 summary, risk_assessment, recommendations。
    """.strip()

    resp = client.chat.completions.create(
        model="qwen3-4b",
        messages=[
            {"role": "system", "content": "你是一名临床医生助手，输出简洁清晰的中文段落。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        extra_body={"enable_thinking": False}
    )

    text = resp.choices[0].message.content.strip()
    try:
        data = json.loads(text)
        return {
            "summary": data.get("summary", "（LLM未返回）"),
            "risk_assessment": data.get("risk_assessment", "（LLM未返回）"),
            "recommendations": data.get("recommendations", "（LLM未返回）")
        }
    except Exception:
        return {
            "summary": "（占位）整体控制尚可。",
            "risk_assessment": "（占位）饮食与漏服是主要风险。",
            "recommendations": "（占位）携带药盒，减盐限糖，复查指标。"
        }

# ==================== 工具函数：字体/画图 ====================
def _config_chinese_font():
    zh = None
    for f in font_manager.fontManager.ttflist:
        if 'SimHei' in f.name or 'Microsoft YaHei' in f.name:
            zh = f.name; break
    if zh:
        plt.rcParams['font.sans-serif'] = [zh]
    plt.rcParams['axes.unicode_minus'] = False

def _as_uri(p: Path) -> str:
    try:
        if p and p.exists():
            return str(p.relative_to(OUT_DIR).as_posix())
        return ""
    except Exception:
        return p.name if p and p.exists() else ""

def save_line_chart(dates, values, title, output_path):
    _config_chinese_font()
    plt.figure(figsize=(9, 4))
    plt.plot(dates, values, marker='o')
    plt.title(title); plt.xlabel('日期'); plt.ylabel('数值')
    plt.xticks(rotation=45, ha='right'); plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight"); plt.close()

def save_bar_compare(categories, vals_a, vals_b, label_a, label_b, title, output_path):
    _config_chinese_font()
    import numpy as np
    x = np.arange(len(categories))
    width = 0.38
    plt.figure(figsize=(8, 4.5))
    plt.bar(x - width/2, vals_a, width, label=label_a)
    plt.bar(x + width/2, vals_b, width, label=label_b)
    plt.xticks(x, categories, rotation=0)
    plt.title(title); plt.legend()
    plt.tight_layout(); plt.savefig(output_path, bbox_inches="tight"); plt.close()

def save_trend_multi(dates, series_dict, title, output_path):
    _config_chinese_font()
    plt.figure(figsize=(10, 5))
    for name, ys in series_dict.items():
        plt.plot(dates, ys, marker='o', label=name)
    plt.title(title); plt.xlabel('日期'); plt.ylabel('数值/标记')
    plt.xticks(rotation=45, ha='right'); plt.grid(True); plt.legend()
    plt.tight_layout(); plt.savefig(output_path, bbox_inches="tight"); plt.close()

# =================== 依从性统计与图表 ===================
def build_lifestyle(memory: dict) -> dict:
    ls = memory.get("lifestyle", {})
    if ls:
        return {
            "diet": ls.get("diet", "—"),
            "exercise": ls.get("exercise", "—"),
            "sleep": ls.get("sleep", "—"),
            "psychology": ls.get("psychology", "—"),
        }
    mapped = {"diet":"—","exercise":"—","sleep":"—","psychology":"—"}
    for item in memory.get("prescription", {}).get("lifestyle", []) or []:
        t = item.get("recommendation_type")
        desc = item.get("description")
        if not desc:
            continue
        if t == "饮食": mapped["diet"] = desc
        elif t == "运动": mapped["exercise"] = desc
        elif t in ("睡眠","作息"): mapped["sleep"] = desc
        elif t in ("压力","心理"): mapped["psychology"] = desc
    return mapped

def build_adherence(memory: dict) -> dict:
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

def build_app(memory: dict, dialogues: dict | None = None) -> dict:
    if memory.get("app"):
        app = memory["app"]
        return {
            "checkins": app.get("checkins", "—"),
            "symptoms": app.get("symptoms", "—"),
            "consultations": app.get("consultations", "—"),
            "surveys": app.get("surveys", "—"),
            "adherence": app.get("adherence", "—"),
        }
    hist = memory.get("adherence_history", []) or []
    sfh = memory.get("suggestion_feedback_history", []) or []
    days = len({h.get("date") for h in hist if h.get("date")})
    symptoms = sum(1 for h in hist if "症状" in (h.get("category") or "")) + \
               sum(1 for s in sfh if "症状" in (s.get("suggestion_category") or ""))
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
    def slot(s=None,a=None,d=None,r=None):
        return {"state": s or "—", "advice": a or "—", "doctor": d or "—", "risk": r or "—"}
    tips = memory.get("tips", {})
    out = {
        "medication": slot(), "monitoring": slot(), "exercise": slot(), "diet": slot(), "psychology": slot()
    }
    for k in out:
        if isinstance(tips.get(k), dict):
            out[k].update({kk: tips[k].get(kk, out[k][kk]) for kk in out[k]})
    risk_parts = []
    if status.get("bp") != "达标": risk_parts.append("血压控制欠佳")
    if status.get("bg") != "达标": risk_parts.append("空腹血糖偏高")
    if status.get("hba1c") != "达标": risk_parts.append("糖化血红蛋白未达标")
    if status.get("ldl") != "达标": risk_parts.append("LDL-C 偏高")
    if status.get("bmi") != "达标": risk_parts.append("体重/BMI 超标")
    hist = (adherence or {}).get("history", [])
    total = len(hist)
    compliant = sum(1 for a in hist if a.get("overall_status") == "完全遵从")
    rate = (compliant/total*100) if total else 0.0
    adh_state = "依从性一般" if rate < 60 else "依从性尚可"
    if out["medication"]["state"] in ("—",""):
        out["medication"].update({
            "state": adh_state,
            "advice": "使用分药器/手机闹钟固定时程；漏服>2次/周需随访复评。",
            "doctor": "必要时简化方案或调整给药时程。",
            "risk": "长期漏服将增加波动与并发症风险。"
        })
    if out["monitoring"]["state"] in ("—",""):
        out["monitoring"].update({
            "state": "指标部分未达标" if risk_parts else "指标总体达标",
            "advice": "按医嘱规律监测并记录，出现异常值及时就医/复诊。",
            "doctor": "结合居家监测与化验指标综合评估干预效果。",
            "risk": "未达标项：" + ("、".join(risk_parts) if risk_parts else "无")
        })
    if out["exercise"]["state"] in ("—",""):
        out["exercise"].update({
            "state": "建议规律运动",
            "advice": "每周≥150分钟中等强度有氧 + 2次抗阻训练；避免久坐。",
            "doctor": "合并慢病者循序渐进，运动前做好热身与血压自测。",
            "risk": "运动不足可致体重上升、胰岛素抵抗、血压控制变差。"
        })
    if out["diet"]["state"] in ("—",""):
        out["diet"].update({
            "state": "建议清淡少盐、控糖控脂",
            "advice": "优先全谷物/蔬果；每日盐<5g；限制含糖饮料与油炸。",
            "doctor": "合并肾病/高钾者定制个体化膳食。",
            "risk": "不合理饮食会影响血糖/血脂/血压控制。"
        })
    if out["psychology"]["state"] in ("—",""):
        out["psychology"].update({
            "state": "关注睡眠与压力管理",
            "advice": "固定作息，睡前避免咖啡因与电子屏；可练习冥想/呼吸。",
            "doctor": "持续焦虑/失眠建议心理门诊或睡眠评估。",
            "risk": "长期压力与睡眠障碍会降低依从性并升高心血管风险。"
        })
    return out

def build_adherence_stats(memory: dict, assets_dir: Path):
    adherence = memory.get('adherence_history', []) or []
    dates_set = set()
    cat_date_counts = defaultdict(lambda: defaultdict(int))
    for a in adherence:
        date = a.get('date')
        cat = a.get('category', '其他')
        if date:
            dates_set.add(date)
            cat_date_counts[cat][date] += 1
    dates = sorted(dates_set)
    series = {cat: [cat_date_counts[cat].get(d, 0) for d in dates] for cat in cat_date_counts}
    charts = {}
    if dates and series:
        p = assets_dir / "adherence_trend.png"
        save_trend_multi(dates, series, "各类别依从趋势", p)
        charts["adherence_trend"] = _as_uri(p)
    causes = defaultdict(int)
    for a in adherence:
        if a.get('overall_status') != '完全遵从':
            reason = a.get('reason', '其他')
            causes[reason] += 1
    if causes:
        top = dict(sorted(causes.items(), key=lambda x: x[1], reverse=True)[:5])
        _config_chinese_font()
        import numpy as np
        cats = list(top.keys()); vals = list(top.values())
        y = np.arange(len(cats))
        fig = plt.figure(figsize=(8, 4.5))
        plt.barh(y, vals)
        plt.yticks(y, cats); plt.title("主要非依从原因"); plt.xlabel("次数")
        plt.tight_layout()
        p = assets_dir / "adherence_causes.png"
        plt.savefig(p, bbox_inches="tight"); plt.close(fig)
        charts["adherence_causes"] = _as_uri(p)
    med = [a for a in adherence if a.get('category') == '用药' and a.get('date')]
    med_dates = [m['date'] for m in med]
    def map_status(s): return 1 if s == '完全遵从' else (0.5 if s == '部分遵从' else 0)
    med_vals = [map_status(m.get('overall_status')) for m in med]
    if med_dates and med_vals:
        p = assets_dir / "med_adherence_trend.png"
        save_line_chart(med_dates, med_vals, "用药依从趋势（1/0.5/0）", p)
        charts["med_adherence_trend"] = _as_uri(p)
    total = len(adherence)
    compliant = sum(1 for a in adherence if a.get('overall_status') == '完全遵从')
    noncompliant = sum(1 for a in adherence if a.get('overall_status') == '不遵从')
    rate = f"{(compliant/total*100):.1f}%" if total else "0.0%"
    return {
        "charts": charts,
        "summary": {"total": total, "compliant": compliant, "noncompliant": noncompliant, "rate": rate}
    }

# =================== 生理数据图表 ===================
def plot_physio_report_dfmem(df_patient: pd.DataFrame, memory: dict, assets_dir: Path):
    charts = {}
    if "date" in df_patient.columns:
        dates = pd.to_datetime(df_patient["date"]).dt.strftime("%Y-%m-%d").tolist()
    else:
        dates = list(range(len(df_patient)))
    if set(["sbp","dbp"]).issubset(df_patient.columns):
        p = assets_dir / "bp_trend.png"
        save_trend_multi(dates, {
            "收缩压": df_patient["sbp"].tolist(),
            "舒张压": df_patient["dbp"].tolist()
        }, "既往血压变化记录", p)
        charts["bp_trend"] = _as_uri(p)
    if set(["fbg","ppg"]).issubset(df_patient.columns):
        p = assets_dir / "glucose_trend.png"
        save_trend_multi(dates, {
            "空腹血糖": df_patient["fbg"].tolist(),
            "餐后血糖": df_patient["ppg"].tolist()
        }, "既往血糖变化记录", p)
        charts["glucose_trend"] = _as_uri(p)
    cols = [c for c in ["hba1c","ldl","bmi","weight_kg","hr"] if c in df_patient.columns]
    if len(df_patient) >= 2 and cols:
        first = df_patient.iloc[0]
        last = df_patient.iloc[-1]
        cat_labels = {"hba1c":"HbA1c","ldl":"LDL-C","bmi":"BMI","weight_kg":"体重","hr":"心率"}
        cats = [cat_labels[c] for c in cols]
        vals_a = [float(first[c]) for c in cols]
        vals_b = [float(last[c]) for c in cols]
        p = assets_dir / "monthly_comparison.png"
        save_bar_compare(cats, vals_a, vals_b, "期初", "最近", "核心指标对比", p)
        charts["monthly_comparison"] = _as_uri(p)
    charts.update(build_adherence_stats(memory, assets_dir)["charts"])
    return charts

def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def pick_latest_json(dir_path: Path, suffix: str) -> Path|None:
    files = sorted([p for p in dir_path.glob(f"*{suffix}")], key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def find_memory_path_by_id(patient_id: str) -> Path:
    exact = MEMORY_DIR / f"{patient_id}_memory.json"
    if exact.exists(): return exact
    cands = sorted(MEMORY_DIR.glob(f"{patient_id}*_memory.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if cands: return cands[0]
    raise FileNotFoundError(f"未在 {MEMORY_DIR} 找到 {patient_id}_memory.json")

def load_physio_for_id(patient_id: str) -> pd.DataFrame:
    if not PHYSIO_CSV.exists():
        raise FileNotFoundError(f"缺少 CSV：{PHYSIO_CSV}")
    df = pd.read_csv(PHYSIO_CSV)
    if "patient_id" not in df.columns:
        raise ValueError(f"CSV 缺少列 patient_id：{PHYSIO_CSV}")
    dfi = df[df["patient_id"].astype(str) == str(patient_id)].copy()
    if dfi.empty:
        raise ValueError(f"CSV 中未找到 patient_id={patient_id} 的记录")
    if "date" in dfi.columns:
        dfi["date"] = pd.to_datetime(dfi["date"], errors="coerce")
        dfi = dfi.sort_values("date")
    return dfi

def build_monitoring_from_df(df_patient: pd.DataFrame) -> dict:
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

def compute_status(m: dict) -> dict:
    def _ok_bp(bp_txt: str):
        try:
            s, d = bp_txt.split(" ")[0].split("/")
            return int(s) < 140 and int(d) < 90
        except Exception:
            return False
    return {
        "bp": "达标" if _ok_bp(m.get("bp","—")) else ("—" if m.get("bp","—")=="—" else "未达标"),
        "bg": "达标" if m.get("bg","—")!="—" and float(m["bg"].split()[0]) < 7.0 else ("—" if m.get("bg","—")=="—" else "未达标"),
        "hba1c": "达标" if m.get("hba1c","—")!="—" and float(m["hba1c"].rstrip('%')) < 7.0 else ("—" if m.get("hba1c","—")=="—" else "未达标"),
        "ldl": "达标" if m.get("ldl","—")!="—" and float(m["ldl"].split()[0]) < 2.6 else ("—" if m.get("ldl","—")=="—" else "未达标"),
        "bmi": "达标" if m.get("bmi","—")!="—" and 18.5 <= float(m["bmi"].split()[0]) <= 24.9 else ("—" if m.get("bmi","—")=="—" else "未达标"),
        "hr": "达标" if m.get("hr","—")!="—" else "—",
        "kidney": "达标" if m.get("kidney","—")!="—" else "—",
    }

def build_visuals_markdown(adherence_charts: dict):
    lines = ["\n---\n## 附：依从性可视化"]
    if adherence_charts.get("adherence_trend"):
        lines.append(f"![各类别依从趋势]({adherence_charts['adherence_trend']})")
    if adherence_charts.get("adherence_causes"):
        lines.append(f"![主要非依从原因]({adherence_charts['adherence_causes']})")
    if adherence_charts.get("med_adherence_trend"):
        lines.append(f"![用药依从趋势]({adherence_charts['med_adherence_trend']})")
    return "\n\n".join(lines)

# =================== 主流程 ===================
def main():
    parser = argparse.ArgumentParser(description="按 patient_id 生成医生版/家属版 HTML 报告（无 PDF）")
    parser.add_argument("--id", help="患者唯一ID（= memory 文件名前缀，去掉 _memory.json）")
    args = parser.parse_args()

    # 选择 memory 文件（优先按ID，否则取最新）
    if args.id:
        mem_path = find_memory_path_by_id(args.id)
        patient_id = args.id
    else:
        mem_path = pick_latest_json(MEMORY_DIR, "_memory.json")
        if not mem_path:
            raise FileNotFoundError("data/output/memory 里未找到 *_memory.json")
        patient_id = mem_path.name.replace("_memory.json", "")

    # 对话文件可选
    dlg_path = DIALOGUE_DIR / f"{patient_id}_multiday.json"
    dialogues = load_json(dlg_path) if dlg_path.exists() else {}

    memory = load_json(mem_path)
    df_patient = load_physio_for_id(patient_id)

    # 基本信息
    basic = memory.get("basic_info", {})
    disease_info = memory.get("disease_info", {"primary_diseases": []})

    # 汇总处方药物注入
    try:
        _meds = build_current_medications(memory)
        disease_info["current_medications"] = _meds.get("list", [])
        disease_info["current_medications_text"] = _meds.get("text", "—")
    except Exception:
        disease_info["current_medications"] = []
        disease_info["current_medications_text"] = "—"
    try:
        for _d in disease_info.get("primary_diseases", []) or []:
            if isinstance(_d, dict) and "current_medications_text" not in _d:
                _d["current_medications_text"] = disease_info.get("current_medications_text", "—")
    except Exception:
        pass

    monitoring = build_monitoring_from_df(df_patient)
    status = compute_status(monitoring)

    targets = memory.get("targets", {
        "bp": "< 140/90 mmHg",
        "bg": "< 7.0 mmol/L（空腹）",
        "hba1c": "< 7.0%",
        "ldl": "< 2.6 mmol/L",
        "bmi": "18.5–24.9 kg/m²",
        "hr": "60–100 bpm",
        "kidney": "eGFR ≥ 60 ml/min/1.73m²",
    })

    if ("date" in df_patient.columns) and (df_patient["date"].notna().any()):
        period_start = pd.to_datetime(df_patient["date"].min()).date().isoformat()
        period_end   = pd.to_datetime(df_patient["date"].max()).date().isoformat()
        report_period = f"{period_start} 至 {period_end}"
    else:
        report_period = "—"

    # 规范化块
    adherence_std = build_adherence(memory)
    lifestyle_std = build_lifestyle(memory)
    app_overview  = build_app(memory, dialogues)
    tips_block    = build_tips(memory, monitoring, status, adherence_std)

    ctx_base = {
        "report": {
            "period": report_period,
            "date": datetime.now().strftime("%Y-%m-%d")
        },
        "patient": {
            "name": basic.get("name", patient_id),
            "gender": basic.get("sex", "—"),
            "age": basic.get("age", "—"),
            "occupation": basic.get("occupation", "—"),
            "education": basic.get("education", "—"),
            "family": basic.get("living_situation", "—"),
            "phone": basic.get("contact_phone", "—"),
            "allergies": "、".join(disease_info.get("allergies", [])) or "未记录",
            "history": "、".join([d.get("disease_name","") for d in disease_info.get("primary_diseases",[])]) or "未记录",
            "support": basic.get("support", "—"),
            "current_medications": disease_info.get("current_medications_text", "—"),
        },
        "disease_info": disease_info,
        "monitoring": monitoring,
        "targets": targets,
        "status": status,
        "adherence": adherence_std,
        "lifestyle": lifestyle_std,
        "app": app_overview,
        "tips": tips_block,
        "ai": memory.get("ai", {}),
        "references": memory.get("references", []),
    }

    charts_physio = plot_physio_report_dfmem(df_patient, memory, ASSETS_DIR)
    stats_adherence = build_adherence_stats(memory, ASSETS_DIR)
    ctx_base["charts"] = {**charts_physio, **stats_adherence.get("charts", {})}

    # LLM 综合分析（基于标准化依从性）
    ctx_base["ai"] = generate_ai_analysis(ctx_base["monitoring"], ctx_base["adherence"])

    # 模板
    doctor_tpl_path = next((p for p in [TPL_DIR/"doctor_template_slim.md", TPL_DIR/"doctor_template.md"] if p.exists()), None)
    family_tpl_path = TPL_DIR/"family_template.md"
    if not doctor_tpl_path or not family_tpl_path.exists():
        raise FileNotFoundError("缺少模板：doctor_template_slim.md(or doctor_template.md) / family_template.md")

    env = Environment(loader=BaseLoader(), autoescape=False, undefined=ChainableUndefined)
    doc_tpl = doctor_tpl_path.read_text(encoding="utf-8")
    fam_tpl = family_tpl_path.read_text(encoding="utf-8")

    doc_md = env.from_string(doc_tpl).render(**ctx_base)
    fam_md = env.from_string(fam_tpl).render(**ctx_base)

    visuals_md = build_visuals_markdown(stats_adherence["charts"])
    doc_md += visuals_md
    fam_md += visuals_md

    doc_html = markdown(doc_md, extensions=["tables", "fenced_code"])
    fam_html = markdown(fam_md, extensions=["tables", "fenced_code"])

    def build_html_shell(title: str, content: str, patient_id: str = "unknown") -> str:
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
:root {{
    --fg:#222; --fg-soft:#444; --bg:#fff; --muted:#888;
    --pri:#2e7d32; --pri-weak:#e9f5eb; --warn:#c62828; --bar:#0f766e;
    --card:#f6f7f9; --border:#ddd; --btn:#0ea5e9; --btn-hover:#0284c7;
}}
html,body {{ margin:0; padding:0; background:var(--bg); color:var(--fg); font-family:"Noto Sans CJK SC","Microsoft YaHei","PingFang SC",Arial; }}
body {{ font-size:14.5px; line-height:1.6; }}
.page-container {{ max-width:1100px; margin:0 auto; padding:16px 20px 80px; }}
.meta {{ color:var(--fg-soft); margin-bottom:12px; }}
h1,h2,h3 {{ color:#111; margin:.7em 0 .45em; position:relative; }}
table {{ border-collapse:collapse; width:100%; margin:.4em 0 .8em; }}
th,td {{ border:1px solid #ccc; padding:6px 8px; vertical-align:top; }}
th {{ background:#f6f7f9; }}
blockquote {{ color:#555; margin:.6em 0; padding-left:.8em; border-left:3px solid #ddd; }}
img {{ max-width:100%; }}

/* 顶部工具条 */
.anno-toolbar {{
    position:fixed; left:50%; transform:translateX(-50%);
    bottom:16px; z-index:9999; display:flex; gap:8px; align-items:center;
    background:linear-gradient(90deg,#0ea5e9,#06b6d4); color:#fff;
    padding:10px 12px; border-radius:14px; box-shadow:0 8px 20px rgba(0,0,0,.15);
}}
.anno-toolbar button, .anno-toolbar label.btn {{
    appearance:none; border:0; border-radius:10px; padding:8px 10px; cursor:pointer; font-weight:600;
    background:#ffffff; color:#0b3b48; transition:all .15s ease; box-shadow:0 2px 6px rgba(0,0,0,.12);
}}
.anno-toolbar button:hover, .anno-toolbar label.btn:hover {{ transform:translateY(-1px); }}
.anno-toolbar .sep {{ width:1px; height:20px; background:rgba(255,255,255,.6); margin:0 4px; }}
.hidden-input {{ display:none; }}

/* 批注按钮：批注模式下显示 */
.add-note-btn {{
    display:none; position:absolute; right:-4px; top:50%; transform:translate(100%,-50%);
    background:var(--btn); color:#fff; border:0; padding:3px 8px; border-radius:10px; font-size:12px; cursor:pointer;
}}
.add-note-btn:hover {{ background:var(--btn-hover); }}

/* 章节小面板（常显交互控件） */
.section-tools {{
    display:inline-flex; gap:8px; align-items:center; margin-left:8px; transform:translateY(-1px);
}}
.section-tools select, .section-tools input[type="checkbox"] {{
    font-size:12px; padding:2px 6px;
}}
.section-tools .chip {{
    font-size:12px; padding:2px 8px; border:1px solid var(--border); border-radius:10px; background:#fff;
}}
.section-tools .btn-mini {{
    font-size:12px; padding:2px 8px; border:1px solid var(--border); border-radius:10px; background:#fff; cursor:pointer;
}}
.section-tools .btn-mini:hover {{ background:#f1f5f9; }}

/* 批注卡片 */
.anno-card {{
    background:var(--card); border:1px solid var(--border); border-left:4px solid var(--bar);
    border-radius:12px; padding:10px; margin:8px 0 12px;
}}
.anno-card .anno-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; color:var(--fg-soft); font-size:12px; }}
.anno-card .anno-body[contenteditable="true"] {{
    min-height:48px; padding:6px 8px; border-radius:8px; background:#fff; border:1px dashed #cbd5e1;
    outline:none;
}}
.anno-card .anno-actions {{ text-align:right; margin-top:6px; }}
.anno-card .anno-actions button {{
    background:#fff; border:1px solid #cbd5e1; border-radius:8px; padding:4px 8px; cursor:pointer; margin-left:6px;
}}
.anno-card .anno-actions button:hover {{ background:#f1f5f9; }}

/* 全局批注面板 */
.global-anno {{
    background:#fff; border:1px solid var(--border); border-radius:14px; padding:12px; margin:10px 0 18px;
    box-shadow:0 2px 10px rgba(0,0,0,.06);
}}
.global-anno h3 {{ margin-top:0; }}
.global-anno .area {{ width:100%; min-height:68px; resize:vertical; padding:8px; border-radius:10px; border:1px solid #cbd5e1; }}
.global-anno .actions {{ text-align:right; margin-top:6px; }}
.muted {{ color:var(--muted); font-size:12px; }}

/* 打印：隐藏工具条与批注按钮 */
@media print {{
    .anno-toolbar {{ display:none!important; }}
    .add-note-btn {{ display:none!important; }}
    .page-container {{ padding-bottom:0; }}
}}
</style>
</head>
<body>
<div class="page-container" data-patient-id="{patient_id}">
    <div class="meta">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>

    <!-- 全局批注 -->
    <section class="global-anno" id="global-anno">
      <h3>📝 全局批注（医生）</h3>
      <textarea class="area" id="globalAnnoArea" placeholder="在此填写整体意见；支持导出/导入与自动保存。"></textarea>
      <div class="actions muted">内容自动保存到浏览器（仅本机）。</div>
    </section>

    {content}
</div>

<!-- 底部批注工具条 -->
<div class="anno-toolbar" id="annoToolbar">
    <button id="toggleAnno">关闭批注模式</button>
    <div class="sep"></div>
    <button id="exportAnno">导出批注与交互数据</button>
    <label class="btn" for="importAnnoInput">导入数据</label>
    <input id="importAnnoInput" class="hidden-input" type="file" accept="application/json" />
    <button id="clearAnno">清空本地数据</button>
    <div class="sep"></div>
    <button id="printView">打印友好</button>
</div>

<script>
(() => {{
const patientId = document.querySelector('.page-container')?.dataset?.patientId || 'unknown';
const LS_ANNOTATIONS = `report-annotations::${{patientId}}`;
const LS_GLOBAL = `report-annotations-global::${{patientId}}`;
const LS_INTERACTIONS = `report-interactions::${{patientId}}`;
let annoMode = true;

function nowStr() {{
  const d = new Date();
  const pad = n => (n<10? '0'+n : ''+n);
  return `${{d.getFullYear()}}-${{pad(d.getMonth()+1)}}-${{pad(d.getDate())}} ${{pad(d.getHours())}}:${{pad(d.getMinutes())}}`;
}}

function loadJSON(key, def) {{
  try {{ return JSON.parse(localStorage.getItem(key) || JSON.stringify(def)); }}
  catch {{ return def; }}
}}
function saveJSON(key, val) {{
  localStorage.setItem(key, JSON.stringify(val || {{}}));
}}

function loadAnnotations() {{ return loadJSON(LS_ANNOTATIONS, {{}}); }}
function saveAnnotations(data) {{ saveJSON(LS_ANNOTATIONS, data); }}
function loadGlobal() {{ return localStorage.getItem(LS_GLOBAL) || ''; }}
function saveGlobal(val) {{ localStorage.setItem(LS_GLOBAL, val || ''); }}
function loadInteracts() {{ return loadJSON(LS_INTERACTIONS, {{}}); }}
function saveInteracts(obj) {{ saveJSON(LS_INTERACTIONS, obj); }}

/* ====== 批注基础 ====== */
function setupSectionAnchors() {{
  const headers = document.querySelectorAll('h1, h2, h3');
  headers.forEach((h, idx) => {{
    const secId = h.id || `sec-${{idx}}`;
    h.id = secId;

    // 批注按钮（需开启批注模式才显示）
    const btn = document.createElement('button');
    btn.className = 'add-note-btn';
    btn.textContent = '➕ 批注';
    btn.addEventListener('click', () => createNoteCard(secId));
    h.appendChild(btn);
  }});
}}

function refreshAnnoButtons() {{
  const show = annoMode ? 'inline-block' : 'none';
  document.querySelectorAll('.add-note-btn').forEach(b => b.style.display = show);
}}

function renderNotes() {{
  const store = loadAnnotations();
  Object.entries(store).forEach(([secId, arr]) => {{
    const anchor = document.getElementById(secId);
    if (!anchor) return;
    arr.forEach(n => insertNoteCardAfter(anchor, n));
  }});
}}

function createNoteCard(secId) {{
  const payload = {{ id: `n-${{Date.now()}}`, ts: nowStr(), html: '' }};
  const store = loadAnnotations();
  if (!store[secId]) store[secId] = [];
  store[secId].push(payload);
  saveAnnotations(store);
  const anchor = document.getElementById(secId);
  if (anchor) insertNoteCardAfter(anchor, payload, true);
}}

function insertNoteCardAfter(anchorEl, note, focus=false) {{
  const card = document.createElement('div');
  card.className = 'anno-card';
  card.dataset.noteId = note.id;
  card.dataset.secId = anchorEl.id;

  card.innerHTML = `
    <div class="anno-head">
      <div>章节：<code>${{anchorEl.textContent.replace('➕ 批注','').trim()}}</code></div>
      <div>时间：${{note.ts}}</div>
    </div>
    <div class="anno-body" contenteditable="true" spellcheck="false">${{note.html || ''}}</div>
    <div class="anno-actions">
      <button data-act="del">删除</button>
    </div>
  `;

  const body = card.querySelector('.anno-body');
  body.addEventListener('input', () => {{
    const store = loadAnnotations();
    const list = store[card.dataset.secId] || [];
    const item = list.find(x => x.id === card.dataset.noteId);
    if (item) {{ item.html = body.innerHTML; saveAnnotations(store); }}
  }});
  card.querySelector('[data-act="del"]').addEventListener('click', () => {{
    const store = loadAnnotations();
    const list = store[card.dataset.secId] || [];
    const idx = list.findIndex(x => x.id === card.dataset.noteId);
    if (idx >= 0) list.splice(idx, 1);
    saveAnnotations(store);
    card.remove();
  }});
  if (anchorEl.nextSibling) {{
    anchorEl.parentNode.insertBefore(card, anchorEl.nextSibling);
  }} else {{
    anchorEl.parentNode.appendChild(card);
  }}
  if (focus) body.focus();
}}

/* ====== 章节交互（按内容类型合理分配） ====== */
const SectionKindMap = [
  {{ key: 'disease', includes: ['主要疾病诊断', '治疗', '诊断及治疗'] }},
  {{ key: 'monitor', includes: ['核心监测指标','监测','指标'] }},
  {{ key: 'adherence', includes: ['依从','依从性','依從'] }},
  {{ key: 'lifestyle', includes: ['生活方式','生活','干预'] }},
  {{ key: 'tips', includes: ['建议','提示','随访建议','治疗建议'] }},
  {{ key: 'ai', includes: ['AI','人工智能','综合分析','总结','风险评估'] }},
];

function detectKind(titleText) {{
  const t = (titleText || '').replace(/\\s+/g,'');
  for (const m of SectionKindMap) {{
    if (m.includes.some(k => t.includes(k))) return m.key;
  }}
  return null;
}}

function mountSectionTools() {{
  const headers = document.querySelectorAll('h1, h2, h3');
  const store = loadInteracts();
  headers.forEach(h => {{
    const kind = detectKind(h.textContent);
    if (!kind) return;
    const secId = h.id;
    const wrap = document.createElement('span');
    wrap.className = 'section-tools';

    if (kind === 'disease') {{
      wrap.innerHTML = `
        <span class="chip">处置：</span>
        <select data-k="disease.plan">
          <option value="">无</option>
          <option>简化</option>
          <option>加强</option>
          <option>改药</option>
          <option>会诊</option>
        </select>
        <label class="chip"><input type="checkbox" data-k="disease.medChecked"> 已核对用药</label>
      `;
    }}

    if (kind === 'monitor') {{
      wrap.innerHTML = `
        <span class="chip">复查安排：</span>
        <select data-k="monitor.recheck">
          <option value="">按需要</option>
          <option>1周</option>
          <option>2周</option>
          <option>4周</option>
        </select>
        <button class="btn-mini" data-act="mark-recheck">记为需复查</button>
      `;
    }}

    if (kind === 'adherence') {{
      wrap.innerHTML = `
        <label class="chip"><input type="checkbox" data-k="adherence.follow"> 需随访</label>
        <span class="chip">周期：</span>
        <select data-k="adherence.period">
          <option>1周</option><option>2周</option><option selected>4周</option>
        </select>
        <button class="btn-mini" data-act="make-follow">记录随访任务</button>
      `;
    }}

    if (kind === 'lifestyle') {{
      wrap.innerHTML = `
        <span class="chip">生活方式指导：</span>
        <label class="chip"><input type="checkbox" data-k="life.diet"> 饮食</label>
        <label class="chip"><input type="checkbox" data-k="life.exercise"> 运动</label>
        <br><span style="margin-left:20px;"></span>
        <label class="chip"><input type="checkbox" data-k="life.sleep"> 睡眠</label>
        <label class="chip"><input type="checkbox" data-k="life.psy"> 心理</label>
        <button class="btn-mini" data-act="lifestyle-complete">完成教育</button>
      `;
    }}

    if (kind === 'tips') {{
      wrap.innerHTML = `
        <span class="chip">建议采纳情况：</span>
        <select data-k="tips.overall">
          <option value="">总体评价</option>
          <option>完全采纳</option>
          <option>部分采纳</option>
          <option>需要修改</option>
          <option>重新制定</option>
        </select>
        <br><span style="margin-left:20px;"></span>
        <label class="chip">重点关注：</label>
        <select data-k="tips.focus">
          <option value="">选择重点</option>
          <option>用药依从性</option>
          <option>血压监测</option>
          <option>血糖控制</option>
          <option>生活方式</option>
        </select>
        <button class="btn-mini" data-act="create-plan">制定随访计划</button>
      `;
    }}

    if (kind === 'ai') {{
      wrap.innerHTML = `
        <span class="chip">AI分析确认：</span>
        <select data-k="ai.summary">
          <option value="">总结</option>
          <option>同意</option>
          <option>需修改</option>
        </select>
        <select data-k="ai.risk">
          <option value="">风险评估</option>
          <option>同意</option>
          <option>需修改</option>
        </select>
        <select data-k="ai.recommendations">
          <option value="">建议</option>
          <option>同意</option>
          <option>需修改</option>
        </select>
        <button class="btn-mini" data-act="ai-approve">确认分析</button>
      `;
    }}

    // 读存储并回填
    wrap.querySelectorAll('select, input[type="checkbox"]').forEach(el => {{
      const k = `${{secId}}::${{el.dataset.k}}`;
      const v = store[k];
      if (el.tagName === 'SELECT') {{ if (v !== undefined) el.value = v; }}
      else if (el.type === 'checkbox') {{ el.checked = !!v; }}
      el.addEventListener('change', () => {{
        const cur = loadInteracts();
        cur[k] = (el.type === 'checkbox') ? el.checked : el.value;
        saveInteracts(cur);
      }});
    }});

    wrap.querySelectorAll('[data-act="mark-recheck"]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const cur = loadInteracts();
        cur[`${{secId}}::monitor.needRecheck`] = true;
        cur[`${{secId}}::monitor.markTs`] = nowStr();
        saveInteracts(cur);
        btn.textContent = '已标记';
        btn.disabled = true;
      }});
    }});
    wrap.querySelectorAll('[data-act="make-follow"]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const cur = loadInteracts();
        cur[`${{secId}}::adherence.taskTs`] = nowStr();
        saveInteracts(cur);
        btn.textContent = '已记录';
        btn.disabled = true;
      }});
    }});
    wrap.querySelectorAll('[data-act="lifestyle-complete"]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const cur = loadInteracts();
        cur[`${{secId}}::lifestyle.completeTs`] = nowStr();
        saveInteracts(cur);
        btn.textContent = '已完成';
        btn.disabled = true;
      }});
    }});
    wrap.querySelectorAll('[data-act="create-plan"]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const cur = loadInteracts();
        cur[`${{secId}}::tips.planTs`] = nowStr();
        saveInteracts(cur);
        btn.textContent = '已制定';
        btn.disabled = true;
      }});
    }});
    wrap.querySelectorAll('[data-act="ai-approve"]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const cur = loadInteracts();
        cur[`${{secId}}::ai.approveTs`] = nowStr();
        saveInteracts(cur);
        btn.textContent = '已确认';
        btn.disabled = true;
      }});
    }});

    h.appendChild(wrap);
  }});
}}

/* ====== 工具条 ====== */
function setupToolbar() {{
  const $toggle = document.getElementById('toggleAnno');
  const $export = document.getElementById('exportAnno');
  const $import = document.getElementById('importAnnoInput');
  const $clear  = document.getElementById('clearAnno');
  const $print  = document.getElementById('printView');
  const $global = document.getElementById('globalAnnoArea');

  // 初始化全局批注
  $global.value = loadGlobal();
  $global.addEventListener('input', () => saveGlobal($global.value));

  // 设置初始按钮文本
  $toggle.textContent = annoMode ? '关闭批注模式' : '开启批注模式';

  $toggle.addEventListener('click', () => {{
    annoMode = !annoMode;
    $toggle.textContent = annoMode ? '关闭批注模式' : '开启批注模式';
    refreshAnnoButtons();
  }});

  $export.addEventListener('click', () => {{
    const data = {{
      patient_id: patientId,
      exported_at: nowStr(),
      global: $global.value || '',
      sections: loadAnnotations(),
      interactions: loadInteracts()
    }};
    const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `annotations_${{patientId}}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }});

  $import.addEventListener('change', (e) => {{
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {{
      try {{
        const data = JSON.parse(reader.result);
        if (data?.global !== undefined) saveGlobal(data.global);
        if (data?.sections) saveAnnotations(data.sections);
        if (data?.interactions) saveInteracts(data.interactions);
        location.reload();
      }} catch (err) {{
        alert('导入失败：JSON格式不正确');
      }}
    }};
    reader.readAsText(f, 'utf-8');
    e.target.value = '';
  }});

  $clear.addEventListener('click', () => {{
    if (!confirm('确定清空所有本地数据吗？仅清除此患者的本机数据。')) return;
    localStorage.removeItem(LS_ANNOTATIONS);
    localStorage.removeItem(LS_GLOBAL);
    localStorage.removeItem(LS_INTERACTIONS);
    location.reload();
  }});

  $print.addEventListener('click', () => window.print());
}}

/* ====== 初始化 ====== */
setupSectionAnchors();     // 安插批注按钮
mountSectionTools();       // 按章节类型挂载交互控件（常显）
renderNotes();             // 恢复批注卡片
setupToolbar();            // 工具条
refreshAnnoButtons();      // 默认批注按钮隐藏

}})();
</script>
</body>
</html>"""

    doc_html_shell = build_html_shell("医生版报告", doc_html, patient_id=patient_id)
    fam_html_shell = build_html_shell("家属版报告", fam_html, patient_id=patient_id)

    # 输出 HTML（不再生成 PDF）
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR/"doctor_report_demo.html").write_text(doc_html_shell, encoding="utf-8")
    (OUT_DIR/"family_report_demo.html").write_text(fam_html_shell, encoding="utf-8")

    s = stats_adherence["summary"]
    print(f"[概要] 依从记录：{s['total']} 条，完全依从：{s['compliant']}，不遵从：{s['noncompliant']}，完全依从率：{s['rate']}")
    print(f"[完成] HTML 报告已输出到：{OUT_DIR}")

if __name__ == "__main__":
    main()
