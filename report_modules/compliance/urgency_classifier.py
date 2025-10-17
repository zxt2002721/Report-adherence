# -*- coding: utf-8 -*-
"""
urgency_classifier.py
紧迫程度分类器 - 使用LLM判断患者情况的紧迫程度

分级标准：
- urgent (紧急级): 需要医生立即介入决策
- attention (关注级): 需要医生定期审阅
- stable (稳定级): AI建议即可
"""

from typing import Dict, Any, Literal, Optional, List
from dataclasses import dataclass, asdict, field
import json
import re
from json_repair import repair_json
from report_modules.common import config
from .prompt_manager import prompt_manager


UrgencyLevel = Literal["urgent", "attention", "stable"]


@dataclass
class UrgencyAssessment:
    """紧迫程度评估结果"""
    level: UrgencyLevel  # urgent/attention/stable
    risk_score: int  # 0-100风险评分
    reasoning: str  # LLM的判断理由
    key_concerns: list  # 关键关注点
    doctor_intervention_needed: bool  # 是否需要医生介入
    suggested_action: str  # 建议行动
    follow_up_days: int  # 建议随访间隔（天）
    verification_passed: bool = True  # 规则引擎校验是否通过
    verification_notes: str = ""  # 校验说明
    task_assessment: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    def get_level_text(self) -> str:
        """获取中文级别描述"""
        level_map = {
            "urgent": "🔴 紧急级",
            "attention": "🟡 关注级",
            "stable": "🟢 稳定级"
        }
        return level_map.get(self.level, "未知")
    
    def get_level_description(self) -> str:
        """获取级别详细说明"""
        desc_map = {
            "urgent": "需要医生立即介入决策，建议尽快联系医生",
            "attention": "需要医生定期审阅，请保持关注",
            "stable": "病情稳定，继续保持当前管理方案"
        }
        return desc_map.get(self.level, "")


def classify_urgency_with_llm(
    patient_data: Dict[str, Any],
    monitoring: Dict[str, Any],
    adherence: Dict[str, Any],
    lifestyle: Dict[str, Any] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
    task_progress: Optional[List[Dict[str, Any]]] = None,
) -> UrgencyAssessment:
    """
    优先调用LLM生成紧迫程度评估，必要时退回本地规则引擎。
    
    Args:
        patient_data: 患者基础信息
        monitoring: 生理监测数据
        adherence: 依从性数据
        lifestyle: 生活方式数据
    
    Returns:
        UrgencyAssessment: 紧迫程度评估结果
    """
    print("  → 使用规则引擎进行紧迫程度评估...")

    assessment = None
    prompt_error = None

    try:
        prompt = prompt_manager.format_prompt(
            "urgency_classification_prompt",
            patient_info=patient_data,
            monitoring=monitoring,
            adherence=adherence,
            lifestyle=lifestyle or {},
            tasks=tasks or [],
            task_progress=task_progress or [],
        )
    except Exception as exc:
        prompt_error = exc
        prompt = None
        print(f"  ⚠️  构建紧迫程度prompt失败：{exc}")

    if prompt:
        try:
            llm_response = config.call_qwen_api(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500,
            )
            assessment = _parse_urgency_response(llm_response)
        except Exception as exc:
            print(f"  ⚠️  LLM紧迫度评估失败，改用规则引擎：{exc}")

    if assessment is None:
        try:
            heuristic_payload = config.generate_urgency_assessment_from_context(
                patient=patient_data,
                monitoring=monitoring,
                adherence=adherence,
                lifestyle=lifestyle or {},
                tasks=tasks or [],
                task_progress=task_progress or [],
            )
            assessment = _parse_urgency_response(json.dumps(heuristic_payload, ensure_ascii=False))
        except Exception as exc:
            print(f"  ⚠️  规则评估失败: {exc}")
            return _get_default_assessment("attention", f"规则评估失败: {str(exc)}")

    print("  → 规则引擎二次校验...")
    assessment = _verify_with_rules(assessment, monitoring, adherence, task_progress)

    if prompt_error and assessment:
        note = "规则评估提示：prompt构建失败，已使用规则结果。"
        assessment.verification_notes = (assessment.verification_notes or "") + note
    
    print(f"  ✓ 紧迫程度评估完成: {assessment.get_level_text()} (风险评分: {assessment.risk_score})")
    
    return assessment


