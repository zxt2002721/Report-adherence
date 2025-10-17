# 紧迫程度分级功能

## 概述

基于LLM的智能紧迫程度分级系统，自动判断患者情况是否需要医生立即介入决策。

## 分级标准

### 🔴 紧急级 (urgent)
- **定义**: 需要医生立即介入决策
- **判定条件**:
  - 生理指标严重异常（血压≥180/110，血糖≥15等）
  - 危险药物漏服率>30%
  - 出现新的严重症状或并发症
  - 多重高危因素叠加
- **风险评分**: 70-100分
- **建议随访**: 3-7天

### 🟡 关注级 (attention)
- **定义**: 需要医生定期审阅
- **判定条件**:
  - 生理指标轻中度异常
  - 服药依从性<80%
  - 生活方式有明显问题
  - 患者有疑虑或抵触情绪
- **风险评分**: 40-69分
- **建议随访**: 7-14天

### 🟢 稳定级 (stable)
- **定义**: AI建议即可，医生可选择性查看
- **判定条件**:
  - 所有指标在目标范围内
  - 服药依从性≥90%
  - 生活方式健康
  - 患者配合度高
- **风险评分**: 0-39分
- **建议随访**: 14-30天

## 技术实现

### 1. LLM评估

使用大语言模型基于患者数据进行智能判断：

```python
from report_modules.compliance import urgency_classifier

assessment = urgency_classifier.classify_urgency_with_llm(
    patient_data=patient_info,
    monitoring=monitoring_data,
    adherence=adherence_data,
    lifestyle=lifestyle_data
)

print(f"紧迫程度: {assessment.level}")
print(f"风险评分: {assessment.risk_score}/100")
print(f"判断理由: {assessment.reasoning}")
```

### 2. 规则引擎二次校验

防止LLM判断不准确，通过规则引擎进行校验：

- **生理指标检查**: 血压、血糖、心率等是否严重异常
- **依从性检查**: 用药依从性、监测依从性
- **多因素叠加**: 高危因素≥3个自动提升级别
- **风险评分匹配**: 评分与级别不符时自动调整

```python
# 规则校验会自动执行
if assessment.verification_passed:
    print("✓ 规则校验通过")
else:
    print(f"⚠️ 规则调整: {assessment.verification_notes}")
```

### 3. 不确定情况处理

当LLM判断不确定时，统一定为 **关注级(attention)**，确保医生能够审阅。

### 4. 医生手动调整

医生可以手动调整LLM的判断：

**前端调用**:
```javascript
urgencyManager.showAdjustDialog(patientId, reportId, currentLevel);
```

**API端点**:
```http
PATCH /api/reports/{report_id}/urgency
Content-Type: application/json

{
  "patient_id": "P001",
  "new_level": "urgent",
  "reason": "患者出现新症状，需要紧急处理",
  "adjusted_by": "doctor",
  "adjusted_at": "2025-10-16T10:30:00"
}
```

## 使用方式

### 在报告生成中自动评估

紧迫程度评估已集成到compliance报告生成流程：

```bash
# 生成报告时自动包含紧迫程度评估
python report.py P001 --type compliance
```

报告中会显示醒目的紧迫程度状态卡片。

### 独立评估

也可以独立调用评估功能：

```python
from report_modules.compliance import urgency_classifier
from report_modules.common import data_loader

# 加载数据
memory, dialogues, df_patient = data_loader.load_patient_data(patient_id)

# 快速评估
assessment = urgency_classifier.quick_classify(
    patient_id="P001",
    memory=memory,
    df_patient=df_patient,
    dialogues=dialogues
)

print(assessment.get_level_text())  # 🔴 紧急级
```

### 测试评估功能

运行测试脚本验证功能：

```bash
# 完整测试所有患者
python test_urgency_classifier.py

# 快速测试单个患者
python test_urgency_classifier.py --quick
```

## 前端集成

### 1. 引入JS模块

```html
<script src="js/urgency.js"></script>
```

### 2. 显示紧迫程度徽章

