
# 分诊系统规格说明书 (Triage Specification)

## 1. 系统概述

**目标**：辅助医生对患者进行分诊判断，决定患者是否需要立即就医或可居家观察，并提供决策建议供医生审核标注。

**核心流程**：


```
患者数据 → 初步判断 → 分支路径 → 医生标注 → 生成报告
├─ 立即就医路径
└─ 居家观察路径
```


## 2. 核心任务：初步判断

### 2.1 UI界面设计（紧凑版）

```
┌────────────────────────────────────────────────┐
│ 初步判断                                        │
│                                                │
│ 这个病人需要：                                  │
│ ┌──────────────────────────────┐              │
│ │ ▼ 立即就医（需要去医院/急诊）  │ ← 下拉选择   │
│ └──────────────────────────────┘              │
│                                                │
│ 系统建议：立即就医                              │
│ 理由：生命体征异常，存在高危症状                 │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

**下拉选项**：
- 立即就医（需要去医院/急诊）
- 居家观察（不需要立即就医）

### 2.2 数据结构

```python
@dataclass
class InitialDecision:
    """初步判断"""
    decision: Literal["immediate_care", "home_observation"]
    system_suggestion: str
    doctor_choice: str
    doctor_note: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

---

## 3. 路径A：立即就医

### 3.1 紧急程度判断 (ESI分级)

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 紧急程度判断 (ESI)                              │
│                                                │
│ ┌──────────────────────────────┐              │
│ │ ▼ Level 2 - 高危，危及生命    │              │
│ └──────────────────────────────┘              │
│                                                │
│ 系统建议：Level 2                               │
│ 理由：患者胸痛伴心电图异常                       │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **下拉选项** ：

* Level 1 - 需要复苏抢救（立即）
* Level 2 - 高危，危及生命
* Level 3 - 紧急
* Level 4 - 次紧急
* Level 5 - 非紧急

 **判定标准参考表** ：

| ESI级别 | 定义           | 典型症状               |
| ------- | -------------- | ---------------------- |
| Level 1 | 需要立即复苏   | 心跳骤停、无呼吸、休克 | 
| Level 2 | 高危或意识改变 | 胸痛、呼吸困难、大出血 | 
| Level 3 | 紧急           | 中度呼吸困难、腹痛     | 
| Level 4 | 次紧急         | 轻度损伤、发热         | 
| Level 5 | 非紧急         | 慢性症状、随访         | 

 **数据结构** ：

```python
esi_level: int  # 1-5
esi_system_suggestion: int
esi_doctor_choice: int
esi_note: Optional[str] = None
```

---

### 3.2 急诊资源需求

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 急诊资源需求                                    │
│                                                │
│ 已选择的资源：                                  │
│ [血常规] [心肌酶谱] [12导联心电图]              │
│ [心内科会诊] [CT(胸部)] [新增]                  │
│                                                │
│ [📝 编辑资源列表]  [+ 添加批注]                 │
│                                                │
│ 💡 提示：系统初始推荐了4项资源，您已添加1项     │
└────────────────────────────────────────────────┘

