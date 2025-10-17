#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧迫程度分类器测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from report_modules.common import data_loader
from report_modules.compliance import urgency_classifier, monitoring_processor, data_builder


def test_urgency_classifier():
    """测试紧迫程度分类器"""
    
    print("=" * 60)
    print("紧迫程度分类器测试")
    print("=" * 60)
    
    # 测试患者ID
    patient_ids = [
        "patient_urgent_4cb54929806e",
    ]
    
    for idx, patient_id in enumerate(patient_ids, 1):
        print(f"\n{'='*60}")
        print(f"测试患者 {idx}: {patient_id[:8]}...")
        print(f"{'='*60}\n")
        
        try:
            # 加载数据
            print("1. 加载患者数据...")
            memory, dialogues, df_patient = data_loader.load_patient_data(patient_id)
            print(f"   ✓ 数据加载成功")
            
            # 构建所需数据
            print("\n2. 构建评估数据...")
            patient_data = {
                "patient_id": f"P{idx:03d}",
                "name": memory.get("basic_info", {}).get("name", f"患者{idx}"),
                "age": memory.get("basic_info", {}).get("age", "未知"),
                "gender": memory.get("basic_info", {}).get("sex", "未知")
            }
            
            monitoring = monitoring_processor.build_monitoring_from_df(df_patient)
            adherence = data_builder.build_adherence(memory)
            lifestyle = data_builder.build_lifestyle(memory)
            
            print(f"   ✓ 监测数据: {len(monitoring)} 项")
            print(f"   ✓ 依从性数据: {len(adherence)} 类别")
            print(f"   ✓ 生活方式数据: {len(lifestyle)} 项")
            
            # 调用分类器
            print("\n3. 执行紧迫程度评估...")
            assessment = urgency_classifier.classify_urgency_with_llm(
                patient_data=patient_data,
                monitoring=monitoring,
                adherence=adherence,
                lifestyle=lifestyle
            )
            
            # 显示结果
            print(f"\n{'='*60}")
            print("评估结果")
            print(f"{'='*60}")
            print(f"患者: {patient_data['name']} ({patient_data['patient_id']})")
            print(f"紧迫程度: {assessment.get_level_text()}")
            print(f"风险评分: {assessment.risk_score}/100")
            print(f"需要医生介入: {'是' if assessment.doctor_intervention_needed else '否'}")
            print(f"建议随访间隔: {assessment.follow_up_days}天")
            
            print(f"\n判断理由:")
            print(f"  {assessment.reasoning}")
            
            print(f"\n关键关注点:")
            for concern in assessment.key_concerns:
                print(f"  • {concern}")
            
            print(f"\n建议行动:")
            print(f"  {assessment.suggested_action}")
            
            if not assessment.verification_passed:
                print(f"\n⚠️ 规则校验:")
                print(f"  {assessment.verification_notes}")
            else:
                print(f"\n✓ 规则校验通过")
            
            print(f"\n{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)


def test_quick_classify():
    """测试快速分类便捷函数"""
    
    print("\n" + "="*60)
    print("快速分类函数测试")
    print("="*60 + "\n")
    
    patient_id = "patient_urgent_4cb54929806e"
    
    try:
        print(f"测试患者: {patient_id[:8]}...")
        
        # 加载基础数据
        memory, dialogues, df_patient = data_loader.load_patient_data(patient_id)
        
        # 使用快速分类
        print("\n使用快速分类函数...")
        assessment = urgency_classifier.quick_classify(
            patient_id="P001",
            memory=memory,
            df_patient=df_patient,
            dialogues=dialogues
        )
        
        print(f"\n结果: {assessment.get_level_text()} (风险评分: {assessment.risk_score})")
        print(f"判断理由: {assessment.reasoning}")
        
        # 转换为字典
        print("\n转换为字典格式:")
        assessment_dict = assessment.to_dict()
        print(f"字典键: {list(assessment_dict.keys())}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='紧迫程度分类器测试')
    parser.add_argument('--quick', action='store_true', help='仅测试快速分类函数')
    
    args = parser.parse_args()
    
    if args.quick:
        test_quick_classify()
    else:
        test_urgency_classifier()
