# -*- coding: utf-8 -*-
"""
图表生成器 - 负责生成各种可视化图表
"""

from pathlib import Path
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB']
plt.rcParams['axes.unicode_minus'] = False     # 解决负号'-'显示为方块的问题


# from matplotlib import font_manager


# def check_chinese_fonts():
#     """检查系统中是否有中文字体"""
#     print("\n======== 开始在 Matplotlib 的字体列表中搜索中文字体 ========")

#     found_fonts = []
#     # 遍历 Matplotlib 能找到的所有字体
#     for font in font_manager.fontManager.ttflist:
#         # 检查一些常见的中文字体名称关键词
#         # Linux上常见的中文字体通常包含 'ukai', 'uming', 'wqy', 'firefly' 等
#         keywords = ['ukai', 'uming', 'wqy', 'firefly', 'droid sans fallback', 'source han', 
#                     'PingFang', 'Song', 'Hei', 'Kai', 'Yuan', 'Sans']
#         if any(keyword.lower() in font.name.lower() for keyword in keywords):
#             found_fonts.append(font.name)

#     if found_fonts:
#         print("\n[成功] 在您的 Linux 环境中找到了以下可能支持中文的字体:")
#         # 排序并打印所有找到的字体
#         for font_name in sorted(list(set(found_fonts))):
#             print(f"  - {font_name}")
#         print("\n[下一步] 请从上面的列表中选择一个看起来最像中文字体的名字（比如包含 'uming' 或 'wqy'），然后按照第二步的指示修改您的代码。")
#     else:
#         print("\n[失败] 抱歉，在您的 Matplotlib 环境中没有找到任何常见的中文字体。")

#     print("\n======================= 搜索结束 =======================")
#     return found_fonts


def _config_chinese_font():
    """配置中文字体"""
    zh = None
    for f in font_manager.fontManager.ttflist:
        if 'SimHei' in f.name or 'Microsoft YaHei' in f.name:
            zh = f.name
            break
    if zh:
        plt.rcParams['font.sans-serif'] = [zh]
    plt.rcParams['axes.unicode_minus'] = False


def _as_uri(p: Path, out_dir: Path) -> str:
    """将路径转换为相对URI"""
    try:
        if p and p.exists():
            return str(p.relative_to(out_dir).as_posix())
        return ""
    except Exception:
        return p.name if p and p.exists() else ""