**点击"编辑资源列表"后弹出完整选项**（资源已预选）：
┌─────────────────────────────────────────────────┐
│ 编辑急诊资源需求                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🏥 床旁评估与监护                                │
│ ☐ 生命体征与心电监护                            │
│ ☐ 床旁快速检测(血糖/酮体/尿试纸)                │
│ ☐ 体格检查                                      │
│ ☐ 重点专科床旁评估(神经/呼吸/血管/POCUS)        │
│                                                 │
│ 🔬 实验室检查 - 血液学                           │
│ ☑ 血常规 (CBC)                    [系统推荐]    │
│ ☐ D-二聚体                                      │
│                                                 │
│ 🧪 实验室检查 - 生化                             │
│ ☐ 基础/全面代谢功能组合 (BMP/CMP)               │
│ ☑ 心脏标志物组合 (肌钙蛋白/BNP)   [系统推荐]    │
│ ☐ 炎症标志物 (CRP/PCT/ESR)                     │
│ ☐ 特定器官功能标志物 (脂肪酶/肝功/CK)           │
│ ☐ 乳酸/毒理学筛查                               │
│                                                 │
│ 🩸 实验室检查 - 凝血                             │
│ ☐ 凝血功能 (PT/INR, PTT)                       │
│                                                 │
│ 💉 实验室检查 - 内分泌                           │
│ ☐ 激素/内分泌检测 (甲状腺/HCG/皮质醇)           │
│                                                 │
│ 🫁 实验室检查 - 血气                             │
│ ☐ 动/静脉血气分析 (ABG/VBG)                    │
│                                                 │
│ 💧 实验室检查 - 尿液                             │
│ ☐ 尿液分析及镜检                                │
│                                                 │
│ 🦠 实验室检查 - 微生物                           │
│ ☐ 各类标本培养及涂片(血/尿/痰/伤口)             │
│ ☐ 感染性疾病快速检测/PCR                        │
│ ☐ 体液分析(脑脊液/胸腹水/关节液)                │
│ ☐ 血清学/特殊病原体检测                         │
│                                                 │
│ 📷 影像检查                                      │
│ ☐ X光检查                                       │
│ ☑ CT扫描                          [医生新增]    │
│ ☐ 超声检查                                      │
│ ☐ 磁共振成像 (MRI)                              │
│ ☐ 核医学扫描 (V/Q, HIDA)                       │
│                                                 │
│ ⚡ 心脏/神经电生理                                │
│ ☑ 12导联心电图 (ECG/EKG)         [系统推荐]    │
│ ☐ 高级心脏/神经电生理检查 (Holter/EEG)         │
│                                                 │
│ 🏥 其他检查                                      │
│ ☐ 血管造影/介入操作                             │
│ ☐ 内镜检查 (EGD/支气管镜)                       │
│ ☐ 诊断性穿刺操作 (腰穿/腹穿/关节穿刺)           │
│                                                 │
│ 👨‍⚕️ 专科会诊                                     │
│ ☑ 心内科会诊                      [系统推荐]    │
│ ☐ 神经科会诊                                    │
│ ☐ 呼吸科会诊                                    │
│ ☐ 消化科会诊                                    │
│ ☐ 外科会诊                                      │
│ ☐ 骨科会诊                                      │
│ ☐ 泌尿科会诊                                    │
│ ☐ 妇产科会诊                                    │
│ ☐ 儿科会诊                                      │
│ ☐ 精神科会诊                                    │
│                                                 │
│        [取消]           [确认修改]              │
└─────────────────────────────────────────────────┘
```

 **资源库定义** ：

```python
EMERGENCY_RESOURCES = {
    "床旁评估与监护": {
        "category_id": "bedside_assessment",
        "items": [
            {
                "id": "BS-AM-001",
                "name": "生命体征与心电监护",
                "description": "持续监测心率、血压、呼吸频率、体温与血氧饱和度",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 180
            },
            {
                "id": "BS-AM-002",
                "name": "床旁快速检测(血糖/酮体/尿试纸)",
                "description": "床旁快速化验用于即刻决策",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 10
            },
            {
                "id": "BS-AM-003",
                "name": "体格检查",
                "description": "系统体格检查评估气道与循环稳定性",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 10
            },
            {
                "id": "BS-AM-004",
                "name": "重点专科床旁评估(神经/呼吸/血管/POCUS)",
                "description": "针对主诉的目标性非影像床旁评估",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 15
            }
        ]
    },
    
    "实验室检查 - 血液学": {
        "category_id": "lab_hematology",
        "items": [
            {
                "id": "LAB-HE-001",
                "name": "血常规 (CBC)",
                "description": "包含WBC及分类、Hb/Hct与血小板",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 50
            },
            {
                "id": "LAB-HE-002",
                "name": "D-二聚体",
                "description": "纤维蛋白降解产物升高提示体内凝血-纤溶激活",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 50
            }
        ]
    },
    
    "实验室检查 - 生化": {
        "category_id": "lab_chemistry",
        "items": [
            {
                "id": "LAB-CH-001",
                "name": "基础/全面代谢功能组合 (BMP/CMP)",
                "description": "评估电解质、肾功能、葡萄糖、肝酶等",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 55
            },
            {
                "id": "LAB-CH-002",
                "name": "心脏标志物组合 (肌钙蛋白/BNP)",
                "description": "心肌标志物用于诊断心肌梗死/损伤",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 50
            },
            {
                "id": "LAB-CH-003",
                "name": "炎症标志物 (CRP/PCT/ESR)",
                "description": "反映炎症/感染活动度",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 65
            },
            {
                "id": "LAB-CH-004",
                "name": "特定器官功能标志物 (脂肪酶/肝功/CK)",
                "description": "脂肪酶用于胰腺炎诊断",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 60
            },
            {
                "id": "LAB-CH-005",
                "name": "乳酸/毒理学筛查",
                "description": "乳酸反映组织低灌注与代谢性酸中毒程度",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 60
            }
        ]
    },
    
    "实验室检查 - 凝血": {
        "category_id": "lab_coagulation",
        "items": [
            {
                "id": "LAB-CO-001",
                "name": "凝血功能 (PT/INR, PTT)",
                "description": "评估外源性/内源性凝血通路",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 50
            }
        ]
    },
    
    "实验室检查 - 内分泌": {
        "category_id": "lab_endocrinology",
        "items": [
            {
                "id": "LAB-EN-001",
                "name": "激素/内分泌检测 (甲状腺/HCG/皮质醇)",
                "description": "用于妊娠/甲状腺危象/肾上腺危象评估",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 185
            }
        ]
    },
    
    "实验室检查 - 血气": {
        "category_id": "lab_gas_analysis",
        "items": [
            {
                "id": "LAB-GA-001",
                "name": "动/静脉血气分析 (ABG/VBG)",
                "description": "评估氧合、通气与酸碱状态",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 15
            }
        ]
    },
    
    "实验室检查 - 尿液": {
        "category_id": "lab_urinalysis",
        "items": [
            {
                "id": "LAB-UR-001",
                "name": "尿液分析及镜检",
                "description": "评估白细胞、血尿、蛋白尿与酮体",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 60
            }
        ]
    },
    
    "实验室检查 - 微生物": {
        "category_id": "lab_microbiology",
        "items": [
            {
                "id": "LAB-MI-001",
                "name": "各类标本培养及涂片(血/尿/痰/伤口)",
                "description": "病原体鉴定及药敏",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 90
            },
            {
                "id": "LAB-MI-002",
                "name": "感染性疾病快速检测/PCR (流感/COVID-19/C.diff)",
                "description": "快速抗原或核酸检测",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 45
            },
            {
                "id": "LAB-MI-003",
                "name": "体液分析(脑脊液/胸腹水/关节液)",
                "description": "细胞计数、蛋白/葡萄糖、培养与晶体学",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 60
            },
            {
                "id": "LAB-MI-004",
                "name": "血清学/特殊病原体检测 (HIV/肝炎/莱姆病)",
                "description": "血清学抗体/抗原检测",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 180
            }
        ]
    },
    
    "影像检查": {
        "category_id": "imaging",
        "items": [
            {
                "id": "DX-IM-001",
                "name": "X光检查",
                "description": "快速、低剂量成像用于胸部/骨骼评估",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 50
            },
            {
                "id": "DX-IM-002",
                "name": "CT扫描",
                "description": "高分辨率断层成像评估颅内出血、肺栓塞、急腹症",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 60
            },
            {
                "id": "DX-IM-003",
                "name": "超声检查",
                "description": "床旁POCUS与正式超声",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 15
            },
            {
                "id": "DX-IM-004",
                "name": "磁共振成像 (MRI)",
                "description": "对中枢神经系统、脊柱与软组织病变敏感",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 90
            },
            {
                "id": "DX-IM-005",
                "name": "核医学扫描 (V/Q, HIDA)",
                "description": "功能成像评估PE、胆囊功能",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 180
            }
        ]
    },
    
    "心脏/神经电生理": {
        "category_id": "electrophysiology",
        "items": [
            {
                "id": "DX-AC-001",
                "name": "12导联心电图 (ECG/EKG)",
                "description": "识别急性缺血/梗死、心律失常",
                "workflow": "Bedside - Parallel",
                "turnaround_minutes": 10
            },
            {
                "id": "DX-AC-002",
                "name": "高级心脏/神经电生理检查 (Holter/EEG)",
                "description": "捕捉间歇性心律失常或癫痫活动",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 90
            }
        ]
    },
    
    "其他检查": {
        "category_id": "other_procedures",
        "items": [
            {
                "id": "DX-OS-001",
                "name": "血管造影/介入操作",
                "description": "冠脉造影与支架、介入栓塞止血",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 90
            },
            {
                "id": "DX-OS-002",
                "name": "内镜检查 (EGD/支气管镜)",
                "description": "直接观察并可行止血、取异物",
                "workflow": "Requires Dedicated Room",
                "turnaround_minutes": 120
            },
            {
                "id": "DX-OS-003",
                "name": "诊断性穿刺操作 (腰穿/腹穿/关节穿刺)",
                "description": "获取体液进行诊断并可减压治疗",
                "workflow": "Bedside - Focused",
                "turnaround_minutes": 45
            }
        ]
    },
    
    
}
```

 **数据结构** ：

```python
resources_needed: List[str]
resources_system_suggestion: List[str]
resources_doctor_choice: List[str]
resources_note: Optional[str] = None
```

---

### 3.3 最大安全等待时间 (Patient-to-Doctor)

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 最大安全等待时间 (Patient-to-Doctor)            │
│                                                │
│ ┌──────────────────────────────┐              │
│ │ ▼ 10分钟内                    │              │
│ └──────────────────────────────┘              │
│                                                │
│ 系统建议：10分钟内                              │
│ 理由：患者存在急性心肌缺血风险                   │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **下拉选项** ：

* 0分钟 - 立即（无等待）
* 10分钟内
* 30分钟内
* 60分钟内
* 120分钟内
* 自定义：___ 分钟

 **数据结构** ：

```python
max_wait_time: int  # 分钟
max_wait_time_system: int
max_wait_time_doctor: int
max_wait_time_note: Optional[str] = None
```

---

### 3.4 病情恶化风险

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 病情恶化风险                                    │
│                                                │
│ ┌──────────────────────────────┐              │
│ │ ▼ 中风险                      │              │
│ └──────────────────────────────┘              │
│                                                │
│ 系统判断依据：                                  │
│ • 生命体征部分异常                              │
│ • 存在高危症状（胸痛）                          │
│ • 有心血管病史                                  │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **下拉选项** ：

* 低风险
* 中风险
* 高风险

 **数据结构** ：

```python
deterioration_risk: Literal["低", "中", "高"]
deterioration_risk_system: str
deterioration_risk_doctor: str
deterioration_risk_note: Optional[str] = None
```

---

### 3.5 医院推荐建议
Note: 优先实现单选项， 然后无距离.  医院[实验室能力，等待时长]. 但是这里的信息呈现方式还是不确定。 

 **UI界面（折叠版）** ：

```
┌────────────────────────────────────────────────┐
│ 系统推荐医院                                    │
│                                                │
│ 🏥 市第一人民医院急诊科                         │
│                                                │
│ 推荐理由：                                      │
│ ✅ 距离最近（3.2公里，预计8分钟）               │
│ ✅ 有心内科急诊能力                             │
│ ✅ 有24小时心导管室                             │
│ ⚠️ 当前急诊较繁忙（等待30-45分钟）             │
│                                                │
│ 预计床位等待时间：30-45分钟                     │
│                                                │
│ 医生判断：                                      │
│ (●) 同意系统建议                                │
│ ( ) 不同意，选择其他医院 [▼ 展开列表]          │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **点击"展开列表"后显示** ：[待定]