def _parse_urgency_response(response: str) -> UrgencyAssessment:
    """
    解析紧迫程度评估的JSON响应
    
    Args:
        response: JSON格式的评估文本
    
    Returns:
        UrgencyAssessment: 解析后的评估结果
    """
    # 提取JSON
    json_str = _extract_json_from_response(response)
    if not json_str:
        raise ValueError("无法从响应中提取JSON")
    
    # 修复并解析JSON
    try:
        repaired = repair_json(json_str, ensure_ascii=False, return_objects=True)
        if isinstance(repaired, (dict, list)):
            data = repaired
        else:
            data = json.loads(repaired)
    except Exception as e:
        raise ValueError(f"JSON解析失败: {e}")
    
    # 验证必需字段
    required_fields = [
        "level",
        "risk_score",
        "reasoning",
        "key_concerns",
        "doctor_intervention_needed",
        "suggested_action",
        "follow_up_days",
    ]
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        raise ValueError(f"缺少必需字段: {missing_fields}")
    
    # 验证level值
    if data["level"] not in ["urgent", "attention", "stable"]:
        print(f"  ⚠️  无效的level值: {data['level']}, 默认设为attention")
        data["level"] = "attention"
    
    # 构建UrgencyAssessment对象
    return UrgencyAssessment(
        level=data["level"],
        risk_score=int(data["risk_score"]),
        reasoning=data["reasoning"],
        key_concerns=data["key_concerns"] if isinstance(data["key_concerns"], list) else [],
        doctor_intervention_needed=bool(data["doctor_intervention_needed"]),
        suggested_action=data["suggested_action"],
        follow_up_days=int(data["follow_up_days"]),
        task_assessment=data.get("task_assessment", []) if isinstance(data.get("task_assessment", []), list) else []
    )


def _extract_json_from_response(text: str) -> Optional[str]:
    """
    从LLM响应中提取JSON内容
    
    支持多种格式：
    1. ```json ... ```
    2. { ... } 直接JSON
    """
    # 尝试提取markdown代码块
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1).strip()
    
    # 尝试提取纯JSON
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, text)
    if match:
        return match.group(0).strip()
    
    return None


