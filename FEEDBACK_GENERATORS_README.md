# 智能健康反馈生成器套件

本项目包含三个不同功能的AI驱动反馈生成器，用于分析医生的诊疗批注并生成不同受众和用途的反馈报告。

## 功能概述

### 1. 医生反馈生成器 (`generate_doctor_feedback.py`)
**目标受众**：医生、医疗管理者  
**功能**：分析医生的诊疗决策质量，提供专业改进建议  
**数据来源**：仅医生批注和交互数据

**分析维度**：
- 🔍 **诊疗质量评估**：临床思维、治疗方案、安全考虑、随访计划、沟通质量
- 🎯 **诊疗风格分析**：诊疗风格、决策倾向、风险承受度、干预偏好
- 📚 **学习资源推荐**：临床指南、培训课程、病例讨论、技能发展

### 2. 患者健康报告生成器 (`generate_patient_health_report.py`)
**目标受众**：患者、家属  
**功能**：将医生的专业批注转换为患者友好的健康指导  
**数据来源**：仅医生批注和交互数据

**反馈内容**：
- 📋 **健康状况总览**：用温和语言描述健康状况
- 💊 **用药指导**：用药情况和注意事项
- 🌟 **生活方式建议**：饮食、运动、作息指导
- 📊 **监测计划**：检查安排和自我监测方法

### 3. 综合患者健康报告生成器 (`generate_comprehensive_patient_report.py`) ⭐ **推荐**
**目标受众**：患者、家属  
**功能**：结合原始报告数据和医生批注，生成包含修改说明的综合健康报告  
**数据来源**：原始患者数据 + 医生批注和交互数据

**独特优势**：
- � **修改对比分析**：详细说明医生做了哪些专业调整
- � **数据图表展示**：包含原始健康数据的可视化图表
- 🩺 **全面健康评估**：结合客观数据和主观判断
- 💡 **调整说明**：解释医生修改的临床意义和患者影响

## 三种生成器的对比

| 特性 | 医生反馈生成器 | 患者健康报告生成器 | **综合患者健康报告生成器** |
|------|---------------|-------------------|------------------------|
| **目标受众** | 医生/管理者 | 患者/家属 | **患者/家属** |
| **数据来源** | 仅批注数据 | 仅批注数据 | **原始数据+批注数据** |
| **报告重点** | 质量评估打分 | 健康指导 | **修改说明+健康指导** |
| **包含图表** | ❌ | ❌ | **✅** |
| **修改对比** | ❌ | ❌ | **✅** |
| **临床解释** | 专业术语 | 通俗语言 | **通俗+专业解释** |
| **推荐指数** | ⭐⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |

## 使用方法

### 医生反馈生成

```bash
# 基于患者ID生成医生质量反馈
python generate_doctor_feedback.py --patient-id 患者ID --doctor-name "张医生"

# 使用下载文件夹中最新的批注文件
python generate_doctor_feedback.py --downloads --doctor-name "张医生"
```

### 患者健康报告生成

```bash
# 基于批注数据生成患者健康指导
python generate_patient_health_report.py --patient-id 患者ID --patient-name "李先生"

# 使用下载文件夹中最新的批注文件
python generate_patient_health_report.py --downloads --patient-name "李先生"
```

### 综合患者健康报告生成 ⭐ **推荐使用**

```bash
# 生成包含原始数据和修改说明的综合报告
python generate_comprehensive_patient_report.py --patient-id 患者ID --patient-name "李先生"

# 使用下载文件夹中最新的批注文件
python generate_comprehensive_patient_report.py --downloads --patient-name "李先生"

# 自定义输出路径
python generate_comprehensive_patient_report.py --downloads --output "综合健康报告.html"
```

## 输出文件说明

### 医生反馈报告
- **HTML**：`doctor_feedback_患者ID_时间戳.html`
- **JSON**：`doctor_feedback_患者ID_时间戳.json`
- **内容**：评分、分析、建议、学习资源