```
┌────────────────────────────────────────────────┐
│ 选择医院                                        │
├────────────────────────────────────────────────┤
│                                                │
│ (●) 市第一人民医院                              │
│     距离：3.2km | 心内科能力：⭐⭐⭐⭐⭐         │
│     当前状态：🟡 繁忙 | 预计等待：30-45分钟     │
│                                                │
│ ( ) 市中心医院                                  │
│     距离：5.8km | 心内科能力：⭐⭐⭐⭐           │
│     当前状态：🟢 正常 | 预计等待：15-20分钟     │
│                                                │
│ ( ) 区人民医院                                  │
│     距离：2.1km | 心内科能力：⭐⭐⭐             │
│     当前状态：🟢 空闲 | 预计等待：5-10分钟      │
│                                                │
│        [取消]           [确认]                 │
└────────────────────────────────────────────────┘
```

 **数据结构** ：

```python
recommended_hospital: str
hospital_system_suggestion: str
hospital_doctor_choice: str
hospital_agree: bool
hospital_note: Optional[str] = None
```

---

### 3.6 当前医院状态（实时数据，可折叠）. [待定]

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 📊 推荐医院当前状态  [▼ 展开详情]              │
└────────────────────────────────────────────────┘
```

 **点击展开后** ：

```
┌────────────────────────────────────────────────┐
│ 📊 推荐医院当前状态  [▲ 收起]                  │
├────────────────────────────────────────────────┤
│                                                │
│ 🏥 市第一人民医院                               │
│ 急诊科状态：🟡 繁忙                             │
│ 候诊人数：12人                                  │
│ 平均等待时间：35分钟                            │
│                                                │
│ 可用资源：                                      │
│ • 心电图：✅ 可用                               │
│ • CT：✅ 可用（需等待20分钟）                   │
│ • 心内科医生：✅ 在岗                           │
│ • 急诊床位：⚠️ 紧张（剩余2张）                 │
│                                                │
│ 数据更新时间：2025-10-06 14:30                 │
└────────────────────────────────────────────────┘
```

---

### 3.7 立即就医路径完整数据结构

```python
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime

