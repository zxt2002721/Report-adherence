# -*- coding: utf-8 -*-
"""
配置文件 - 存放路径配置和常量
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from openai import OpenAI


def _resolve_first_existing(*candidates: str) -> Path:
    """Return the first existing path from candidates, fallback to the first candidate."""
    for candidate in candidates:
        path_obj = Path(candidate)
        if path_obj.exists():
            return path_obj
    return Path(candidates[0])


# ======================== 可配置路径 ========================
# TPL_DIR = Path("data/template")
BASE_DIR = Path(__file__).resolve().parent.parent  # 假设config.py在项目根目录的子目录中

# LLM 增强数据目录优先，保留旧版作为回退
MEMORY_DIR = _resolve_first_existing(
    "data/output_llm_enhanced/memory_data",
    "data/output/memory",
)
DIALOGUE_DIR = _resolve_first_existing(
    "data/output_llm_enhanced/dialogue_data",
    "data/output/dialogue_data",
)
PHYSIO_CSV = _resolve_first_existing(
    "data/output_llm_enhanced/patient_physio_timeseries.csv",
    "data/output/patient_physio_timeseries.csv",
)

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


@dataclass
class _UrgencyContext:
    """Minimal structure extracted from prompt for offline heuristic assessment."""

    patient: Dict[str, object]
    monitoring: Dict[str, str]
    adherence: Dict[str, object]
    lifestyle: Dict[str, object]
    tasks: List[Dict[str, object]]
    task_progress: List[Dict[str, object]]


def _parse_first_number(text: str) -> float | None:
    """Extract first numeric value from a text block."""

    if not isinstance(text, str):
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def _extract_json_blocks(prompt: str) -> List[dict]:
    """Pull JSON objects from ```json blocks inside the prompt."""

    blocks: List[dict] = []
    for chunk in re.findall(r"```json\s*([\s\S]*?)```", prompt):
        try:
            blocks.append(json.loads(chunk))
        except json.JSONDecodeError:
            blocks.append({})
    return blocks


def _build_offline_context(prompt: str) -> _UrgencyContext:
    """Build structured context from the prompt for heuristic fallback."""

    blocks = _extract_json_blocks(prompt)
    while len(blocks) < 6:
        blocks.append({})
    patient, monitoring, adherence, lifestyle, tasks, task_progress = blocks[:6]
    return _UrgencyContext(
        patient=patient,
        monitoring=monitoring,
        adherence=adherence,
        lifestyle=lifestyle,
        tasks=tasks if isinstance(tasks, list) else [],
        task_progress=task_progress if isinstance(task_progress, list) else [],
    )


def generate_urgency_assessment_from_context(
    patient: Dict[str, object] | None,
    monitoring: Dict[str, object] | None,
    adherence: Dict[str, object] | None,
    lifestyle: Dict[str, object] | None = None,
    tasks: List[Dict[str, object]] | None = None,
    task_progress: List[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    """
    Build a deterministic urgency assessment without calling external LLM services.

    Args:
        patient: Basic patient information.
        monitoring: Aggregated vital signs readings.
        adherence: Medication/monitoring adherence structure.
        lifestyle: Lifestyle snapshot.
        tasks: Compliance task definitions.
        task_progress: Historical execution records for tasks.

    Returns:
        Dict[str, object]: Parsed assessment dictionary compliant with UrgencyAssessment schema.
    """

    ctx = _UrgencyContext(
        patient=patient or {},
        monitoring=monitoring or {},
        adherence=adherence or {},
        lifestyle=lifestyle or {},
        tasks=tasks or [],
        task_progress=task_progress or [],
    )
    raw_json = _heuristic_urgency_response(ctx)
    return json.loads(raw_json)


def _heuristic_urgency_response(ctx: _UrgencyContext) -> str:
    """Generate a deterministic urgency assessment JSON via heuristics."""

    issues: List[str] = []
    urgent_signals: List[str] = []
    score = 35
    task_assessment: List[Dict[str, object]] = []

    bp_text = ctx.monitoring.get("bp") if isinstance(ctx.monitoring, dict) else None
    sbp = dbp = None
    if isinstance(bp_text, str) and "/" in bp_text:
        try:
            head = bp_text.split()[0]
            sbp, dbp = [float(part) for part in head.split("/")[:2]]
        except Exception:
            sbp = dbp = None
    if sbp is not None and dbp is not None:
        if sbp >= 180 or dbp >= 110 or sbp < 90 or dbp < 60:
            urgent_signals.append("血压严重异常")
            score = max(score, 82)
        elif sbp >= 160 or dbp >= 100:
            issues.append("血压显著升高")
            score = max(score, 68)
        elif sbp >= 140 or dbp >= 90:
            issues.append("血压轻度升高")
            score = max(score, 55)

    glucose_val = _parse_first_number(ctx.monitoring.get("bg")) if isinstance(ctx.monitoring, dict) else None
    if glucose_val is not None:
        if glucose_val >= 15 or glucose_val < 3.9:
            urgent_signals.append("血糖处于危险范围")
            score = max(score, 85)
        elif glucose_val >= 10:
            issues.append("血糖控制欠佳")
            score = max(score, 65)
        elif glucose_val >= 7:
            issues.append("血糖偏高")
            score = max(score, 55)

    hba1c_val = _parse_first_number(ctx.monitoring.get("hba1c")) if isinstance(ctx.monitoring, dict) else None
    if hba1c_val is not None:
        if hba1c_val >= 8.5:
            urgent_signals.append("糖化血红蛋白明显升高")
            score = max(score, 82)
        elif hba1c_val >= 7.0:
            issues.append("糖化血红蛋白高于目标")
            score = max(score, 60)

    hr_val = _parse_first_number(ctx.monitoring.get("hr")) if isinstance(ctx.monitoring, dict) else None
    if hr_val is not None:
        if hr_val >= 120 or hr_val <= 50:
            urgent_signals.append("心率异常")
            score = max(score, 80)
        elif hr_val >= 100:
            issues.append("心率偏快")
            score = max(score, 58)

    adherence_summary = {}
    if isinstance(ctx.adherence, dict):
        adherence_summary = ctx.adherence.get("summary", {}) if isinstance(ctx.adherence.get("summary", {}), dict) else {}
    adherence_rate = _parse_first_number(adherence_summary.get("rate"))
    if adherence_rate is not None:
        if adherence_rate < 50:
            urgent_signals.append("用药依从性极差")
            score = max(score, 80)
        elif adherence_rate < 80:
            issues.append("用药依从性不足")
            score = max(score, 58)

    def _norm(text: str) -> str:
        return re.sub(r"\s+", "", text or "").lower()

    def _infer_task_status(entry: Dict[str, object]) -> str:
        status_text = str(entry.get("completion_status", "")).strip().lower()
        severity_text = str(entry.get("severity", "")).strip().lower()
        if any(flag in status_text for flag in ["未完成", "不遵从", "漏", "中断", "拒绝"]) or severity_text in {"high", "urgent", "critical", "red"}:
            return "red"
        if any(flag in status_text for flag in ["部分", "欠佳", "待改进", "波动", "延迟"]) or severity_text in {"medium", "moderate", "yellow", "attention"}:
            return "yellow"
        if status_text and any(flag in status_text for flag in ["完成", "已完成", "遵从", "按时", "良好"]):
            return "green"
        return "unknown"

    tasks = ctx.tasks if isinstance(ctx.tasks, list) else []
    progresses = ctx.task_progress if isinstance(ctx.task_progress, list) else []
    progress_map = {}
    for entry in progresses:
        task_name = entry.get("task") or entry.get("task_name") or entry.get("name")
        if task_name:
            progress_map[_norm(task_name)] = entry

    task_reasoning_snippets: List[str] = []
    for task in tasks:
        task_name = str(task.get("task") or "").strip()
        norm_name = _norm(task_name)
        matched = progress_map.get(norm_name)
        status = "unknown"
        evidence = ""
        notes = ""
        if matched:
            status = _infer_task_status(matched)
            evidence = str(matched.get("evidence") or matched.get("detail") or "").strip()
            notes = str(matched.get("notes") or matched.get("summary") or "").strip()
        entry = {
            "task": task_name or "（未命名任务）",
            "frequency": task.get("frequency", "—"),
            "instructions": task.get("instructions", "—"),
            "status": status,
            "evidence": evidence,
            "notes": notes,
        }
        task_assessment.append(entry)
        if status == "red":
            urgent_signals.append(f"重点任务未执行：{entry['task']}")
            score = max(score, 88)
            if evidence or notes:
                task_reasoning_snippets.append(f"任务“{entry['task']}”未达成，记录：{evidence or notes}")
        elif status == "yellow":
            issues.append(f"任务执行波动：{entry['task']}")
            score = max(score, 62)
            if evidence or notes:
                task_reasoning_snippets.append(f"任务“{entry['task']}”执行不稳定：{evidence or notes}")
        elif status == "green":
            if evidence:
                task_reasoning_snippets.append(f"任务“{entry['task']}”执行良好：{evidence}")
        else:
            if not matched:
                task_reasoning_snippets.append(f"任务“{entry['task']}”缺少执行记录")

    level = "stable"
    doctor_needed = False
    follow_up_days = 21

    if urgent_signals:
        level = "urgent"
        doctor_needed = True
        follow_up_days = 5
        score = max(score, 86)
    elif score >= 60 or issues:
        level = "attention"
        doctor_needed = True
        follow_up_days = 10
        score = max(score, 48)
    else:
        score = min(score, 40)

    concerns: List[str] = []
    concerns.extend(urgent_signals or [])
    concerns.extend(issues)
    if not concerns:
        concerns.append("目前关键指标处于目标范围")
    if len(concerns) == 1:
        concerns.append("保持随访以观察趋势")

    patient_name = ctx.patient.get("name") if isinstance(ctx.patient, dict) else None
    primary_label = patient_name or "患者"

    reasoning_parts: List[str] = []
    if urgent_signals:
        reasoning_parts.append("存在" + "、".join(urgent_signals) + "等高危信号")
    elif issues:
        reasoning_parts.append("检测到" + "、".join(issues) + "等需要持续关注的指标")
    else:
        reasoning_parts.append("近期生理指标整体达标，未发现显著异常")

    if adherence_rate is not None:
        reasoning_parts.append(f"服药依从性约为{adherence_rate:.1f}%")
    if task_reasoning_snippets:
        reasoning_parts.append("重点任务汇总：" + "；".join(task_reasoning_snippets))
    if level == "stable":
        reasoning_parts.append("建议继续维持当前管理方案并按期复查")
    elif level == "attention":
        reasoning_parts.append("建议医生在近一至两周内复核方案并适度调整")
    else:
        reasoning_parts.append("建议尽快联系主管医生进行诊疗决策")

    suggested_action = {
        "urgent": "建议3天内联系主管医生并评估是否调整治疗方案",
        "attention": "建议7-10天内安排医生复审并优化管理计划",
        "stable": "保持当前方案，按时监测并于3周后复查",
    }[level]

    result = {
        "level": level,
        "risk_score": int(min(max(score, 0), 100)),
        "reasoning": f"{primary_label}：" + "。".join(reasoning_parts),
        "key_concerns": concerns[:5],
        "doctor_intervention_needed": doctor_needed,
        "suggested_action": suggested_action,
        "follow_up_days": follow_up_days,
        "task_assessment": task_assessment,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def call_qwen_api(*, prompt: str, temperature: float = 0.7, max_tokens: int = 1200, model: str = "qwen-turbo") -> str:
    """Invoke Qwen-compatible endpoint; fall back to deterministic heuristics on failure."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt不能为空")

    try:
        if hasattr(client, "responses"):
            response = client.responses.create(
                model=model,
                input=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            if hasattr(response, "output_text") and response.output_text:
                return response.output_text
            if hasattr(response, "output"):
                output_fragments: List[str] = []
                for item in response.output or []:
                    if "content" in item:
                        for piece in item["content"]:
                            if piece.get("type") == "text":
                                output_fragments.append(piece.get("text", ""))
                merged = "\n".join(output_fragments).strip()
                if merged:
                    return merged
        elif hasattr(client, "chat") and hasattr(client.chat, "completions"):
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choices = getattr(completion, "choices", []) or []
            if choices:
                first_choice = choices[0]
                if hasattr(first_choice, "message"):
                    message = first_choice.message
                    content = getattr(message, "content", None)
                else:
                    message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
                    content = message.get("content")

                if isinstance(content, list):
                    merged = "\n".join(
                        [
                            part.get("text", "")
                            for part in content
                            if isinstance(part, dict)
                        ]
                    ).strip()
                    if merged:
                        return merged
                elif isinstance(content, str) and content.strip():
                    return content
                elif hasattr(message, "content") and isinstance(message.content, str):
                    text = message.content.strip()
                    if text:
                        return text
    except Exception as exc:
        print(f"  ⚠️  Qwen API 调用失败，使用规则回退：{exc}")

    ctx = _build_offline_context(prompt)
    return _heuristic_urgency_response(ctx)

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
