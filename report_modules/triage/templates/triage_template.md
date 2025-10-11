# 分诊评估报告

## 一、基本信息

* **患者ID:** {{ patient_id }}
* **性别:** {{ patient_info.sex }}
* **年龄:** {{ patient_info.age }}
* **主诉:** {{ patient_info.chief_complaint }}
* **过敏史:** {{ medical_history.allergies_str }}
* **既往史:** {{ medical_history.diagnoses_str }}
* **当前用药:** {{ medical_history.medications_str }}
---
## 二、急诊生命体征

* **体温:** {{ vital_signs.temperature }}°F
* **心率:** {{ vital_signs.heartrate }} 次/分
* **呼吸:** {{ vital_signs.resprate }} 次/分
* **血氧:** {{ vital_signs.o2sat }}%
* **血压:** {{ vital_signs.sbp }}/{{ vital_signs.dbp }} mmHg
---

## 三、AI分诊决策

<h4>问诊摘要</h4>
<div class="summary{% if not pre_triage_summary %} empty{% endif %}">
    {{ pre_triage_summary if pre_triage_summary else '⚠️ 暂无分诊前摘要' }}
</div>

<h4>3.2 初步判断与ESI分级</h4>
<div class="decision-interactive">
    <div class="form-group">
        <label for="judgment-select">初步判断:</label>
        {# ✅ 使用您提供的 select 下拉框，并添加一个 class 用于JS选择 #}
        <select id="judgment-select" class="path-switcher-select" data-k="judgment.final">
            <option value="yes" {% if go_to_hospital.chose|string == 'yes' %}selected{% endif %}>建议立即就医</option>
            <option value="no" {% if go_to_hospital.chose|string == 'no' %}selected{% endif %}>可居家观察</option>
        </select>
    </div>
    <div class="form-group">
        <label for="esi-select">ESI等级:</label>
        <select id="esi-select" data-k="esi.level">
            {# ✅ 关键修正：使用 |string 过滤器，并将 esi 值转为整数部分进行比较 #}
            <option value="1" {% if vital_signs.esi|float|int|string == '1' %}selected{% endif %}>1 - 需抢救</option>
            <option value="2" {% if vital_signs.esi|float|int|string == '2' %}selected{% endif %}>2 - 高危</option>
            <option value="3" {% if vital_signs.esi|float|int|string == '3' %}selected{% endif %}>3 - 紧急</option>
            <option value="4" {% if vital_signs.esi|float|int|string == '4' %}selected{% endif %}>4 - 次紧急</option>
            <option value="5" {% if vital_signs.esi|float|int|string == '5' %}selected{% endif %}>5 - 非紧急</option>
        </select>
    </div>
</div>


<div id="path-immediate-care">  {# <<< 为“立即就医”路径的容器添加 ID #}
    <h4>3.3 资源判断</h4>
    <div class="decision-interactive">
        {# <<< 关键修改：直接渲染初始推荐的资源列表 #}
        <div id="resource-display-area" class="resource-display-area">
            <p style="margin:0; font-weight:bold;">模型推荐资源:</p>
            <ul class="resource-list">
            {% for category, resources in resource_details.items() %}
                <li><strong>{{ category }}:</strong> 
                {# 使用 for 循环展示每个资源 #}
                {% for resource in resources %}<span class="resource-item">{{ resource.name }}</span>{% endfor %}
                </li>
            {% else %}
                <li>暂无模型推荐资源。</li>
            {% endfor %}
            </ul>
        </div>
        <button class="btn-mini" data-act="edit-resources">📝 编辑资源</button>
    </div>
    
    <h4>3.4 最大等待时间</h4>
    <div class="decision-interactive">
        <label for="time-select">最大等待时间:</label>
        <select id="time-select" data-k="time.max">
            <option value="0" {% if max_time_to_doctor.chose|string == '0' %}selected{% endif %}>立即</option>
            <option value="10" {% if max_time_to_doctor.chose|string == '10' %}selected{% endif %}>10分钟内</option>
            <option value="30" {% if max_time_to_doctor.chose|string == '30' %}selected{% endif %}>30分钟内</option>
            <option value="60" {% if max_time_to_doctor.chose|string == '60' %}selected{% endif %}>60分钟内</option>
            <option value="120" {% if max_time_to_doctor.chose|string == '120' %}selected{% endif %}>120分钟内</option>
        </select>
    </div>

    <h4>3.5 恶化风险</h4>
    <div class="decision-interactive">
        <label for="risk-select">恶化风险:</label>
        <select id="risk-select" data-k="risk.deterioration">
            <option value="低" {% if deterioration_risk.chose|string == '低' %}selected{% endif %}>低风险</option>
            <option value="中" {% if deterioration_risk.chose|string == '中' %}selected{% endif %}>中风险</option>
            <option value="高" {% if deterioration_risk.chose|string == '高' %}selected{% endif %}>高风险</option>
        </select>
    </div>
<h4>3.6 医院推荐</h4>

{% if hospital_recommendation and hospital_recommendation.recommendations %}
    {% for rec in hospital_recommendation.recommendations %}
    <div class="hospital-recommendation" data-priority="{{ rec.priority }}">
        <div class="hospital-header">
            <span class="priority-badge">推荐 {{ rec.priority }}</span>
            <h5>{{ rec.hospital_info.name }} ({{ rec.hospital_info.level }})</h5>
            {% if hospital_recommendation.system_suggested == rec.priority %}
            <span class="badge badge-esi">系统推荐</span>
            {% endif %}
        </div>
        
        <div class="hospital-details">
            <p><strong>🏥 急诊状态：</strong>{{ rec.hospital_info.emergency_dept_status }}</p>
            <p><strong>⏱️ 预计总等待时间：</strong>{{ rec.wait_time.total_estimated_min }} 分钟</p>
            <p><strong>📋 排队情况：</strong>{{ rec.wait_time.queue_position }}</p>
            
            <p><strong>🔬 资源匹配度：</strong>
                <span class="badge {% if rec.resource_match.match_rate == 100 %}badge-high{% elif rec.resource_match.match_rate >= 70 %}badge-medium{% else %}badge-low{% endif %}">
                    {{ rec.resource_match.match_rate }}%
                </span>
            </p>
            
            {% if rec.resource_match.critical_resources_with_names %}
            <div class="critical-info">
                <strong>✅ 关键资源可用：</strong><br>
                {% for res in rec.resource_match.critical_resources_with_names %}
                <span class="resource-item" style="display:inline-block; margin:4px 4px 4px 0;">{{ res.name }}</span>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if rec.resource_match.missing_resources_with_names %}
            <div class="warning-info">
                <strong>⚠️ 缺少资源：</strong><br>
                {% for res in rec.resource_match.missing_resources_with_names %}
                <span class="resource-item" style="display:inline-block; margin:4px 4px 4px 0; background:#fff;">{{ res.name }}</span>
                {% endfor %}
            </div>
            {% endif %}
            
            <details>
                <summary><strong>📋 推荐理由</strong></summary>
                <p style="margin-top:8px; line-height:1.6;">{{ rec.recommendation_reason }}</p>
            </details>
            
            <details>
                <summary><strong>⚖️ 优劣势分析</strong></summary>
                <div style="margin-top:8px;">
                    <p><strong>优势：</strong></p>
                    <ul>
                    {% for pro in rec.pros_cons.优势 %}
                        <li>{{ pro }}</li>
                    {% endfor %}
                    </ul>
                    <p><strong>劣势：</strong></p>
                    <ul>
                    {% for con in rec.pros_cons.劣势 %}
                        <li>{{ con }}</li>
                    {% endfor %}
                    </ul>
                </div>
            </details>
            
            <p><strong>🚨 风险评估：</strong><br>
                转院风险: <span class="risk-{{ rec.risk_assessment.transfer_risk }}">{{ rec.risk_assessment.transfer_risk }}</span> | 
                延误风险: <span class="risk-{{ rec.risk_assessment.delay_risk }}">{{ rec.risk_assessment.delay_risk }}</span> | 
                资源不可用风险: <span class="risk-{{ rec.risk_assessment.resource_unavailable_risk }}">{{ rec.risk_assessment.resource_unavailable_risk }}</span>
            </p>
        </div>
        
        <div class="decision-interactive">
            <label class="chip">
                <input type="checkbox" data-k="hospital.approve_priority_{{ rec.priority }}"
                {% if hospital_recommendation.system_suggested == rec.priority %}checked{% endif %}> 
                批准此推荐
            </label>
        </div>
    </div>
    {% endfor %}

    <div class="decision-interactive" style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:10px;">
        <label for="final-hospital-select" style="display:block; margin-bottom:8px;"><strong>👨‍⚕️ 医生最终决定：</strong></label>
        <select id="final-hospital-select" data-k="hospital.final_choice" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border);">
            <option value="">-- 请选择医院 --</option>
            {% for rec in hospital_recommendation.recommendations %}
            <option value="{{ rec.priority }}" 
                {% if hospital_recommendation.system_suggested == rec.priority %}selected{% endif %}>
                推荐{{ rec.priority }}: {{ rec.hospital_info.name }} ({{ rec.hospital_info.level }})
            </option>
            {% endfor %}
        </select>
    </div>

    {% if hospital_recommendation.suggestion_basis %}
    <details style="margin-top:16px; padding:12px; background:var(--card); border-radius:8px;">
        <summary style="cursor:pointer; font-weight:600; color:var(--btn);"><strong>🤖 系统决策依据</strong></summary>
        <div style="margin-top:12px;">
            <p><strong>ESI等级：</strong>{{ hospital_recommendation.suggestion_basis.esi_level }}</p>
            <p><strong>关键决策因素：</strong></p>
            <ul>
            {% for factor in hospital_recommendation.suggestion_basis.key_decision_factors %}
                <li>{{ factor }}</li>
            {% endfor %}
            </ul>
        </div>
    </details>
    {% endif %}

{% else %}
    <div class="warning-info">
        ⚠️ 暂无医院推荐信息
    </div>
{% endif %}

---


<div id="path-home-observation"> {# <<< 为“居家观察”路径的容器添加 ID #}
    <h4>3.3 建议复查时间</h4>
    <div class="decision-interactive">
        <label for="followup-select">复查时间:</label>
        <select id="followup-select" data-k="followup.time">
            <option value="12" {% if followup_time.chose|string == '12' %}selected{% endif %}>12小时内</option>
            <option value="24" {% if followup_time.chose|string == '24' %}selected{% endif %}>24小时内</option>
            <option value="48" {% if followup_time.chose|string == '48' %}selected{% endif %}>48小时内</option>
        </select>
    </div>
    
    <h4>3.4 居家护理措施</h4>
    <div class="decision-interactive">
        <span>模型建议了 {{ care_measures.chose|length }} 项措施。</span>
        <button class="btn-mini" data-act="edit-care-measures">📝 编辑护理措施</button>
    </div>

    <h4>3.5 警告信号</h4>
    <div class="decision-interactive">
        <span>模型建议了 {{ warning_signs.chose|length }} 项警告信号。</span>
        <button class="btn-mini" data-act="edit-warning-signs">📝 编辑警告信号</button>
    </div>

    <h4>3.6 居家恶化风险</h4>
    <div class="decision-interactive">
        <label for="home-risk-select">恶化风险:</label>
        <select id="home-risk-select" data-k="risk.home_deterioration">
            <option value="低" {% if home_deterioration_risk.chose|string == '低' %}selected{% endif %}>低风险</option>
            <option value="中" {% if home_deterioration_risk.chose|string == '中' %}selected{% endif %}>中风险</option>
            <option value="高" {% if home_deterioration_risk.chose|string == '高' %}selected{% endif %}>高风险</option>
        </select>
    </div>
</div>


<h4>3.7 急诊就诊记录确认</h4>

<div class="physician-approval-form">
    <table class="approval-table">
        <tr>
            <td style="width:30%; font-weight:600;">记录生成时间：</td>
            <td>{{ report_generated_time }}</td>
        </tr>
        <tr>
            <td style="font-weight:600;">记录人：</td>
            <td>
                <input type="text" class="form-input" data-k="approval.recorder_name" 
                       placeholder="请输入记录人姓名" style="width:100%; padding:6px; border:1px solid var(--border); border-radius:4px;">
            </td>
        </tr>
        <tr>
            <td style="font-weight:600;">科室/地点：</td>
            <td>
                <input type="text" class="form-input" data-k="approval.location" 
                       placeholder="请输入科室或地点" style="width:100%; padding:6px; border:1px solid var(--border); border-radius:4px;">
            </td>
        </tr>
        <tr>
            <td style="font-weight:600;">分诊评估审核：</td>
            <td>
                <label style="margin-right:20px;">
                    <input type="radio" name="triage-review" value="agree" data-k="approval.triage_review"> 同意
                </label>
                <label>
                    <input type="radio" name="triage-review" value="disagree" data-k="approval.triage_review"> 不同意
                </label>
            </td>
        </tr>
        <tr>
            <td style="font-weight:600;">医生签名：</td>
            <td>
                <input type="text" class="form-input signature-input" data-k="approval.physician_signature" 
                       placeholder="请输入医生姓名" style="width:100%; padding:6px; border:1px solid var(--border); border-radius:4px; font-style:italic;">
            </td>
        </tr>
    </table>
</div>