@dataclass
class ImmediateCareAssessment:
    """立即就医评估"""
  
    # ESI分级
    esi_level: int  # 1-5
    esi_system_suggestion: int
    esi_doctor_choice: int
    esi_note: Optional[str] = None
  
    # 急诊资源
    resources_needed: List[str]
    resources_system_suggestion: List[str]
    resources_doctor_choice: List[str]
    resources_note: Optional[str] = None
  
    # 最大等待时间（分钟）
    max_wait_time: int
    max_wait_time_system: int
    max_wait_time_doctor: int
    max_wait_time_note: Optional[str] = None
  
    # 恶化风险
    deterioration_risk: Literal["低", "中", "高"]
    deterioration_risk_system: str
    deterioration_risk_doctor: str
    deterioration_risk_note: Optional[str] = None
  
    # 医院推荐
    recommended_hospital: str
    hospital_system_suggestion: str
    hospital_doctor_choice: str
    hospital_agree: bool
    hospital_note: Optional[str] = None
  
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
```

---

## 4. 路径B：居家观察

### 4.1 默认参数

```python
{
    "esi_level": 5,
    "resources_needed": [],
    "max_wait_time": "24小时",
    "deterioration_risk": "低"
}
```

---

### 4.2 建议复查时间

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 建议复查时间                                    │
│                                                │
│ ┌──────────────────────────────┐              │
│ │ ▼ 24小时内复查                │              │
│ └──────────────────────────────┘              │
│                                                │
│ 系统建议：24小时内复查                          │
│ 理由：轻度发热，需观察体温变化                   │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **下拉选项** ：

* 12小时内复查
* 24小时内复查
* 48小时内复查
* 72小时内复查
* 1周内复查
* 自定义：___ 小时

 **数据结构** ：

```python
followup_time: str  # "12小时", "24小时", etc.
followup_time_system: str
followup_time_doctor: str
followup_time_note: Optional[str] = None
```

---

### 4.3 居家护理措施

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 建议的居家护理措施                              │
│                                                │
│ 系统推荐：                                      │
│ ☑ 充分休息                                     │
│ ☑ 多饮水（每日1500-2000ml）                    │
│ ☑ 监测体温（每4小时测量一次）                   │
│ ☑ 清淡饮食                                     │
│                                                │
│ 医生选择：                                      │
│ ☑ 充分休息                                     │
│ ☑ 多饮水（每日1500-2000ml）                    │
│ ☑ 监测体温（每4小时测量一次）                   │
│ ☑ 清淡饮食                                     │
│ ☑ 温水擦浴（体温>38.5°C）[新增]                │
│                                                │
│ [📝 编辑措施列表]  [+ 添加批注]                 │
└────────────────────────────────────────────────┘
```

 **点击"编辑措施列表"后弹出** ：

```
┌─────────────────────────────────────────┐
│ 选择居家护理措施                         │
├─────────────────────────────────────────┤
│                                         │
│ 🛏️ 基础护理                              │
│ ☐ 充分休息                              │
│ ☐ 保持室内通风                          │
│ ☐ 适当活动                              │
│ ☐ 避免剧烈运动                          │
│                                         │
│ 🍽️ 饮食管理                              │
│ ☐ 多饮水（每日1500-2000ml）             │
│ ☐ 清淡饮食                              │
│ ☐ 少食多餐                              │
│ ☐ 避免刺激性食物                        │
│ ☐ 避免饮酒                              │
│                                         │
│ 📊 监测措施                              │
│ ☐ 监测体温（每4小时）                   │
│ ☐ 监测血压（每日2次）                   │
│ ☐ 监测血糖（餐前餐后）                  │
│ ☐ 记录症状日记                          │
│ ☐ 监测尿量                              │
│                                         │
│ 🌡️ 物理治疗                              │
│ ☐ 温水擦浴（体温>38.5°C）               │
│ ☐ 冷敷（局部肿胀）                      │
│ ☐ 热敷（关节疼痛）                      │
│ ☐ 雾化吸入                              │
│                                         │
│ 💊 药物管理                              │
│ ☐ 按时服药                              │
│ ☐ 避免自行加药                          │
│ ☐ 记录用药时间                          │
│ ☐ 注意药物不良反应                      │
│                                         │
│ 🧼 隔离与卫生                            │
│ ☐ 隔离措施（传染性疾病）                │
│ ☐ 勤洗手                                │
│ ☐ 戴口罩                                │
│ ☐ 房间消毒                              │
│ ☐ 餐具分开                              │
│                                         │
│        [取消]           [确认]          │
└─────────────────────────────────────────┘
```

 **措施库定义** ：