def save_line_chart(dates, values, title, output_path):
    """保存折线图"""
    _config_chinese_font()
    plt.figure(figsize=(9, 4))
    plt.plot(dates, values, marker='o')
    plt.title(title)
    plt.xlabel('日期')
    plt.ylabel('数值')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def save_bar_compare(categories, vals_a, vals_b, label_a, label_b, title, output_path):
    """保存对比柱状图"""
    _config_chinese_font()
    x = np.arange(len(categories))
    width = 0.38
    plt.figure(figsize=(8, 4.5))
    plt.bar(x - width/2, vals_a, width, label=label_a)
    plt.bar(x + width/2, vals_b, width, label=label_b)
    plt.xticks(x, categories, rotation=0)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def save_trend_multi(dates, series_dict, title, output_path):
    """保存多系列趋势图"""
    _config_chinese_font()
    plt.figure(figsize=(10, 5))
    for name, ys in series_dict.items():
        plt.plot(dates, ys, marker='o', label=name)
    plt.title(title)
    plt.xlabel('日期')
    plt.ylabel('数值/标记')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def generate_adherence_charts(memory: dict, assets_dir: Path, out_dir: Path) -> dict:
    """生成依从性相关图表"""
    adherence = memory.get('adherence_history', []) or []
    charts = {}
    
    # 1. 各类别依从趋势图
    dates_set = set()
    cat_date_counts = defaultdict(lambda: defaultdict(int))
    
    for a in adherence:
        date = a.get('date')
        cat = a.get('category', '其他')
        if date:
            dates_set.add(date)
            cat_date_counts[cat][date] += 1
    
    dates = sorted(dates_set)
    series = {cat: [cat_date_counts[cat].get(d, 0) for d in dates] 
              for cat in cat_date_counts}
    
    if dates and series:
        p = assets_dir / "adherence_trend.png"
        save_trend_multi(dates, series, "各类别依从趋势", p)
        charts["adherence_trend"] = _as_uri(p, out_dir)
    
    # 2. 主要非依从原因图
    causes = defaultdict(int)
    for a in adherence:
        if a.get('overall_status') != '完全遵从':
            reason = a.get('reason', '其他')
            causes[reason] += 1
    
    if causes:
        top = dict(sorted(causes.items(), key=lambda x: x[1], reverse=True)[:5])
        _config_chinese_font()
        cats = list(top.keys())
        vals = list(top.values())
        y = np.arange(len(cats))
        
        fig = plt.figure(figsize=(8, 4.5))
        plt.barh(y, vals)
        plt.yticks(y, cats)
        plt.title("主要非依从原因")
        plt.xlabel("次数")
        plt.tight_layout()
        
        p = assets_dir / "adherence_causes.png"
        plt.savefig(p, bbox_inches="tight")
        plt.close(fig)
        charts["adherence_causes"] = _as_uri(p, out_dir)
    
    # 3. 用药依从趋势图
    med = [a for a in adherence if a.get('category') == '用药' and a.get('date')]
    med_dates = [m['date'] for m in med]
    
    def map_status(s): 
        return 1 if s == '完全遵从' else (0.5 if s == '部分遵从' else 0)
    
    med_vals = [map_status(m.get('overall_status')) for m in med]
    
    if med_dates and med_vals:
        p = assets_dir / "med_adherence_trend.png"
        save_line_chart(med_dates, med_vals, "用药依从趋势（1/0.5/0）", p)
        charts["med_adherence_trend"] = _as_uri(p, out_dir)
    
    return charts


def generate_physio_charts(df_patient: pd.DataFrame, assets_dir: Path, out_dir: Path) -> dict:
    """生成生理数据图表"""
    charts = {}
    
    # 准备日期数据
    if "date" in df_patient.columns:
        dates = pd.to_datetime(df_patient["date"]).dt.strftime("%Y-%m-%d").tolist()
    else:
        dates = list(range(len(df_patient)))
    
    # 1. 血压趋势图
    if set(["sbp", "dbp"]).issubset(df_patient.columns):
        p = assets_dir / "bp_trend.png"
        save_trend_multi(dates, {
            "收缩压": df_patient["sbp"].tolist(),
            "舒张压": df_patient["dbp"].tolist()
        }, "既往血压变化记录", p)
        charts["bp_trend"] = _as_uri(p, out_dir)
    
    # 2. 血糖趋势图
    if set(["fbg", "ppg"]).issubset(df_patient.columns):
        p = assets_dir / "glucose_trend.png"
        save_trend_multi(dates, {
            "空腹血糖": df_patient["fbg"].tolist(),
            "餐后血糖": df_patient["ppg"].tolist()
        }, "既往血糖变化记录", p)
        charts["glucose_trend"] = _as_uri(p, out_dir)
    
    # 3. 核心指标对比图
    cols = [c for c in ["hba1c", "ldl", "bmi", "weight_kg", "hr"] 
            if c in df_patient.columns]
    
    if len(df_patient) >= 2 and cols:
        first = df_patient.iloc[0]
        last = df_patient.iloc[-1]
        cat_labels = {
            "hba1c": "HbA1c", 
            "ldl": "LDL-C", 
            "bmi": "BMI", 
            "weight_kg": "体重", 
            "hr": "心率"
        }
        cats = [cat_labels[c] for c in cols]
        vals_a = [float(first[c]) for c in cols]
        vals_b = [float(last[c]) for c in cols]
        
        p = assets_dir / "monthly_comparison.png"
        save_bar_compare(cats, vals_a, vals_b, "期初", "最近", "核心指标对比", p)
        charts["monthly_comparison"] = _as_uri(p, out_dir)
    
    return charts

