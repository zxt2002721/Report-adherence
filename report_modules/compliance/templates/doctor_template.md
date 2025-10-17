# 慢病阶段管理月报（医生版）

## 🚨 紧迫程度评估

<div class="urgency-banner urgency-{{ urgency.level }}">
    <div class="urgency-header">
        <span class="urgency-icon">
            {% if urgency.level == "urgent" %}🔴
            {% elif urgency.level == "attention" %}🟡
            {% else %}🟢
            {% endif %}
        </span>
        <div>
            <h3>{{ urgency.get_level_text() }}</h3>
            <span class="risk-score">风险评分：{{ urgency.risk_score }}/100</span>
        </div>
    </div>
    
    <p class="reasoning"><strong>判断理由：</strong>{{ urgency.reasoning }}</p>
    
    <div class="key-concerns">
        <strong>关键关注点：</strong>
        <ul>
            {% for concern in urgency.key_concerns %}
            <li>{{ concern }}</li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="action-row">
        <div class="action-item">
            <strong>建议行动：</strong>
            <span>{{ urgency.suggested_action }}</span>
        </div>
        <div class="action-item">
            <strong>建议随访间隔：</strong>
            <span>{{ urgency.follow_up_days }} 天</span>
        </div>
        <div class="action-item">
            <strong>需要医生介入：</strong>
            <span>{% if urgency.doctor_intervention_needed %}是 ✓{% else %}否{% endif %}</span>
        </div>
    </div>
    
    {% if not urgency.verification_passed %}
    <div class="verification-note failed">
        ⚠️ 规则校验调整：{{ urgency.verification_notes }}
    </div>
    {% endif %}
</div>

---

## 一、基本信息

- 姓名：{{ patient.name }}
- 性别：{{ patient.gender }}
- 年龄：{{ patient.age }}
- 职业：{{ patient.occupation }}
- 文化程度：{{ patient.education }}
- 家庭情况：{{ patient.family }}
- 联系方式：{{ patient.phone }}
- 过敏史：{{ patient.allergies }}
- 既往史：{{ patient.history }}
- 家庭支持情况：{{ patient.support }}

---

## 二、主要疾病诊断及治疗

{% for d in disease_info.primary_diseases %}

- 疾病名称：{{ d.disease_name }} （ICD10: {{ d.icd10_code }}）
  - 当前病情：{{ d.current_severity }}
  - 当前用药：{{ d.current_medications_text }}
  - 与指南推荐：{{ d.guideline_recommended }}
  - 一致性评价：{{ d.consistency }}
    {% endfor %}

---

---

## 三、核心监测指标

| 指标     | 当前值                  | 推荐目标             | 是否达标            |
| -------- | ----------------------- | -------------------- | ------------------- |
| 血压     | {{ monitoring.bp }}     | {{ targets.bp }}     | {{ status.bp }}     |
| 空腹血糖 | {{ monitoring.bg }}     | {{ targets.bg }}     | {{ status.bg }}     |
| HbA1c    | {{ monitoring.hba1c }}  | {{ targets.hba1c }}  | {{ status.hba1c }}  |
| LDL-C    | {{ monitoring.ldl }}    | {{ targets.ldl }}    | {{ status.ldl }}    |
| BMI      | {{ monitoring.bmi }}    | {{ targets.bmi }}    | {{ status.bmi }}    |
| 心率     | {{ monitoring.hr }}     | {{ targets.hr }}     | {{ status.hr }}     |
| 肾功能   | {{ monitoring.kidney }} | {{ targets.kidney }} | {{ status.kidney }} |

### 指标趋势图

#### 血压变化

![]({{ charts.bp_trend }})

#### 血糖变化

![]({{ charts.glucose_trend }})

#### 体重/BMI/心率对比

![]({{ charts.monthly_comparison }})

---

## 四、生活方式处方

- 饮食：{{ lifestyle.diet }}
- 运动：{{ lifestyle.exercise }}
- 睡眠：{{ lifestyle.sleep }}
- 心理：{{ lifestyle.psychology }}

---

## 五、依从性与APP使用情况

- 打卡情况：{{ app.checkins }}
- 症状反馈：{{ app.symptoms }}
- 在线咨询：{{ app.consultations }}
- 问卷完成情况：{{ app.surveys }}
- 依从性总体：{{ app.adherence }}

### 依从性趋势图

![]({{ charts.adherence_trend }})

---

## 六、重点遵从任务清单

{% if compliance_tasks %}
| 任务 | 执行频率 | 核心说明 |
| ---- | -------- | -------- |
{%- for item in compliance_tasks %}
| {{ item.task }} | {{ item.frequency }} | {{ item.instructions }} |
{%- endfor %}
{% else %}
- 当前暂无重点遵从任务记录，建议结合随访完善关键任务。
{% endif %}

---

## 七、健康管理提示（来源：{{ tips_source }}）

### 1. 用药管理

- 状态：{{ tips.medication.state }}
- 建议：{{ tips.medication.advice }}
- 医生补充：{{ tips.medication.doctor }}
- 风险提示：{{ tips.medication.risk }}

### 2. 指标监测

- 状态：{{ tips.monitoring.state }}
- 建议：{{ tips.monitoring.advice }}
- 医生补充：{{ tips.monitoring.doctor }}
- 风险提示：{{ tips.monitoring.risk }}

### 3. 运动与康复

- 状态：{{ tips.exercise.state }}
- 建议：{{ tips.exercise.advice }}
- 医生补充：{{ tips.exercise.doctor }}
- 风险提示：{{ tips.exercise.risk }}

### 4. 饮食管理

- 状态：{{ tips.diet.state }}
- 建议：{{ tips.diet.advice }}
- 医生补充：{{ tips.diet.doctor }}
- 风险提示：{{ tips.diet.risk }}

### 5. 心理与家庭支持

- 状态：{{ tips.psychology.state }}
- 建议：{{ tips.psychology.advice }}
- 医生补充：{{ tips.psychology.doctor }}
- 风险提示：{{ tips.psychology.risk }}

---

## 八、AI 综合分析

- 总结：{{ ai.summary }}
- 风险评估：{{ ai.risk_assessment }}
- 个性化建议：{{ ai.recommendations }}

---

## 九、参考文献

{% for ref in references %}

- {{ ref }}
  {% endfor %}

---

> 报告生成日期：{{ report.date }}
> 报告周期：{{ report.period }}