```python
HOME_CARE_MEASURES = {
    "基础护理": [
        "充分休息", "保持室内通风", "适当活动", "避免剧烈运动"
    ],
    "饮食管理": [
        "多饮水（每日1500-2000ml）", "清淡饮食", "少食多餐",
        "避免刺激性食物", "避免饮酒"
    ],
    "监测措施": [
        "监测体温（每4小时）", "监测血压（每日2次）",
        "监测血糖（餐前餐后）", "记录症状日记", "监测尿量"
    ],
    "物理治疗": [
        "温水擦浴（体温>38.5°C）", "冷敷（局部肿胀）",
        "热敷（关节疼痛）", "雾化吸入"
    ],
    "药物管理": [
        "按时服药", "避免自行加药", "记录用药时间", "注意药物不良反应"
    ],
    "隔离与卫生": [
        "隔离措施（传染性疾病）", "勤洗手", "戴口罩",
        "房间消毒", "餐具分开"
    ]
}
```

 **数据结构** ：

```python
care_measures: List[str]
care_measures_system: List[str]
care_measures_doctor: List[str]
care_measures_note: Optional[str] = None
```

---

### 4.4 需要立即就医的警告信号

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 需要立即就医的警告信号                          │
│                                                │
│ 系统推荐的警告信号：                            │
│ ☑ 高热>39°C且持续不退                          │
│ ☑ 呼吸困难或气促                               │
│ ☑ 胸痛或胸闷                                   │
│ ☑ 意识改变（嗜睡、昏迷）                        │
│                                                │
│ 医生选择的警告信号：                            │
│ ☑ 高热>39°C且持续不退                          │
│ ☑ 呼吸困难或气促                               │
│ ☑ 胸痛或胸闷                                   │
│ ☑ 意识改变（嗜睡、昏迷）                        │
│ ☑ 持续呕吐或腹泻 [新增]                         │
│                                                │
│ [📝 编辑警告信号]  [+ 添加批注]                 │
└────────────────────────────────────────────────┘
```

 **点击"编辑警告信号"后弹出** ：

```
┌─────────────────────────────────────────┐
│ 选择警告信号                             │
├─────────────────────────────────────────┤
│                                         │
│ 🫁 呼吸系统                              │
│ ☐ 呼吸困难或气促                        │
│ ☐ 呼吸频率>30次/分                      │
│ ☐ 嘴唇发紫（紫绀）                      │
│ ☐ 咯血                                  │
│ ☐ 胸痛伴呼吸困难                        │
│                                         │
│ ❤️ 心血管系统                            │
│ ☐ 胸痛或胸闷                            │
│ ☐ 心悸伴晕厥                            │
│ ☐ 血压过低（<90/60mmHg）                │
│ ☐ 血压过高（>180/110mmHg）              │
│ ☐ 心率过快（>120次/分）                 │
│ ☐ 心率过慢（<50次/分）                  │
│                                         │
│ 🧠 神经系统                              │
│ ☐ 意识改变（嗜睡、昏迷）                │
│ ☐ 剧烈头痛                              │
│ ☐ 抽搐                                  │
│ ☐ 肢体活动障碍                          │
│ ☐ 视力突然改变                          │
│ ☐ 言语不清                              │
│                                         │
│ 🍽️ 消化系统                              │
│ ☐ 持续呕吐                              │
│ ☐ 严重腹痛                              │
│ ☐ 便血或黑便                            │
│ ☐ 剧烈腹泻                              │
│ ☐ 无法进食进水                          │
│                                         │
│ 🌡️ 全身症状                              │
│ ☐ 高热>39°C且持续不退                   │
│ ☐ 寒战伴高热                            │
│ ☐ 皮疹伴发热                            │
│ ☐ 严重乏力                              │
│ ☐ 出血不止                              │
│                                         │
│ ⚠️ 特殊情况                              │
│ ☐ 严重过敏反应                          │
│ ☐ 孕妇阴道出血                          │
│ ☐ 自杀倾向                              │
│ ☐ 药物过量                              │
│                                         │
│        [取消]           [确认]          │
└─────────────────────────────────────────┘
```

 **警告信号库定义** ：

```python
WARNING_SIGNS = {
    "呼吸系统": [
        "呼吸困难或气促", "呼吸频率>30次/分",
        "嘴唇发紫（紫绀）", "咯血", "胸痛伴呼吸困难"
    ],
    "心血管系统": [
        "胸痛或胸闷", "心悸伴晕厥",
        "血压过低（<90/60mmHg）", "血压过高（>180/110mmHg）",
        "心率过快（>120次/分）", "心率过慢（<50次/分）"
    ],
    "神经系统": [
        "意识改变（嗜睡、昏迷）", "剧烈头痛", "抽搐",
        "肢体活动障碍", "视力突然改变", "言语不清"
    ],
    "消化系统": [
        "持续呕吐", "严重腹痛", "便血或黑便",
        "剧烈腹泻", "无法进食进水"
    ],
    "全身症状": [
        "高热>39°C且持续不退", "寒战伴高热",
        "皮疹伴发热", "严重乏力", "出血不止"
    ],
    "特殊情况": [
        "严重过敏反应", "孕妇阴道出血", "自杀倾向", "药物过量"
    ]
}
```

 **数据结构** ：

```python
warning_signs: List[str]
warning_signs_system: List[str]
warning_signs_doctor: List[str]
warning_signs_note: Optional[str] = None
```

---

### 4.5 居家恶化风险

 **UI界面** ：

```
┌────────────────────────────────────────────────┐
│ 居家观察期间恶化风险                            │
│                                                │
│ ┌──────────────────────────────┐              │
│ │ ▼ 低风险                      │              │
│ └──────────────────────────────┘              │
│                                                │
│ 系统判断依据：                                  │
│ • 生命体征正常                                  │
│ • 症状轻微且稳定                                │
│ • 无高危病史                                    │
│ • 家属能够提供护理                              │
│                                                │
│ [+ 添加批注]                                   │
└────────────────────────────────────────────────┘
```

 **下拉选项** ：

* 低风险
* 中风险
* 高风险

 **数据结构** ：

```python
deterioration_risk: Literal["低", "中", "高"]
deterioration_risk_system: str
deterioration_risk_doctor: str
deterioration_risk_note: Optional[str] = None
```

---

### 4.6 居家观察路径完整数据结构

```python
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime

