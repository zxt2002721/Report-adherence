#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版报告生成服务
提供基础的患者查找和报告生成功能
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_file
import sys
import traceback

# 添加当前目录到Python路径，确保能导入report_modules
sys.path.insert(0, str(Path(__file__).parent))

# 导入报告生成模块
try:
    from report_modules import ReportFactory
    REPORT_SYSTEM_AVAILABLE = True
    print("✅ 报告生成系统加载成功")
except ImportError as e:
    print(f"⚠️ 报告生成系统加载失败: {e}")
    print("   将使用模拟模式")
    REPORT_SYSTEM_AVAILABLE = False

app = Flask(__name__)

# 手动添加CORS头
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 配置路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "report" / "output"

# 患者ID映射到实际数据文件
PATIENT_MAPPING = {
    'P001': '0b389f61f90fcf6da613e08c64e06fdbaf05758cdd9e6b5ae730f1b8a8a654e4',
    'P002': '6e84e63ded176d781f2a6e6a8d3e2cc82de94c2b360bee96209ddd24dabf3f3a',
    'P003': '7cb394d6e1c52e050ef41a9caa3c186d6a6a71fe2172fa8f901783973404285a'
}

# 患者信息数据库（可以从实际数据源读取）
PATIENT_INFO = {
    'P001': {
        'id': 'P001',
        'name': '张三',
        'age': 65,
        'gender': '男',
        'diagnosis': '2型糖尿病,高血压',
        'dataFile': '0b389f61f90fcf6da613e08c64e06fdbaf05758cdd9e6b5ae730f1b8a8a654e4'
    },
    'P002': {
        'id': 'P002',
        'name': '李四',
        'age': 58,
        'gender': '女',
        'diagnosis': '高血压,冠心病',
        'dataFile': '6e84e63ded176d781f2a6e6a8d3e2cc82de94c2b360bee96209ddd24dabf3f3a'
    },
    'P003': {
        'id': 'P003',
        'name': '王五',
        'age': 72,
        'gender': '男',
        'diagnosis': '慢性肾病,糖尿病',
        'dataFile': '7cb394d6e1c52e050ef41a9caa3c186d6a6a71fe2172fa8f901783973404285a'
    }
}

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """获取患者信息"""
    try:
        patient_id_upper = patient_id.upper()
        
        # 检查患者ID是否存在
        if patient_id_upper not in PATIENT_INFO:
            return jsonify({'error': f'患者 {patient_id} 不存在'}), 404
        
        patient = PATIENT_INFO[patient_id_upper]
        
        # 检查数据文件是否存在
        data_file = DATA_DIR / "output" / "dialogue_data" / f"{patient['dataFile']}_multiday.json"
        if not data_file.exists():
            print(f"⚠️ 数据文件不存在: {data_file}")
            patient['hasData'] = False
        else:
            patient['hasData'] = True
            print(f"✅ 找到数据文件: {data_file}")
        
        return jsonify(patient)
            
    except Exception as e:
        print(f"❌ 获取患者信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """生成报告 - 使用真实的报告生成系统"""
    try:
        data = request.json
        patient_id = data.get('patientId', '').upper()
        report_type = data.get('reportType', '')
        
        print(f"🚀 开始生成报告: {patient_id} - {report_type}")
        
        if not patient_id or not report_type:
            return jsonify({'error': '缺少必要参数'}), 400
            
        if patient_id not in PATIENT_INFO:
            return jsonify({'error': '患者不存在'}), 404
            
        if not REPORT_SYSTEM_AVAILABLE:
            return jsonify({'error': '报告生成系统不可用'}), 503
            
        # 获取患者数据文件ID
        data_id = PATIENT_INFO[patient_id]['dataFile']
        
        # 检查报告类型是否支持
        available_types = ReportFactory.list_types()
        if report_type not in available_types:
            return jsonify({
                'error': f'不支持的报告类型: {report_type}',
                'available': available_types
            }), 400
        
        # 创建输出目录
        output_dir = REPORT_DIR / patient_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 输出目录: {output_dir}")
        print(f"🔍 数据ID: {data_id}")
        
        # 使用ReportFactory创建生成器
        generator = ReportFactory.create(
            report_type=report_type,
            patient_id=data_id
        )
        
        print(f"🏭 生成器创建成功: {generator.__class__.__name__}")
        
        # 生成报告HTML
        print("⚙️ 开始生成报告内容...")
        html_content = generator.generate()
        
        print(f"✅ 报告内容生成完成，长度: {len(html_content)} 字符")
        
        # 保存报告到文件
        report_filename = f"{report_type}_{patient_id}.html"
        report_file_path = output_dir / report_filename
        
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"💾 报告已保存到: {report_file_path}")
        
        # 获取统计信息（如果是依从性报告）
        stats_info = {}
        if report_type == 'compliance':
            try:
                stats = generator.get_adherence_stats()
                stats_info = {
                    'total': stats['total'],
                    'compliant': stats['compliant'],
                    'noncompliant': stats['noncompliant'],
                    'rate': stats['rate']
                }
                print(f"📊 依从性统计: {stats_info}")
            except Exception as e:
                print(f"⚠️ 无法获取统计信息: {e}")
        
        # 返回成功响应
        report_url = f"/api/reports/{patient_id}/{report_filename}"
        
        response_data = {
            'success': True,
            'reportPath': report_url,
            'message': '报告生成成功',
            'reportType': report_type,
            'patientId': patient_id,
            'filename': report_filename
        }
        
        if stats_info:
            response_data['stats'] = stats_info
        
        print(f"🎉 报告生成完成!")
        return jsonify(response_data)
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 报告生成失败: {error_msg}")
        print(f"🔍 详细错误信息:")
        traceback.print_exc()
        
        return jsonify({
            'error': f'报告生成失败: {error_msg}',
            'type': 'generation_error'
        }), 500

@app.route('/api/reports/<patient_id>/<filename>', methods=['GET'])
def get_report(patient_id, filename):
    """获取生成的报告文件"""
    try:
        report_file = REPORT_DIR / patient_id / filename
        
        print(f"📄 请求报告文件: {report_file}")
        
        if report_file.exists():
            print(f"✅ 文件存在，返回报告")
            return send_file(
                report_file, 
                as_attachment=False, 
                mimetype='text/html; charset=utf-8'
            )
        else:
            print(f"❌ 文件不存在: {report_file}")
            # 列出目录中的文件以帮助调试
            report_dir = REPORT_DIR / patient_id
            if report_dir.exists():
                files = list(report_dir.glob('*.html'))
                print(f"🔍 目录中的HTML文件: {[f.name for f in files]}")
                
            return jsonify({
                'error': '报告文件不存在',
                'requestedFile': str(report_file),
                'exists': False
            }), 404
            
    except Exception as e:
        print(f"❌ 获取报告文件失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    status = {
        'status': 'healthy',
        'message': '慢性病报告生成服务运行正常',
        'reportSystem': REPORT_SYSTEM_AVAILABLE,
        'availablePatients': list(PATIENT_INFO.keys())
    }
    
    if REPORT_SYSTEM_AVAILABLE:
        try:
            status['availableReportTypes'] = ReportFactory.list_types()
        except Exception as e:
            status['reportSystemError'] = str(e)
    
    return jsonify(status)

@app.route('/', methods=['GET'])
def index():
    """主页"""
    status = {
        'name': '慢性病报告生成服务',
        'version': '2.0.0',
        'reportSystemAvailable': REPORT_SYSTEM_AVAILABLE,
        'endpoints': [
            'GET /api/health - 健康检查',
            'GET /api/patients/<patient_id> - 获取患者信息',
            'POST /api/generate-report - 生成报告',
            'GET /api/reports/<patient_id>/<filename> - 获取报告文件'
        ],
        'testPatients': list(PATIENT_INFO.keys())
    }
    
    if REPORT_SYSTEM_AVAILABLE:
        try:
            status['availableReportTypes'] = ReportFactory.list_types()
        except:
            pass
    
    return jsonify(status)

def check_dependencies():
    """检查依赖文件"""
    required_dirs = [DATA_DIR, REPORT_DIR]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"创建目录: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # 检查数据文件
    data_dialogue_dir = DATA_DIR / "dialogue_data"
    if not data_dialogue_dir.exists():
        print(f"警告: 数据目录不存在 {data_dialogue_dir}")
        return False
    
    return True

if __name__ == '__main__':
    print("正在启动慢性病报告生成服务...")
    
    # 检查依赖
    if not check_dependencies():
        print("警告: 某些依赖文件缺失，服务可能无法正常工作")
    
    print("服务启动成功!")
    print("前端访问地址: http://localhost:5000/static/simple.html")
    print("API文档: http://localhost:5000/")
    
    # 启动服务
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )