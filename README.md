# 慢性病管理报告生成系统

一个基于AI的智能慢性病患者报告生成系统，支持服药依从性评估和分诊评估，提供完整的Web界面和API服务。

## 🎯 系统特性

### 核心功能
- **智能报告生成**: 基于AI分析的个性化患者报告
- **多种报告类型**: 支持服药依从性评估和分诊评估
- **🆕 紧迫程度分级**: AI自动判断患者情况是否需要医生立即介入（三级分类）
- **实时数据处理**: 从真实患者对话数据中提取关键信息
- **可视化图表**: 自动生成健康趋势图表和统计图
- **Web界面**: 简洁易用的前端操作界面
- **RESTful API**: 完整的API接口支持

### 技术架构
- **后端**: Python Flask + 模块化报告生成器
- **前端**: 现代HTML5 + JavaScript (无框架依赖)
- **AI分析**: 集成智能分析引擎（含紧迫程度评估）
- **数据可视化**: Matplotlib图表生成
- **报告格式**: HTML格式，支持打印和分享

## 📋 系统要求

### 环境要求
- Python 3.7+
- 现代Web浏览器 (Chrome 60+, Firefox 60+, Safari 12+, Edge 79+)

### Python依赖
```bash
pip install flask jinja2 matplotlib pandas markdown
```

## 🚀 快速开始

### 1. 系统检查
```bash
# 运行系统测试，确保所有组件正常
python test_system.py
```

### 2. 启动系统
```bash
# 方法1: 一键启动 (推荐)
python start_simple.py

# 方法2: 手动启动
python simple_server.py
# 然后在浏览器中打开 frontend/simple.html
```

### 3. 使用系统
1. **访问界面**: 系统启动后会自动打开浏览器
2. **输入患者ID**: 支持 P001, P002, P003
3. **选择报告类型**: 
   - 服药依从性评估 (compliance)
   - 分诊评估 (triage)
4. **生成报告**: 点击生成按钮，等待AI处理
5. **查看结果**: 点击链接预览完整报告

## 📁 目录结构

```
慢性病管理系统/
├── README.md                    # 本文件
├── SIMPLE_README.md             # 简化版说明
├── test_system.py               # 系统测试脚本
├── start_simple.py              # 一键启动脚本
├── simple_server.py             # 简化版API服务器
├── report.py                    # 命令行报告生成器
│
├── frontend/                    # 前端界面
│   ├── simple.html              # 简化版Web界面
│   ├── index.html               # 完整版管理界面
│   ├── css/                     # 样式文件
│   └── js/                      # JavaScript模块
│
├── report_modules/              # 报告生成核心模块
│   ├── __init__.py              # 工厂模式入口
│   ├── base/                    # 基础抽象类
│   ├── common/                  # 共享工具模块
│   ├── compliance/              # 依从性评估模块
│   └── triage/                  # 分诊评估模块
│
├── data/                        # 数据目录
│   └── output/
│       └── dialogue_data/       # 患者对话数据
│
└── report/                      # 报告输出目录
    └── output/                  # 生成的HTML报告
```

## 🧪 测试数据

系统内置了3个测试患者的数据：

| 患者ID | 姓名 | 年龄 | 性别 | 主要诊断 | 数据状态 |
|--------|------|------|------|----------|----------|
| P001   | 张三 | 65岁 | 男   | 2型糖尿病,高血压 | ✅ 可用 |
| P002   | 李四 | 58岁 | 女   | 高血压,冠心病 | ✅ 可用 |
| P003   | 王五 | 72岁 | 男   | 慢性肾病,糖尿病 | ✅ 可用 |

## 🔧 API接口

### 基础接口
```bash
# 健康检查
GET http://localhost:5000/api/health

# 获取患者信息
GET http://localhost:5000/api/patients/{patient_id}

# 生成报告
POST http://localhost:5000/api/generate-report
Content-Type: application/json
{
    "patientId": "P001",
    "reportType": "compliance"
}

# 查看报告
GET http://localhost:5000/api/reports/{patient_id}/{filename}
```

### 示例调用
```python
import requests

# 获取患者信息
response = requests.get('http://localhost:5000/api/patients/P001')
patient = response.json()

# 生成报告
report_request = {
    "patientId": "P001", 
    "reportType": "compliance"
}
response = requests.post('http://localhost:5000/api/generate-report', json=report_request)
result = response.json()

print(f"报告URL: http://localhost:5000{result['reportPath']}")
```

## 📊 报告类型详解

### 1. 服药依从性评估 (compliance)
- **功能**: 分析患者的服药行为和依从性
- **数据源**: 患者对话记录、用药记录
- **输出内容**:
  - 依从性评分和统计
  - 用药时间分析图表
  - 个性化建议和提醒
  - 健康指标趋势图

### 2. 分诊评估 (triage)
- **功能**: 评估患者的紧急程度和就医需求
- **数据源**: 症状描述、生理指标
- **输出内容**:
  - 风险等级评估
  - 症状严重程度分析
  - 就医建议和优先级
  - 相关医疗资源推荐

## ⚙️ 配置和自定义

### 修改患者数据
在 `simple_server.py` 中修改 `PATIENT_INFO` 字典：

```python
PATIENT_INFO = {
    'P004': {
        'id': 'P004',
        'name': '新患者',
        'age': 45,
        'gender': '女',
        'diagnosis': '高血压',
        'dataFile': 'your_data_file_id'
    }
}
```