@dataclass
class HomeObservationAssessment:
    """居家观察评估"""
  
    # 默认参数
    esi_level: int = 5
    resources_needed: List[str] = field(default_factory=list)
  
    # 复查时间
    followup_time: str  # "12小时", "24小时", "48小时", etc.
    followup_time_system: str
    followup_time_doctor: str
    followup_time_note: Optional[str] = None
  
    # 居家护理措施
    care_measures: List[str]
    care_measures_system: List[str]
    care_measures_doctor: List[str]
    care_measures_note: Optional[str] = None
  
    # 警告信号
    warning_signs: List[str]
    warning_signs_system: List[str]
    warning_signs_doctor: List[str]
    warning_signs_note: Optional[str] = None
  
    # 恶化风险
    deterioration_risk: Literal["低", "中", "高"]
    deterioration_risk_system: str
    deterioration_risk_doctor: str
    deterioration_risk_note: Optional[str] = None
  
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
```

---

## 5. 完整数据结构总览

```python
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Union
from datetime import datetime

# ==================== 初步判断 ====================

@dataclass
class InitialDecision:
    """初步判断"""
    decision: Literal["immediate_care", "home_observation"]
    system_suggestion: str
    doctor_choice: str
    doctor_note: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== 立即就医路径 ====================

@dataclass
class ImmediateCareAssessment:
    """立即就医评估"""
  
    # ESI分级
    esi_level: int  # 1-5
    esi_system_suggestion: int
    esi_doctor_choice: int
    esi_note: Optional[str] = None
  
    # 急诊资源
    resources_needed: List[str]
    resources_system_suggestion: List[str]
    resources_doctor_choice: List[str]
    resources_note: Optional[str] = None
  
    # 最大等待时间（分钟）
    max_wait_time: int
    max_wait_time_system: int
    max_wait_time_doctor: int
    max_wait_time_note: Optional[str] = None
  
    # 恶化风险
    deterioration_risk: Literal["低", "中", "高"]
    deterioration_risk_system: str
    deterioration_risk_doctor: str
    deterioration_risk_note: Optional[str] = None
  
    # 医院推荐
    recommended_hospital: str
    hospital_system_suggestion: str
    hospital_doctor_choice: str
    hospital_agree: bool
    hospital_note: Optional[str] = None
  
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== 居家观察路径 ====================

@dataclass
class HomeObservationAssessment:
    """居家观察评估"""
  
    # 默认参数
    esi_level: int = 5
    resources_needed: List[str] = field(default_factory=list)
  
    # 复查时间
    followup_time: str
    followup_time_system: str
    followup_time_doctor: str
    followup_time_note: Optional[str] = None
  
    # 居家护理措施
    care_measures: List[str]
    care_measures_system: List[str]
    care_measures_doctor: List[str]
    care_measures_note: Optional[str] = None
  
    # 警告信号
    warning_signs: List[str]
    warning_signs_system: List[str]
    warning_signs_doctor: List[str]
    warning_signs_note: Optional[str] = None
  
    # 恶化风险
    deterioration_risk: Literal["低", "中", "高"]
    deterioration_risk_system: str
    deterioration_risk_doctor: str
    deterioration_risk_note: Optional[str] = None
  
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== 完整分诊结果 ====================

@dataclass
class TriageResult:
    """分诊结果（包含初步判断 + 对应路径的详细评估）"""
  
    patient_id: str
    initial_decision: InitialDecision
    assessment: Union[ImmediateCareAssessment, HomeObservationAssessment]
    created_at: datetime = field(default_factory=datetime.now)
    doctor_id: Optional[str] = None
```

---

## 6. 常量定义（有限集合）

```python
# ==================== 急诊资源库 ====================

EMERGENCY_RESOURCES = {
    "实验室检查": [
        "血常规", "生化全套", "肝功能", "肾功能",
        "心肌酶谱", "肌钙蛋白", "D-二聚体", "凝血功能",
        "血气分析", "尿常规", "粪便常规"
    ],
    "影像检查": [
        "X光（胸部）", "X光（腹部）",
        "CT（头部）", "CT（胸部）", "CT（腹部）",
        "MRI（头部）", "超声（心脏）", "超声（腹部）",
        "心电图", "动态心电图"
    ],
    "专科会诊": [
        "心内科", "神经科", "呼吸科", "消化科", "外科",
        "骨科", "泌尿科", "妇产科", "儿科", "精神科"
    ],
    "其他资源": [
        "吸氧", "心电监护", "静脉输液", "导尿", "胃管", "ICU床位"
    ]
}


# ==================== 居家护理措施库 ====================

HOME_CARE_MEASURES = {
    "基础护理": [
        "充分休息", "保持室内通风", "适当活动", "避免剧烈运动"
    ],
    "饮食管理": [
        "多饮水（每日1500-2000ml）", "清淡饮食", "少食多餐",
        "避免刺激性食物", "避免饮酒"
    ],
    "监测措施": [
        "监测体温（每4小时）", "监测血压（每日2次）",
        "监测血糖（餐前餐后）", "记录症状日记", "监测尿量"
    ],
    "物理治疗": [
        "温水擦浴（体温>38.5°C）", "冷敷（局部肿胀）",
        "热敷（关节疼痛）", "雾化吸入"
    ],
    "药物管理": [
        "按时服药", "避免自行加药", "记录用药时间", "注意药物不良反应"
    ],
    "隔离与卫生": [
        "隔离措施（传染性疾病）", "勤洗手", "戴口罩",
        "房间消毒", "餐具分开"
    ]
}


