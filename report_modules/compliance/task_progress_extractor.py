# -*- coding: utf-8 -*-
"""任务执行情况分析器

根据随访对话自动推断重点遵从任务的执行状态。

默认优先调用大模型进行语义分析，当大模型不可用或解析失败时，
会退化为占位结果以避免阻断主流程。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from json_repair import repair_json

from report_modules.common import config
from .prompt_manager import prompt_manager


_STATUS_KEYWORDS = {
    "已完成": {"completed", "已完成", "完成", "坚持", "按时", "做到", "遵从"},
    "部分遵从": {"partial", "部分", "偶尔", "间断", "波动", "不太稳定", "有时"},
    "未完成": {"未完成", "未执行", "未做到", "没有执行", "漏", "拒绝", "放弃", "忘记"},
    "缺少记录": {"缺少", "未知", "不清楚", "未提及", "无记录", "无信息"},
}


def analyze_task_progress(
    *,
    tasks: List[Dict[str, Any]],
    patient_info: Dict[str, Any] | None = None,
    dialogues: Any = None,
    adherence_history: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """调用大模型分析任务执行进度。

    Args:
        tasks: 重点遵从任务列表
        patient_info: 患者基础信息（可选）
        dialogues: 与患者相关的对话或记录
        adherence_history: 结构化依从性历史

    Returns:
        List[Dict[str, Any]]: 每个任务的执行情况
    """

    if not tasks:
        return []

    try:
        prompt = prompt_manager.format_prompt(
            "task_progress_analysis_prompt",
            patient_info=patient_info or {},
            tasks=tasks,
            dialogues=dialogues or [],
            adherence_history=adherence_history or [],
        )

        response = config.call_qwen_api(
            prompt=prompt,
            temperature=0.35,
            max_tokens=1200,
        )
        parsed = _parse_llm_response(response)
        return _merge_with_tasks(tasks, parsed)
    except Exception as exc:  # noqa: BLE001 - 保证主流程不中断
        print(f"  ⚠️  AI任务执行分析失败，改用启发式推断：{exc}")

    heuristic = _heuristic_progress_from_dialogues(tasks, dialogues)
    return _merge_with_tasks(tasks, heuristic)


def _parse_llm_response(response: str) -> List[Dict[str, Any]]:
    """解析大模型返回的文本为结构化列表。"""

    json_str = _extract_json(response)
    if not json_str:
        raise ValueError("未找到合法JSON输出")

    try:
        data = repair_json(json_str, ensure_ascii=False, return_objects=True)
        if isinstance(data, str):
            data = json.loads(data)
    except Exception as exc:  # noqa: BLE001 - 保证回退
        raise ValueError(f"任务进度JSON解析失败: {exc}") from exc

    if isinstance(data, dict):
        data = data.get("tasks") or data.get("task_assessment") or data.get("items")
    if not isinstance(data, list):
        raise ValueError("任务进度结果不是数组格式")

    cleaned: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "task": str(item.get("task") or item.get("task_name") or "").strip(),
                "completion_status": _normalise_status(str(item.get("completion_status") or "")),
                "confidence": _safe_float(item.get("confidence"), default=0.6),
                "evidence": str(item.get("evidence") or item.get("evidences") or "").strip(),
                "notes": str(item.get("notes") or item.get("comment") or "").strip(),
            }
        )

    return cleaned


def _extract_json(text: str) -> str | None:
    """从模型输出中提取JSON片段。"""

    match = re.search(r"```json\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()

    match = re.search(r"\[\s*[\{\[]", text)
    if match:
        start = match.start()
        end_match = re.search(r"\][^\]]*$", text)
        if end_match:
            return text[start : end_match.end()].strip()

    match = re.search(r"\{[\s\S]*\}\s*$", text)
    return match.group(0).strip() if match else None


def _normalise_status(status_text: str) -> str:
    """统一化模型返回的状态文本。"""

    text = status_text.strip().lower()
    if not text:
        return "缺少记录"

    for label, keywords in _STATUS_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return label

    return "缺少记录"


def _safe_float(value: Any, default: float = 0.6) -> float:
    """安全地将输入转换为0-1之间的浮点数。"""

    try:
        val = float(value)
    except (TypeError, ValueError):
        return default

    if val < 0:
        return 0.0
    if val > 1:
        return 1.0
    return val


def _merge_with_tasks(
    tasks: List[Dict[str, Any]],
    parsed: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """按输入任务顺序合并模型分析结果。"""

    def _norm(text: str) -> str:
        return re.sub(r"\s+", "", (text or "").lower())

    parsed_map = {_norm(item.get("task")): item for item in parsed if item.get("task")}

    merged: List[Dict[str, Any]] = []
    for task in tasks:
        name = task.get("task") or "（未命名任务）"
        norm_name = _norm(name)
        record = parsed_map.get(norm_name)

        if not record:
            record = {
                "task": name,
                "completion_status": "缺少记录",
                "confidence": 0.4,
                "evidence": "",
                "notes": "近期对话未提及执行情况",
            }
        else:
            record = {
                "task": name,
                "completion_status": record.get("completion_status", "缺少记录"),
                "confidence": _safe_float(record.get("confidence"), 0.6),
                "evidence": record.get("evidence", ""),
                "notes": record.get("notes", ""),
            }

        merged.append(record)

    return merged


def _heuristic_progress_from_dialogues(
    tasks: List[Dict[str, Any]],
    dialogues: Any,
) -> List[Dict[str, Any]]:
    """基于对话内容的简单启发式推断。"""

    patient_msgs = _collect_patient_messages(dialogues)
    results: List[Dict[str, Any]] = []

    for task in tasks:
        name = task.get("task") or "（未命名任务）"
        keywords = _extract_keywords(name)

        status = "缺少记录"
        evidence = ""

        for msg in patient_msgs:
            if not keywords or any(key in msg for key in keywords):
                detected = _infer_status_from_message(msg)
                if detected:
                    evidence = msg
                    if detected == "未完成":
                        status = detected
                        break
                    if detected == "部分遵从":
                        status = "部分遵从"
                    elif detected == "已完成" and status == "缺少记录":
                        status = "已完成"

        if status == "未完成":
            confidence = 0.75
            notes = "患者明确表示未能落实，需要重点干预"
        elif status == "部分遵从":
            confidence = 0.65
            notes = "执行不稳定，需加强提醒与支持"
        elif status == "已完成":
            confidence = 0.6
            notes = "患者表示按计划执行"
        else:
            confidence = 0.4
            notes = "近期对话未覆盖该任务"

        results.append(
            {
                "task": name,
                "completion_status": status,
                "confidence": confidence,
                "evidence": evidence,
                "notes": notes,
            }
        )

    return results


def _collect_patient_messages(dialogues: Any) -> List[str]:
    messages: List[str] = []

    def _consume(obj: Any) -> None:
        if isinstance(obj, dict):
            speaker = obj.get("speaker")
            if speaker == "patient":
                msg = str(obj.get("message") or "").strip()
                if msg:
                    messages.append(msg)
            for key in ("conversation_turns", "turns", "messages", "records"):
                if key in obj and isinstance(obj[key], list):
                    _consume(obj[key])
            for value in obj.values():
                if isinstance(value, (list, dict)):
                    _consume(value)
        elif isinstance(obj, list):
            for item in obj:
                _consume(item)

    if dialogues:
        _consume(dialogues)

    return messages


def _extract_keywords(task_name: str) -> List[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}", task_name or "")
    if not tokens:
        return [task_name.strip()]
    return tokens


def _infer_status_from_message(message: str) -> str | None:
    text = message.strip()
    if not text:
        return None

    negative_hard = ["从不", "一直没", "拒绝", "不去", "不做", "不想", "没去", "没做", "未去"]
    negative_soft = ["偶尔", "有时候", "有时", "忙", "忘", "断", "麻烦", "担心", "害怕", "怕"]
    positive = ["按时", "坚持", "每天", "都会", "照着", "有做", "做到", "安排", "完成"]

    lowered = text.lower()

    if any(word in text for word in negative_hard):
        return "未完成"
    if any(word in text for word in negative_soft):
        return "部分遵从"
    if any(word in text for word in positive):
        return "已完成"
    if "没" in text or "不" in text:
        return "部分遵从"
    if "试着" in text or "努力" in text:
        return "部分遵从"
    if "会" in text and any(word in lowered for word in ("do", "will", "安排")):
        return "已完成"
    return None