```javascript
// 在患者列表中显示
const badge = urgencyManager.renderUrgencyBadge('urgent', 85);
document.getElementById('urgency-badge').innerHTML = badge;
```

### 3. 显示紧迫程度卡片

```javascript
// 在报告详情中显示
const card = urgencyManager.renderUrgencyCard(urgencyData);
document.getElementById('urgency-card').innerHTML = card;
```

### 4. 医生手动调整

```javascript
// 点击按钮显示调整对话框
urgencyManager.showAdjustDialog(patientId, reportId, currentLevel);
```

### 5. 统计信息

```javascript
// 获取紧迫程度统计
const stats = urgencyManager.getUrgencyStats(reports);

// 渲染统计图表
const chart = urgencyManager.renderUrgencyStatsChart(stats);
```

## 数据结构

### UrgencyAssessment

```python
@dataclass
class UrgencyAssessment:
    level: str                      # "urgent" | "attention" | "stable"
    risk_score: int                 # 0-100
    reasoning: str                  # 判断理由
    key_concerns: list              # 关键关注点
    doctor_intervention_needed: bool # 是否需要医生介入
    suggested_action: str           # 建议行动
    follow_up_days: int             # 建议随访间隔（天）
    verification_passed: bool       # 规则校验是否通过
    verification_notes: str         # 校验说明
```

### JSON格式

```json
{
  "level": "urgent",
  "risk_score": 85,
  "reasoning": "患者血压持续偏高，近期用药依从性差...",
  "key_concerns": [
    "血压严重升高（190/105 mmHg）",
    "抗高血压药物漏服率达40%",
    "患者表示头晕、视物模糊"
  ],
  "doctor_intervention_needed": true,
  "suggested_action": "建议3天内联系医生调整用药方案",
  "follow_up_days": 3,
  "verification_passed": false,
  "verification_notes": "规则校验：检测到生理指标严重异常，提升至紧急级。"
}
```

## 配置与调优

### LLM参数

在 `urgency_classifier.py` 中调整：

```python
response = config.call_qwen_api(
    prompt=prompt,
    temperature=0.3,  # 较低温度保证判断稳定性
    max_tokens=1500
)
```

### 规则阈值

在 `_check_critical_vitals()` 和 `_check_adherence_issues()` 中调整：

```python
# 血压阈值
if latest_sbp >= 180 or latest_dbp >= 110:
    issues.append("血压严重升高")

# 依从性阈值
if compliance_rate < 50:
    issues.append("用药依从性极差")
```

### Prompt模板

编辑 `prompts/urgency_classification_prompt.md` 自定义评估标准和输出格式。

## 注意事项

1. **LLM依赖**: 需要配置可用的LLM API（Qwen）
2. **数据质量**: 评估准确性依赖于输入数据的完整性
3. **医生审核**: LLM判断仅供参考，重要决策需医生审核
4. **规则更新**: 根据实际使用反馈持续优化规则引擎
5. **日志记录**: 建议记录所有评估结果用于模型优化

## 未来扩展

- [ ] 历史趋势分析（紧迫程度变化）
- [ ] 推送通知（紧急级自动通知医生）
- [ ] 评估结果持久化
- [ ] 统计分析仪表板
- [ ] 多模型对比（不同LLM的判断差异）
- [ ] A/B测试框架

## 相关文件

### Python模块
- `report_modules/compliance/urgency_classifier.py` - 核心分类器
- `report_modules/compliance/prompts/urgency_classification_prompt.md` - LLM prompt模板
- `report_modules/compliance/generator.py` - 集成到报告生成器
- `report_modules/compliance/html_generator.py` - HTML显示样式

### 前端文件
- `frontend/js/urgency.js` - 前端管理模块
- `frontend/css/components.css` - 紧迫程度样式

### 测试文件
- `test_urgency_classifier.py` - 功能测试脚本

### API
- `simple_server.py` - 紧迫程度API端点

## 问题反馈

如有问题或建议，请联系开发团队。