# ==================== 警告信号库 ====================

WARNING_SIGNS = {
    "呼吸系统": [
        "呼吸困难或气促", "呼吸频率>30次/分",
        "嘴唇发紫（紫绀）", "咯血", "胸痛伴呼吸困难"
    ],
    "心血管系统": [
        "胸痛或胸闷", "心悸伴晕厥",
        "血压过低（<90/60mmHg）", "血压过高（>180/110mmHg）",
        "心率过快（>120次/分）", "心率过慢（<50次/分）"
    ],
    "神经系统": [
        "意识改变（嗜睡、昏迷）", "剧烈头痛", "抽搐",
        "肢体活动障碍", "视力突然改变", "言语不清"
    ],
    "消化系统": [
        "持续呕吐", "严重腹痛", "便血或黑便",
        "剧烈腹泻", "无法进食进水"
    ],
    "全身症状": [
        "高热>39°C且持续不退", "寒战伴高热",
        "皮疹伴发热", "严重乏力", "出血不止"
    ],
    "特殊情况": [
        "严重过敏反应", "孕妇阴道出血", "自杀倾向", "药物过量"
    ]
}


# ==================== ESI分级选项 ====================

ESI_LEVELS = {
    1: {"name": "Level 1 - 需要复苏抢救", "wait_time": 0, "description": "立即"},
    2: {"name": "Level 2 - 高危，危及生命", "wait_time": 10, "description": "10分钟内"},
    3: {"name": "Level 3 - 紧急", "wait_time": 30, "description": "30分钟内"},
    4: {"name": "Level 4 - 次紧急", "wait_time": 60, "description": "60分钟内"},
    5: {"name": "Level 5 - 非紧急", "wait_time": 120, "description": "120分钟内"}
}


# ==================== 最大等待时间选项 ====================

MAX_WAIT_TIME_OPTIONS = [
    {"value": 0, "label": "0分钟 - 立即（无等待）"},
    {"value": 10, "label": "10分钟内"},
    {"value": 30, "label": "30分钟内"},
    {"value": 60, "label": "60分钟内"},
    {"value": 120, "label": "120分钟内"}
]


# ==================== 复查时间选项 ====================

FOLLOWUP_TIME_OPTIONS = [
    "12小时内复查",
    "24小时内复查",
    "48小时内复查",
    "72小时内复查",
    "1周内复查"
]


# ==================== 风险等级 ====================

RISK_LEVELS = ["低", "中", "高"]
```

---

## 7. 系统建议算法（待实现）

```python
class TriageRecommendationEngine:
    """分诊推荐引擎"""
  
    @staticmethod
    def suggest_initial_decision(vital_signs, symptoms, history) -> str:
        """
        推荐初步判断：立即就医 vs 居家观察
      
        Returns:
            "immediate_care" or "home_observation"
        """
        pass
  
    @staticmethod
    def suggest_esi_level(vital_signs, symptoms) -> int:
        """
        推荐ESI分级 (1-5)
        """
        pass
  
    @staticmethod
    def suggest_resources(esi_level, symptoms, chief_complaint) -> List[str]:
        """
        推荐急诊资源
        """
        pass
  
    @staticmethod
    def suggest_max_wait_time(esi_level, deterioration_risk) -> int:
        """
        推荐最大等待时间（分钟）
        """
        pass
  
    @staticmethod
    def assess_deterioration_risk(vital_signs, symptoms, history) -> str:
        """
        评估病情恶化风险
      
        Returns:
            "低", "中", or "高"
        """
        pass
  
    @staticmethod
    def recommend_hospital(patient_location, required_capabilities) -> dict:
        """
        推荐医院
      
        Returns:
            {
                "hospital_name": str,
                "distance": float,
                "capabilities": List[str],
                "current_status": str,
                "estimated_wait": str
            }
        """
        pass
  
    @staticmethod
    def suggest_followup_time(symptoms, vital_signs) -> str:
        """
        推荐复查时间（居家观察）
        """
        pass
  
    @staticmethod
    def suggest_care_measures(symptoms, diagnosis) -> List[str]:
        """
        推荐居家护理措施
        """
        pass
  
    @staticmethod
    def suggest_warning_signs(diagnosis, risk_factors) -> List[str]:
        """
        推荐警告信号
        """
        pass
```

---

## 8. HTML界面实现要点

### 8.1 下拉选择器实现

```html
<!-- ESI选择器 -->
<div class="triage-field">
    <label>紧急程度判断 (ESI)</label>
    <select data-k="esi_level" data-field="esi_doctor_choice">
        <option value="1">Level 1 - 需要复苏抢救（立即）</option>
        <option value="2" selected>Level 2 - 高危，危及生命（10分钟内）</option>
        <option value="3">Level 3 - 紧急（30分钟内）</option>
        <option value="4">Level 4 - 次紧急（60分钟内）</option>
        <option value="5">Level 5 - 非紧急（120分钟内）</option>
    </select>
  
    <div class="system-suggestion">
        系统建议：Level 2<br>
        理由：患者胸痛伴心电图异常
    </div>
  
    <button class="add-note-btn" data-target="esi_note">+ 添加批注</button>
    <div class="note-area" data-note="esi_note" style="display:none;">
        <textarea placeholder="请输入批注..."></textarea>
    </div>