def _verify_with_rules(
    assessment: UrgencyAssessment,
    monitoring: Dict[str, Any],
    adherence: Dict[str, Any],
    task_progress: Optional[List[Dict[str, Any]]] = None,
) -> UrgencyAssessment:
    """
    规则引擎二次校验
    
    校验规则：
    1. 如果生理指标严重异常 → 至少应为attention级
    2. 如果服药依从性极差 → 至少应为attention级
    3. 如果LLM判断不确定 → 统一定为attention级
    4. 如果多个高危因素 → 应为urgent级
    
    Args:
        assessment: LLM的初步评估
        monitoring: 生理监测数据
        adherence: 依从性数据
    
    Returns:
        UrgencyAssessment: 校验后的评估结果
    """
    original_level = assessment.level
    issues = []
    assessment.verification_notes = assessment.verification_notes or ""
    assessment.key_concerns = assessment.key_concerns or []
    
    # 规则1: 检查生理指标
    critical_vitals = _check_critical_vitals(monitoring)
    if critical_vitals:
        issues.extend(critical_vitals)
        if assessment.level == "stable":
            assessment.level = "attention"
            assessment.verification_notes += "规则校验：检测到生理指标异常，提升至关注级。"
    
    # 规则2: 检查依从性
    adherence_issues = _check_adherence_issues(adherence)
    if adherence_issues:
        issues.extend(adherence_issues)
        if assessment.level == "stable":
            assessment.level = "attention"
            assessment.verification_notes += "规则校验：检测到依从性问题，提升至关注级。"
    
    # 规则3: 关键任务执行情况
    task_issues, has_critical_task_issue, has_any_noncompliance = _check_task_issues(task_progress)
    if task_issues:
        issues.extend(task_issues)
        assessment.key_concerns = list(dict.fromkeys((assessment.key_concerns or []) + task_issues))
        if has_any_noncompliance and assessment.level != "urgent":
            assessment.level = "urgent"
            note = "规则校验：检测到重点任务存在不遵从行为，提升至紧急级。"
            if assessment.verification_notes:
                sep = "" if assessment.verification_notes.endswith(("。", "；", "！")) else " "
                assessment.verification_notes += f"{sep}{note}"
            else:
                assessment.verification_notes = note
        elif assessment.level == "stable":
            assessment.level = "attention"
            assessment.verification_notes += "规则校验：遵从任务执行不佳，提升至关注级。"

    # 规则4: 多个高危因素
    if len(issues) >= 3:
        if assessment.level in ["stable", "attention"]:
            assessment.level = "urgent"
            assessment.verification_notes += f"规则校验：检测到{len(issues)}个高危因素，提升至紧急级。"
    
    # 规则5: 风险评分与级别不匹配
    if assessment.risk_score >= 70 and assessment.level == "stable":
        assessment.level = "attention"
        assessment.verification_notes += "规则校验：风险评分过高，提升至关注级。"
    elif assessment.risk_score >= 85 and assessment.level == "attention":
        assessment.level = "urgent"
        assessment.verification_notes += "规则校验：风险评分极高，提升至紧急级。"
    
    # 记录校验结果
    if original_level != assessment.level:
        assessment.verification_passed = False
        print(f"  ⚠️  规则校验调整: {original_level} → {assessment.level}")
        print(f"      原因: {assessment.verification_notes}")
    else:
        assessment.verification_passed = True
        assessment.verification_notes = "规则校验通过，LLM判断合理。"

    # 确保医生介入标记与级别统一
    if assessment.level == "stable":
        assessment.doctor_intervention_needed = False
    else:
        assessment.doctor_intervention_needed = True
    
    return assessment


def _check_task_issues(task_progress: Optional[List[Dict[str, Any]]]) -> tuple[list, bool, bool]:
    """
    检查遵从任务执行情况。

    Returns:
        (issues, has_critical, has_any_noncompliance)
    """
    if not task_progress:
        return [], False, False

    issues: list[str] = []
    has_critical = False
    has_noncompliance = False

    critical_keywords = ["未完成", "未执行", "没执行", "拒绝", "不遵从", "未按时", "中断", "漏", "失败", "恶化"]
    warning_keywords = ["部分", "欠佳", "波动", "待改进", "延迟", "不稳定", "缺少", "未知", "不清楚"]

    for entry in task_progress:
        name = str(entry.get("task") or entry.get("task_name") or entry.get("name") or "重点任务").strip()
        status_text = str(entry.get("status") or entry.get("completion_status") or "").lower()
        severity_text = str(entry.get("severity") or "").lower()
        evidence = str(entry.get("evidence") or entry.get("notes") or entry.get("detail") or "").strip()

        def _record(prefix: str):
            text = f"{prefix}{name}"
            if evidence:
                text += f"（{evidence}）"
            issues.append(text)

        status_lower = status_text.lower()

        if (
            any(keyword in status_lower for keyword in critical_keywords)
            or severity_text in {"high", "urgent", "critical", "red"}
            or status_lower in {"红色", "red", "critical", "urgent"}
        ):
            has_critical = True
            has_noncompliance = True
            _record("重点任务未完成：")
        elif (
            any(keyword in status_lower for keyword in warning_keywords)
            or severity_text in {"medium", "moderate", "yellow", "attention"}
            or status_lower in {"yellow", "注意", "关注"}
        ):
            has_noncompliance = True
            _record("重点任务执行波动：")
        elif status_lower in {"unknown", "缺少记录"}:
            _record("重点任务缺少执行记录：")

    return issues, has_critical, has_noncompliance


