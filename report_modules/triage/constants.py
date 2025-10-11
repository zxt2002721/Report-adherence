# triage/constants.py

"""分诊报告的常量定义"""

# ==================== 急诊资源完整库 ====================

EMERGENCY_RESOURCES = {
    "床旁评估与监护": [
        {
            "id": "BS-AM-001",
            "name": "生命体征与心电监护 (Vital Signs & Cardiac Monitoring)"
        },
        {
            "id": "BS-AM-002",
            "name": "床旁快速检测(血糖/酮体/尿试纸)"
        },
        {
            "id": "BS-AM-003",
            "name": "体格检查 (Physical Examination)"
        },
        {
            "id": "BS-AM-004",
            "name": "重点专科床旁评估(神经/呼吸/血管/POCUS)"
        }
    ],
    
    "实验室检查 - 血液学": [
        {
            "id": "LAB-HE-001",
            "name": "血常规 (Complete Blood Count - CBC)"
        },
        {
            "id": "LAB-HE-002",
            "name": "D-二聚体"
        }
    ],
    
    "实验室检查 - 生化": [
        {
            "id": "LAB-CH-001",
            "name": "基础/全面代谢功能组合 (BMP/CMP)"
        },
        {
            "id": "LAB-CH-002",
            "name": "心脏标志物组合 (肌钙蛋白/BNP)"
        },
        {
            "id": "LAB-CH-003",
            "name": "炎症标志物 (CRP/PCT/ESR)"
        },
        {
            "id": "LAB-CH-004",
            "name": "特定器官功能标志物 (脂肪酶/肝功/CK)"
        },
        {
            "id": "LAB-CH-005",
            "name": "乳酸/毒理学筛查"
        }
    ],
    
    "实验室检查 - 凝血": [
        {
            "id": "LAB-CO-001",
            "name": "凝血功能 (PT/INR, PTT)"
        }
    ],
    
    "实验室检查 - 内分泌": [
        {
            "id": "LAB-EN-001",
            "name": "激素/内分泌检测 (甲状腺/HCG/皮质醇)"
        }
    ],
    
    "实验室检查 - 血气": [
        {
            "id": "LAB-GA-001",
            "name": "动/静脉血气分析 (ABG/VBG)"
        }
    ],
    
    "实验室检查 - 尿液": [
        {
            "id": "LAB-UR-001",
            "name": "尿液分析及镜检"
        }
    ],
    
    "实验室检查 - 微生物": [
        {
            "id": "LAB-MI-001",
            "name": "各类标本培养及涂片(血/尿/痰/伤口)"
        },
        {
            "id": "LAB-MI-002",
            "name": "感染性疾病快速检测/PCR (流感/COVID-19/C.diff)"
        },
        {
            "id": "LAB-MI-003",
            "name": "体液分析(脑脊液/胸腹水/关节液)"
        },
        {
            "id": "LAB-MI-004",
            "name": "血清学/特殊病原体检测 (HIV/肝炎/莱姆病)"
        }
    ],
    
    "影像检查": [
        {
            "id": "DX-IM-001",
            "name": "X光检查"
        },
        {
            "id": "DX-IM-002",
            "name": "CT扫描"
        },
        {
            "id": "DX-IM-003",
            "name": "超声检查"
        },
        {
            "id": "DX-IM-004",
            "name": "磁共振成像 (MRI)"
        },
        {
            "id": "DX-IM-005",
            "name": "核医学扫描 (V/Q, HIDA)"
        }
    ],
    
    "心脏/神经电生理": [
        {
            "id": "DX-AC-001",
            "name": "12导联心电图 (ECG/EKG)"
        },
        {
            "id": "DX-AC-002",
            "name": "高级心脏/神经电生理检查 (Holter/EEG)"
        }
    ],
    
    "其他检查": [
        {
            "id": "DX-OS-001",
            "name": "血管造影/介入操作"
        },
        {
            "id": "DX-OS-002",
            "name": "内镜检查 (EGD/支气管镜)"
        },
        {
            "id": "DX-OS-003",
            "name": "诊断性穿刺操作 (腰穿/腹穿/关节穿刺)"
        }
    ]
}


def get_all_resource_ids():
    """获取所有资源ID列表"""
    ids = []
    for category, resources in EMERGENCY_RESOURCES.items():
        for resource in resources:
            ids.append(resource['id'])
    return ids


def get_resource_by_id(resource_id):
    """根据ID获取资源详情"""
    for category, resources in EMERGENCY_RESOURCES.items():
        for resource in resources:
            if resource['id'] == resource_id:
                return {
                    'id': resource['id'],
                    'name': resource['name'],
                    'category': category
                }
    return None


def get_resources_json():
    """
    返回JSON格式的资源数据（用于前端）
    
    Returns:
        包含所有资源的JSON字符串
    """
    import json
    return json.dumps(EMERGENCY_RESOURCES, ensure_ascii=False)