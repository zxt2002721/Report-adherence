#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慢病患者报告生成器 v2.0
"""

import argparse
from pathlib import Path
from report_modules import ReportFactory


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="生成患者报告")
    
    parser.add_argument("--id", type=str, help="患者ID（可选，默认使用最新患者数据）")
    parser.add_argument(
        "--type",
        type=str,
        default="compliance",
        choices=ReportFactory.list_types(),
        help="报告类型（默认：compliance）"
    )
    parser.add_argument("--output", type=str, help="输出文件路径（可选）")
    
    args = parser.parse_args()
    
    try:
        # 创建生成器
        generator = ReportFactory.create(
            report_type=args.type,
            patient_id=args.id
        )
        
        # 生成报告
        html = generator.generate()
        
        # 保存
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = None  # 使用默认路径
        
        saved_path = generator.save_to_file(output_path)
        
        # 显示统计信息（依从性报告特有）
        if args.type == 'compliance':
            try:
                stats = generator.get_adherence_stats()
                print(f"\n[概要] 依从记录：{stats['total']} 条，"
                      f"完全依从：{stats['compliant']}，"
                      f"不遵从：{stats['noncompliant']}，"
                      f"完全依从率：{stats['rate']}")
            except:
                pass
        
        print(f"\n✅ 报告生成成功！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())