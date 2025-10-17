# 慢病阶段管理月报（家属版）

报告周期：{{ report.period }}
报告日期：{{ report.date }}

---

## 一、患者基本信息

- 姓名：{{ patient.name }}
- 年龄：{{ patient.age }} 岁
- 过敏史：{{ patient.allergies or '未记录' }}
- 疾病史：{{ patient.history or '未记录' }}

---

## 二、目前诊断与用药（含副作用提示）

- 主要诊断：{{ diagnoses|map(attribute='disease_name')|join('、') }}
- 用药数量：{{ prescription.medications|length }} 种

### 用药清单

{% for m in prescription.medications %}

- **{{ m.drug_name }}**（{{ m.category or '—' }}, {{ m.dose }}，{{ m.frequency }}）
  - 可能副作用：{{ m.side_effects or '（待补充）' }}
  - 家属需警惕的信号：{{ m.warning_signs or '（待补充）' }}
    {% endfor %}

---

## 三、重点遵从任务（家属可协助监督）

{% if compliance_tasks %}
| 任务 | 执行频率 | 家属提醒要点 |
| ---- | -------- | ------------- |
{%- for item in compliance_tasks %}
| {{ item.task }} | {{ item.frequency }} | {{ item.instructions }} |
{%- endfor %}
{% else %}
- 当前暂无重点遵从任务记录，可与医生确认关键执行事项。
{% endif %}

---

## 四、关键监测方式（家庭可执行）

- **血压**：早晚各测一次，记录数值。
- **血糖**：空腹一次、餐后一次。
- **体重**：每周一次，注意突然增减。

> 建议：把每天的测量写在本子或手机里，方便医生判断趋势。

---

## 五、管理情况与家属支持

| 日常领域 | 患者当前做法                       | 家属可以这样帮忙                 |
| -------- | ---------------------------------- | -------------------------------- |
| 作息     | {{ lifestyle.sleep or '—' }}      | {{ support.sleep or '—' }}      |
| 饮食     | {{ lifestyle.diet or '—' }}       | {{ support.diet or '—' }}       |
| 运动     | {{ lifestyle.exercise or '—' }}   | {{ support.exercise or '—' }}   |
| 心理     | {{ lifestyle.psychology or '—' }} | {{ support.psychology or '—' }} |

---

## 六、出现以下情况需要注意（危险信号）

| 监控项目  | 日常正常范围                                         | 危机信号（立即就医 / 拨打 120）                                             |
| --------- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| 血压      | {{ ranges.bp or '收缩压90-140 / 舒张压60-90 mmHg' }} | {{ warnings.bp or '收缩压≥180 或 舒张压≥110，伴剧烈头痛/视物模糊/呕吐' }} |
| 血糖      | {{ ranges.bg or '空腹4-7 mmol/L；餐后<10 mmol/L' }}  | {{ warnings.bg or '低血糖<3.9伴出汗心慌；高血糖>16.7伴口渴频尿嗜睡' }}      |
| 胸部症状  | {{ ranges.chest or '无胸闷、胸痛' }}                 | {{ warnings.chest or '胸痛≥5分钟并放射，伴出汗、气短' }}                   |
| 神经症状  | {{ ranges.neuro or '语言/肢体/表情正常' }}           | {{ warnings.neuro or '口齿不清、单侧无力/麻木、突发剧烈头痛' }}             |
| 足部皮肤  | {{ ranges.foot or '完整无破溃' }}                    | {{ warnings.foot or '小伤口>24h不愈、流脓或坏死' }}                         |
| 体重/水肿 | {{ ranges.weight or '体重稳定，小腿不肿' }}          | {{ warnings.weight or '3-5天内突然增加≥2kg，或踝/小腿肿胀伴呼吸困难' }}    |
| 用药依从  | {{ ranges.medication or '按时按量服药' }}            | {{ warnings.medication or '连续漏服>1次；黑便、呕血、严重皮疹、黄疸' }}     |
| 情绪状态  | {{ ranges.psychology or '心情平稳，睡眠正常' }}      | {{ warnings.psychology or '持续抑郁>2周；明显焦虑、失眠、提及轻生念头' }}   |

---

## 七、下次随访

- 建议随访时间：{{ followup.next_visit or '（待补充）' }}
- 需带材料：{{ followup.documents or '血压/血糖记录本、近期检查报告' }}
