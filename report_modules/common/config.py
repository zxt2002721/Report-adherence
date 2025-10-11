# -*- coding: utf-8 -*-
"""
配置文件 - 存放路径配置和常量
"""

from pathlib import Path
from openai import OpenAI

# ======================== 可配置路径 ========================
# TPL_DIR = Path("data/template")
BASE_DIR = Path(__file__).resolve().parent.parent # 假设config.py在项目根目录的子目录中
MEMORY_DIR = Path("data/output/memory")
DIALOGUE_DIR = Path("data/output/dialogue_data")
PHYSIO_CSV = Path("data/output/patient_physio_timeseries.csv")

OUT_DIR = Path("report/output")
ASSETS_DIR = OUT_DIR / "assets"

# 确保输出目录存在
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ======================== AI 客户端配置 ========================
# client = OpenAI(
#     api_key="sk-0bf69a2ea8374928ba7cadbf998f07ae",
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
# )
# client = OpenAI(
#     api_key="sk-4e7b9c2d8f3a4b1c9e6d7f0a2b3c4d5e6f7a8b9c0d1f2f3",
#     base_url="http://127.0.0.1:52345/v1"  # 如果用 https 或域名，改成对应地址
# )


client = OpenAI(
    api_key="sk-0bf69a2ea8374928ba7cadbf998f07ae",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ======================== 目标值配置 ========================
DEFAULT_TARGETS = {
    "bp": "< 140/90 mmHg",
    "bg": "< 7.0 mmol/L（空腹）",
    "hba1c": "< 7.0%",
    "ldl": "< 2.6 mmol/L",
    "bmi": "18.5–24.9 kg/m²",
    "hr": "60–100 bpm",
    "kidney": "eGFR ≥ 60 ml/min/1.73m²",
}