</div>
```

### 8.2 弹出式多选框实现

```html
<!-- 急诊资源选择 -->
<div class="triage-field">
    <label>急诊资源需求</label>
  
    <div class="selected-items">
        <span class="tag">血常规</span>
        <span class="tag">心肌酶谱</span>
        <span class="tag">心电图</span>
        <span class="tag">心内科会诊</span>
    </div>
  
    <button class="edit-btn" onclick="openResourceModal()">
        📝 编辑资源列表
    </button>
  
    <button class="add-note-btn">+ 添加批注</button>
</div>

<!-- 模态框（弹出层） -->
<div id="resourceModal" class="modal" style="display:none;">
    <div class="modal-content">
        <h3>选择急诊资源</h3>
      
        <div class="resource-category">
            <h4>📋 实验室检查</h4>
            <label><input type="checkbox" value="血常规"> 血常规</label>
            <label><input type="checkbox" value="生化全套"> 生化全套</label>
            <!-- ... 更多选项 -->
        </div>
      
        <div class="resource-category">
            <h4>🔬 影像检查</h4>
            <label><input type="checkbox" value="X光（胸部）"> X光（胸部）</label>
            <!-- ... 更多选项 -->
        </div>
      
        <div class="modal-footer">
            <button onclick="closeResourceModal()">取消</button>
            <button onclick="saveResources()">确认</button>
        </div>
    </div>
</div>
```

### 8.3 折叠面板实现

```html
<!-- 医院状态（可折叠） -->
<div class="collapsible-panel">
    <div class="panel-header" onclick="togglePanel(this)">
        <span>📊 推荐医院当前状态</span>
        <span class="toggle-icon">▼</span>
    </div>
  
    <div class="panel-content" style="display:none;">
        <p>🏥 市第一人民医院</p>
        <p>急诊科状态：🟡 繁忙</p>
        <p>候诊人数：12人</p>
        <!-- ... 更多内容 -->
    </div>
</div>

<script>
function togglePanel(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.toggle-icon');
  
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▲';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
    }
}
</script>
```

---

## 9. 报告输出示例

### 9.1 立即就医路径报告

```
┌══════════════════════════════════════════════════════┐
│              分诊报告 - 立即就医                      │
├══════════════════════════════════════════════════════┤
│ 患者ID: P001                                         │
│ 生成时间: 2025-10-06 14:30                           │
│ 分诊医生: 张医生                                      │
└══════════════════════════════════════════════════════┘

1. 初步判断
   ✓ 系统建议: 立即就医
   ✓ 医生决定: 立即就医 ✅ 同意
   └─ 批注: 患者存在急性心肌缺血风险，需紧急处理

2. 紧急程度 (ESI)
   ✓ 系统建议: Level 2
   ✓ 医生决定: Level 2 ✅ 同意
   └─ 批注: 同意，患者有胸痛主诉且心电图异常

3. 急诊资源
   ✓ 系统建议: [血常规, 心肌酶谱, 心电图, 心内科会诊]
   ✓ 医生决定: [血常规, 心肌酶谱, 心电图, 心内科会诊, CT(胸部)]
   └─ 批注: 增加CT检查排除主动脉夹层

4. 最大安全等待时间
   ✓ 系统建议: 10分钟内
   ✓ 医生决定: 10分钟内 ✅ 同意

5. 病情恶化风险
   ✓ 系统建议: 高风险
   ✓ 医生决定: 高风险 ✅ 同意

6. 推荐医院
   ✓ 系统建议: 市第一人民医院（距离3.2km，有心导管室）
   ✓ 医生决定: 市第一人民医院 ✅ 同意
   └─ 批注: 该院有24小时心导管室，适合急性心梗处理
```

### 9.2 居家观察路径报告

```
┌══════════════════════════════════════════════════════┐
│              分诊报告 - 居家观察                      │
├══════════════════════════════════════════════════════┤
│ 患者ID: P002                                         │
│ 生成时间: 2025-10-06 15:00                           │
│ 分诊医生: 李医生                                      │
└══════════════════════════════════════════════════════┘

1. 初步判断
   ✓ 系统建议: 居家观察
   ✓ 医生决定: 居家观察 ✅ 同意
   └─ 批注: 轻度发热，生命体征稳定

2. 建议复查时间
   ✓ 系统建议: 24小时内
   ✓ 医生决定: 24小时内 ✅ 同意

3. 居家护理措施
   ✓ 系统建议: [充分休息, 多饮水, 监测体温, 清淡饮食]
   ✓ 医生决定: [充分休息, 多饮水, 监测体温, 清淡饮食, 温水擦浴]
   └─ 批注: 每4小时测量体温并记录

4. 警告信号（出现时立即就医）
   ☑ 高热>39°C且持续不退
   ☑ 呼吸困难
   ☑ 胸痛
   ☑ 意识改变

5. 恶化风险
   ✓ 系统建议: 低风险
   ✓ 医生决定: 低风险 ✅ 同意
```

---

## 10. 待定事项

**需要进一步明确：**

1. ✅ 急诊资源库 - 已定义
2. ✅ 居家护理措施库 - 已定义
3. ✅ 警告信号库 - 已定义
4. ✅ UI交互设计 - 已采用下拉+弹出模式
5. ⏳ 医院数据库结构（距离、能力、床位等）
6. ⏳ 实时医院状态API接口
7. ⏳ ESI分级的详细判定算法
8. ⏳ 病情恶化风险的量化评分标准

---

 **文档版本** : v1.1 (紧凑UI版)

 **最后更新** : 2025-10-06

 **下一步** : 实现数据结构 (`triage/data_structures.py`)

```

现在整个文档在一个连续的 markdown 代码块中了，可以直接复制。UI 设计改为：

1. **单选题** → 下拉选择器 `<select>`
2. **多选题** → 显示已选标签 + "编辑"按钮弹出模态框
3. **详细信息** → 折叠面板，点击展开

这样界面会紧凑很多！需要我继续生成 `data_structures.py` 的代码吗?
```