### 患者健康报告
- **HTML**：`patient_health_report_患者ID_时间戳.html`
- **JSON**：`patient_health_report_患者ID_时间戳.json`
- **内容**：健康状况、用药指导、生活建议、监测计划

### 综合患者健康报告 ⭐
- **HTML**：`comprehensive_patient_report_患者ID_时间戳.html`
- **JSON**：`comprehensive_patient_report_患者ID_时间戳.json`
- **内容**：
  - 📋 患者基本信息
  - 🔄 医生专业调整说明
  - 📊 健康数据图表
  - 🩺 综合健康状况评估
  - � 用药指导（含调整说明）
  - 🌟 生活方式和监测计划

## 完整工作流程

### 推荐流程（使用综合报告）
1. **生成原始医生报告**：
   ```bash
   python report.py --id 患者ID
   ```

2. **医生添加专业批注**：
   - 在生成的HTML报告中添加批注和交互记录
   - 使用"导出批注与交互数据"功能

3. **生成综合患者健康报告**：
   ```bash
   python generate_comprehensive_patient_report.py --downloads --patient-name "患者姓名"
   ```

4. **可选：生成医生质量反馈**：
   ```bash
   python generate_doctor_feedback.py --downloads --doctor-name "医生姓名"
   ```

### 数据流程图
```
原始数据 → 医生报告 → 医生批注 → 导出JSON → AI分析 → 综合反馈
   ↓         ↓         ↓         ↓         ↓        ↓
患者数据 → report.py → 交互HTML → annotations → 对比分析 → 患者报告
                                    ↓
                                医生质量反馈
```

## 关键特性

### AI分析能力
- **对比分析**：智能对比原始数据与医生调整
- **修改解释**：解释医生调整的临床意义
- **个性化建议**：基于具体数据生成建议
- **多维度评估**：健康、用药、生活方式全覆盖

### 数据处理
- **双数据源**：结合原始数据和批注数据
- **智能匹配**：自动查找相关文件
- **容错处理**：缺失数据时的优雅降级
- **格式兼容**：支持多种数据输入格式

### 用户体验
- **响应式设计**：适配各种设备
- **视觉友好**：清晰的图表和布局
- **分层信息**：从概览到详细的信息层次
- **行动指导**：具体可执行的建议

## 技术架构

### 核心组件
```
综合报告生成器
├── 原始数据加载器 (load_original_report_data)
├── 对比分析器 (compare_original_vs_annotations)
├── 健康总结生成器 (generate_comprehensive_health_summary)
├── 用药指导生成器 (generate_medication_guidance_with_changes)
├── 生活监测计划器 (generate_lifestyle_and_monitoring_plan)
└── HTML渲染器 (generate_comprehensive_patient_html)
```

### AI模型集成
- **模型**：Qwen-3-4B
- **API**：OpenAI兼容接口
- **提示工程**：针对医疗场景优化
- **容错机制**：多级备用方案

## 配置说明

### AI配置
```python
# config.py 中的配置
client = OpenAI(
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

### 输出目录
- 默认输出：`report/output/`
- 支持自定义路径
- 自动创建目录结构

## 最佳实践

### 使用建议
1. **首选综合报告**：包含最完整的信息
2. **批注要详细**：医生批注越详细，分析越准确
3. **定期生成**：每次调整后重新生成报告
4. **保存历史**：JSON文件便于追踪变化

### 注意事项
- 确保患者数据完整性
- 医生批注的专业性直接影响分析质量
- 定期更新AI提示词以提高分析准确性
- 注意患者隐私保护

## 扩展开发

### 添加新的分析维度
```python
def analyze_new_dimension(self, original_context, annotation_data):
    # 实现新的分析逻辑
    pass
```

### 自定义HTML模板
修改 `generate_comprehensive_patient_html` 函数来自定义报告样式。

### 集成其他数据源
扩展 `load_original_report_data` 函数来支持更多数据来源。

---

**推荐使用**：`generate_comprehensive_patient_report.py` 生成最完整的患者健康报告！

**技术支持**：如有问题请查看代码注释或联系开发团队。
