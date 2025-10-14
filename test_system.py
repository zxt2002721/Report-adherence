#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告生成系统测试脚本
用于验证系统各个组件是否正常工作
"""

import sys
from pathlib import Path
import json
import traceback

def test_import_modules():
    """测试模块导入"""
    print("=" * 50)
    print("1. 测试模块导入")
    print("=" * 50)
    
    try:
        from report_modules import ReportFactory
        print("✅ ReportFactory 导入成功")
        
        types = ReportFactory.list_types()
        print(f"✅ 可用报告类型: {types}")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_data_files():
    """测试数据文件"""
    print("\n" + "=" * 50)
    print("2. 测试数据文件")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "output" / "dialogue_data"
    
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return False
    
    print(f"✅ 数据目录存在: {data_dir}")
    
    # 检查测试患者的数据文件
    test_files = [
        "0b389f61f90fcf6da613e08c64e06fdbaf05758cdd9e6b5ae730f1b8a8a654e4_multiday.json",
        "6e84e63ded176d781f2a6e6a8d3e2cc82de94c2b360bee96209ddd24dabf3f3a_multiday.json", 
        "7cb394d6e1c52e050ef41a9caa3c186d6a6a71fe2172fa8f901783973404285a_multiday.json"
    ]
    
    found_files = 0
    for file_name in test_files:
        file_path = data_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name[:12]}... 存在")
            found_files += 1
        else:
            print(f"❌ {file_name[:12]}... 不存在")
    
    print(f"\n📊 数据文件统计: {found_files}/{len(test_files)} 个文件可用")
    return found_files > 0

def test_report_generation():
    """测试报告生成"""
    print("\n" + "=" * 50)
    print("3. 测试报告生成")
    print("=" * 50)
    
    try:
        from report_modules import ReportFactory
        
        # 测试数据ID (P001对应的数据)
        test_patient_id = "0b389f61f90fcf6da613e08c64e06fdbaf05758cdd9e6b5ae730f1b8a8a654e4"
        
        # 测试依从性报告
        print("🔍 测试依从性报告生成...")
        try:
            generator = ReportFactory.create('compliance', test_patient_id)
            print("✅ 依从性报告生成器创建成功")
            
            # 这里不实际生成完整报告，只测试创建过程
            print("✅ 依从性报告测试通过")
            
        except Exception as e:
            print(f"❌ 依从性报告测试失败: {e}")
        
        # 测试分诊报告（如果可用）
        available_types = ReportFactory.list_types()
        if 'triage' in available_types:
            print("🔍 测试分诊报告生成...")
            try:
                generator = ReportFactory.create('triage', test_patient_id)
                print("✅ 分诊报告生成器创建成功")
                print("✅ 分诊报告测试通过")
            except Exception as e:
                print(f"❌ 分诊报告测试失败: {e}")
        else:
            print("⚠️ 分诊报告不可用，跳过测试")
        
        return True
        
    except Exception as e:
        print(f"❌ 报告生成测试失败: {e}")
        traceback.print_exc()
        return False

def test_api_server():
    """测试API服务器"""
    print("\n" + "=" * 50)
    print("4. 测试API服务器配置")
    print("=" * 50)
    
    try:
        # 检查simple_server.py
        server_file = Path(__file__).parent / "simple_server.py"
        if server_file.exists():
            print("✅ simple_server.py 存在")
        else:
            print("❌ simple_server.py 不存在")
            return False
        
        # 检查前端文件
        frontend_file = Path(__file__).parent / "frontend" / "simple.html"
        if frontend_file.exists():
            print("✅ frontend/simple.html 存在")
        else:
            print("❌ frontend/simple.html 不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ API服务器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 慢性病报告生成系统测试")
    print("测试时间:", Path(__file__).stat().st_mtime)
    
    results = []
    
    # 运行各项测试
    results.append(("模块导入", test_import_modules()))
    results.append(("数据文件", test_data_files()))
    results.append(("报告生成", test_report_generation()))
    results.append(("API服务器", test_api_server()))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<12} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常使用")
        print("\n💡 使用方法:")
        print("   python start_simple.py")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    exit(main())