def _check_critical_vitals(monitoring: Dict[str, Any]) -> list:
    """
    检查生理指标是否有严重异常
    
    Returns:
        list: 异常项列表
    """
    issues = []
    
    # 检查血压
    bp = monitoring.get("blood_pressure", {})
    if bp:
        latest_sbp = bp.get("recent_avg", {}).get("sbp", 0)
        latest_dbp = bp.get("recent_avg", {}).get("dbp", 0)
        
        if latest_sbp >= 180 or latest_dbp >= 110:
            issues.append("血压严重升高")
        elif latest_sbp < 90 or latest_dbp < 60:
            issues.append("血压过低")
    
    # 检查血糖
    glucose = monitoring.get("blood_glucose", {})
    if glucose:
        recent_avg = glucose.get("recent_avg", 0)
        if recent_avg >= 15:
            issues.append("血糖严重升高")
        elif recent_avg < 3.9:
            issues.append("血糖过低")
    
    # 检查心率
    hr = monitoring.get("heart_rate", {})
    if hr:
        recent_avg = hr.get("recent_avg", 0)
        if recent_avg >= 120 or recent_avg <= 50:
            issues.append("心率异常")
    
    return issues


def _check_adherence_issues(adherence: Dict[str, Any]) -> list:
    """
    检查依从性是否有严重问题
    
    Returns:
        list: 问题列表
    """
    issues = []
    
    # 检查用药依从性
    medication = adherence.get("medication", {})
    if medication:
        compliance_rate = medication.get("compliance_rate", 100)
        if compliance_rate < 50:
            issues.append("用药依从性极差")
        elif compliance_rate < 80:
            issues.append("用药依从性不佳")
    
    # 检查监测依从性
    monitoring_adherence = adherence.get("monitoring", {})
    if monitoring_adherence:
        compliance_rate = monitoring_adherence.get("compliance_rate", 100)
        if compliance_rate < 60:
            issues.append("监测依从性差")
    
    return issues


def _get_default_assessment(level: UrgencyLevel = "attention", reason: str = "") -> UrgencyAssessment:
    """
    获取默认的评估结果（用于异常情况）
    
    Args:
        level: 默认级别
        reason: 原因说明
    
    Returns:
        UrgencyAssessment: 默认评估结果
    """
    return UrgencyAssessment(
        level=level,
        risk_score=50,
        reasoning=f"由于系统异常，无法完成完整评估，建议医生人工审核。{reason}",
        key_concerns=["系统评估异常", "建议人工审核"],
        doctor_intervention_needed=True,
        suggested_action="请医生人工审核患者情况",
        follow_up_days=7,
        verification_passed=False,
        verification_notes="系统异常，使用默认评估",
        task_assessment=[]
    )


# -------------------- 便捷函数 --------------------

def quick_classify(patient_id: str, memory: dict, df_patient, dialogues: list = None) -> UrgencyAssessment:
    """
    快速分类（便捷函数）
    
    Args:
        patient_id: 患者ID
        memory: memory数据
        df_patient: 生理数据DataFrame
        dialogues: 对话记录
    
    Returns:
        UrgencyAssessment: 评估结果
    """
    from report_modules.compliance import medication_processor, monitoring_processor, data_builder
    
    # 构建所需数据
    patient_data = {
        "patient_id": patient_id,
        "basic_info": memory.get("basic_info", {})
    }
    
    monitoring = monitoring_processor.build_monitoring_from_df(df_patient)
    adherence = data_builder.build_adherence(memory)
    lifestyle = data_builder.build_lifestyle(memory)
    tasks = data_builder.build_compliance_tasks(memory)
    task_progress = memory.get("compliance_task_progress_history", []) or []
    
    return classify_urgency_with_llm(
        patient_data,
        monitoring,
        adherence,
        lifestyle,
        tasks,
        task_progress
    )
