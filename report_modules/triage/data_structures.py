from dataclasses import dataclass

@dataclass
class TriageInput:
    """分诊输入数据（从 test_case 提取）"""
    patient_hpi: dict
    patient_ph: dict
    system_suggested_resources: dict

@dataclass
class TriageResult:
    """分诊结果（就是你的 test_case 格式）"""
    go_to_hospital: dict  # {'chose': 'yes', 'evidence': '...'}
    esi_level: int  # 从 ed_snapshot 里提取
    max_time_to_doctor: dict
    deterioration_risk: dict
    hospital_recommendation: dict
    pre_triage_summary: str