### 自定义报告模板
报告模板位于 `report_modules/*/templates/` 目录中，支持Jinja2模板语法。

### API配置
修改 `simple_server.py` 中的配置：

```python
# 修改服务器端口
app.run(host='0.0.0.0', port=8000)

# 修改数据路径
DATA_DIR = Path('your_custom_data_path')
```

## 🐛 故障排除

### 常见问题

#### 1. 模块导入失败
**问题**: `ModuleNotFoundError: No module named 'report_modules'`

**解决方案**:
```bash
# 检查当前目录
pwd
# 应该在 report_paper 目录中

# 检查Python路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -r requirements.txt
```

#### 2. 数据文件不存在
**问题**: `患者数据文件不存在`

**解决方案**:
```bash
# 检查数据目录
ls data/output/dialogue_data/

# 运行系统测试
python test_system.py
```

#### 3. 端口被占用
**问题**: `Address already in use`

**解决方案**:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# 或修改端口号
# 在 simple_server.py 中修改 app.run(port=8000)
```

#### 4. 报告生成失败
**问题**: AI分析或图表生成错误

**解决方案**:
```bash
# 检查依赖
pip install matplotlib pandas jinja2

# 查看详细错误
python -c "
from report_modules import ReportFactory
try:
    gen = ReportFactory.create('compliance', 'test')
    print('✅ 模块正常')
except Exception as e:
    print('❌ 错误:', e)
"
```

#### 5. 浏览器访问问题
**问题**: 无法访问前端界面

**解决方案**:
- 确保使用现代浏览器
- 检查是否启用了JavaScript
- 尝试不同浏览器
- 检查防火墙设置

### 日志和调试

#### 启用详细日志
```python
# 在 simple_server.py 开头添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 查看生成过程
```bash
# 直接命令行生成报告
python report.py --id P001 --type compliance

# 查看生成的文件
ls report/output/
```

## 🚀 部署指南

### 开发环境
```bash
# 克隆项目
git clone <repository>
cd report_paper

# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_system.py

# 启动服务
python start_simple.py
```

### 生产环境
```bash
# 使用gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 simple_server:app

# 或使用Docker
docker build -t chronic-disease-reports .
docker run -p 5000:5000 chronic-disease-reports
```

## 📝 开发指南

### 添加新的报告类型
1. 在 `report_modules/` 下创建新目录
2. 实现继承自 `BaseReportGenerator` 的生成器类
3. 在 `report_modules/__init__.py` 中注册新类型

### 扩展API功能
1. 在 `simple_server.py` 中添加新的路由
2. 更新前端 JavaScript 调用
3. 添加相应的测试用例

### 自定义前端界面
- 修改 `frontend/simple.html` 的样式和布局
- 扩展 JavaScript 功能
- 添加新的交互组件

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程
1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 运行测试
5. 提交 Pull Request

## 🆕 新功能：紧迫程度分级

### 概述
自动判断患者情况是否需要医生立即介入决策的智能分级系统。

### 三级分类
- **� 紧急级 (urgent)**: 需要医生立即介入决策
  - 生理指标严重异常、危险药物漏服、多重高危因素
  - 风险评分：70-100分，建议3-7天随访
  
- **🟡 关注级 (attention)**: 需要医生定期审阅  
  - 指标轻中度异常、依从性不稳定、生活方式问题
  - 风险评分：40-69分，建议7-14天随访
  
- **🟢 稳定级 (stable)**: AI建议即可
  - 所有指标达标、依从性良好、病情稳定
  - 风险评分：0-39分，建议14-30天随访

### 核心特性
- ✅ **LLM智能评估**: 基于患者数据的AI判断
- ✅ **规则引擎校验**: 防止LLM误判的二次验证
- ✅ **医生手动调整**: 支持医生修正AI判断
- ✅ **不确定处理**: 判断不确定统一为关注级

### 快速使用

#### Python API
```python
from report_modules.compliance import urgency_classifier
from report_modules.common import data_loader

# 加载数据
memory, dialogues, df_patient = data_loader.load_patient_data(patient_id)

# 快速评估
assessment = urgency_classifier.quick_classify(
    patient_id="P001",
    memory=memory,
    df_patient=df_patient
)

print(f"级别: {assessment.get_level_text()}")
print(f"评分: {assessment.risk_score}")
print(f"理由: {assessment.reasoning}")
```

#### 测试功能
```bash
# 完整测试
python test_urgency_classifier.py

# 快速测试
python test_urgency_classifier.py --quick
```

#### API端点
```bash
# 医生手动调整紧迫程度
PATCH http://localhost:5000/api/reports/{report_id}/urgency
Content-Type: application/json
{
    "patient_id": "P001",
    "new_level": "urgent",
    "reason": "患者出现新症状"
}

# 获取紧迫程度统计
GET http://localhost:5000/api/urgency/stats
```

### 详细文档
- 📖 [功能使用文档](URGENCY_FEATURE.md)
- 📖 [技术实现文档](URGENCY_IMPLEMENTATION.md)

---

## �📞 支持

如有问题，请：
1. 查看本 README 的故障排除部分
2. 运行 `python test_system.py` 检查系统状态
3. 查看服务器日志输出
4. 提交 GitHub Issue

---

**最后更新**: 2025年10月16日
**版本**: 2.1.0 (新增紧迫程度分级功能)
**作者**: 慢性病管理系统团队