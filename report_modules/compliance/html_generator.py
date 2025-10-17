# -*- coding: utf-8 -*-
"""
依从性报告HTML生成器 - 定义依从性专用配置
"""

from pathlib import Path
from report_modules.common.html_base import HTMLBaseGenerator
from report_modules.common import config
from markdown import markdown



MODULE_DIR = Path(__file__).parent
TEMPLATE_DIR = MODULE_DIR / "templates"

class ComplianceHTMLGenerator:
    """依从性报告专用HTML生成器"""
    
    # 依从性报告额外样式（如果需要）
    COMPLIANCE_EXTRA_STYLES = """
/* 依从性报告专用样式 */
.adherence-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
}
.adherence-good { background: #d1fae5; color: #065f46; }
.adherence-warn { background: #fef3c7; color: #92400e; }
.adherence-poor { background: #fee2e2; color: #991b1b; }

/* 紧迫程度状态卡片样式 */
.urgency-banner {
    margin: 20px 0;
    padding: 20px;
    border-radius: 12px;
    border-left: 6px solid;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    page-break-inside: avoid;
}

.urgency-banner.urgency-urgent {
    background: #fef2f2;
    border-left-color: #dc2626;
}

.urgency-banner.urgency-attention {
    background: #fffbeb;
    border-left-color: #f59e0b;
}

.urgency-banner.urgency-stable {
    background: #f0fdf4;
    border-left-color: #10b981;
}

.urgency-banner .urgency-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.urgency-banner .urgency-icon {
    font-size: 32px;
}

.urgency-banner h3 {
    margin: 0;
    font-size: 20px;
    color: #111827;
}

.urgency-banner .risk-score {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    margin-left: 12px;
}

.urgency-urgent .risk-score {
    background: #dc2626;
    color: white;
}

.urgency-attention .risk-score {
    background: #f59e0b;
    color: white;
}

.urgency-stable .risk-score {
    background: #10b981;
    color: white;
}

.urgency-banner .reasoning {
    margin: 12px 0;
    font-size: 15px;
    line-height: 1.6;
    color: #374151;
}

.urgency-banner .key-concerns {
    margin: 12px 0;
}

.urgency-banner .key-concerns strong {
    color: #1f2937;
}

.urgency-banner .key-concerns ul {
    margin: 8px 0;
    padding-left: 20px;
}

.urgency-banner .key-concerns li {
    margin: 4px 0;
    color: #4b5563;
}

.urgency-banner .action-row {
    display: flex;
    gap: 20px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(0,0,0,0.1);
}

.urgency-banner .action-item {
    flex: 1;
}

.urgency-banner .action-item strong {
    display: block;
    color: #1f2937;
    margin-bottom: 4px;
}

.urgency-banner .action-item span {
    color: #4b5563;
}

.urgency-banner .verification-note {
    margin-top: 12px;
    padding: 8px 12px;
    background: rgba(0,0,0,0.05);
    border-radius: 6px;
    font-size: 13px;
    color: #6b7280;
}

.urgency-banner .verification-note.failed {
    background: #fef3c7;
    color: #92400e;
}
"""
    
    SECTION_KINDS = [
        {
            'key': 'disease',
            'includes': ['主要疾病诊断', '治疗', '诊断及治疗'],
            'tools_html': '''
                <span class="chip">处置：</span>
                <select data-k="disease.plan">
                    <option value="">无</option>
                    <option>简化</option>
                    <option>加强</option>
                    <option>改药</option>
                    <option>会诊</option>
                </select>
                <label class="chip"><input type="checkbox" data-k="disease.medChecked"> 已核对用药</label>
            '''
        },
        {
            'key': 'monitor',
            'includes': ['核心监测指标', '监测', '指标'],
            'tools_html': '''
                <span class="chip">复查安排：</span>
                <select data-k="monitor.recheck">
                    <option value="">按需要</option>
                    <option>1周</option>
                    <option>2周</option>
                    <option>4周</option>
                </select>
                <button class="btn-mini" data-act="mark-recheck" data-done-text="已标记">记为需复查</button>
            '''
        },
        {
            'key': 'adherence',
            'includes': ['依从', '依从性', '依從'],
            'tools_html': '''
                <label class="chip"><input type="checkbox" data-k="adherence.follow"> 需随访</label>
                <span class="chip">周期：</span>
                <select data-k="adherence.period">
                    <option>1周</option>
                    <option>2周</option>
                    <option selected>4周</option>
                </select>
                <button class="btn-mini" data-act="make-follow" data-done-text="已记录">记录随访任务</button>
            '''
        },
        {
            'key': 'lifestyle',
            'includes': ['生活方式', '生活', '干预'],
            'tools_html': '''
                <span class="chip">生活方式指导：</span>
                <label class="chip"><input type="checkbox" data-k="life.diet"> 饮食</label>
                <label class="chip"><input type="checkbox" data-k="life.exercise"> 运动</label>
                <label class="chip"><input type="checkbox" data-k="life.sleep"> 睡眠</label>
                <label class="chip"><input type="checkbox" data-k="life.psy"> 心理</label>
                <button class="btn-mini" data-act="lifestyle-complete" data-done-text="已完成">完成教育</button>
            '''
        },
        {
            'key': 'tips',
            'includes': ['建议', '提示', '随访建议', '治疗建议'],
            'tools_html': '''
                <span class="chip">建议采纳情况：</span>
                <select data-k="tips.overall">
                    <option value="">总体评价</option>
                    <option>完全采纳</option>
                    <option>部分采纳</option>
                    <option>需要修改</option>
                    <option>重新制定</option>
                </select>
                <label class="chip">重点关注：</label>
                <select data-k="tips.focus">
                    <option value="">选择重点</option>
                    <option>用药依从性</option>
                    <option>血压监测</option>
                    <option>血糖控制</option>
                    <option>生活方式</option>
                </select>
                <button class="btn-mini" data-act="create-plan" data-done-text="已制定">制定随访计划</button>
            '''
        },
        {
            'key': 'ai',
            'includes': ['AI', '人工智能', '综合分析', '总结', '风险评估'],
            'tools_html': '''
                <span class="chip">AI分析确认：</span>
                <select data-k="ai.summary">
                    <option value="">总结</option>
                    <option>同意</option>
                    <option>需修改</option>
                </select>
                <select data-k="ai.risk">
                    <option value="">风险评估</option>
                    <option>同意</option>
                    <option>需修改</option>
                </select>
                <select data-k="ai.recommendations">
                    <option value="">建议</option>
                    <option>同意</option>
                    <option>需修改</option>
                </select>
                <button class="btn-mini" data-act="ai-approve" data-done-text="已确认">确认分析</button>
            '''
        }
    ]
    
    @staticmethod
    def build_visuals_markdown(adherence_charts: dict) -> str:
        """构建依从性可视化部分的Markdown"""
        lines = ["\n---\n## 附：依从性可视化"]
        
        if adherence_charts.get("adherence_trend"):
            lines.append(f"![各类别依从趋势]({adherence_charts['adherence_trend']})")
        
        if adherence_charts.get("adherence_causes"):
            lines.append(f"![主要非依从原因]({adherence_charts['adherence_causes']})")
        
        if adherence_charts.get("med_adherence_trend"):
            lines.append(f"![用药依从趋势]({adherence_charts['med_adherence_trend']})")
        
        return "\n\n".join(lines)
    
    @staticmethod
    def generate_html_reports(context: dict, patient_id: str) -> tuple:
        """生成依从性报告的医生版和家属版"""
        # 查找模板
        # doctor_tpl_path = next(
        #     (p for p in [
        #         config.TPL_DIR/"doctor_template_slim.md", 
        #         config.TPL_DIR/"doctor_template.md"
        #     ] if p.exists()), 
        #     None
        # )
        doctor_tpl_path = TEMPLATE_DIR / "doctor_template.md"
        # family_tpl_path = config.TPL_DIR/"family_template.md"
        family_tpl_path = TEMPLATE_DIR / "family_template.md"        
        if not doctor_tpl_path or not family_tpl_path.exists():
            raise FileNotFoundError("缺少依从性报告模板")
        
        # 渲染Markdown → HTML
        doc_html = HTMLBaseGenerator.render_markdown_template(doctor_tpl_path, context)
        fam_html = HTMLBaseGenerator.render_markdown_template(family_tpl_path, context)
        
        # ✅ 修复：将可视化markdown转换成HTML
        visuals_md = ComplianceHTMLGenerator.build_visuals_markdown(
            context.get("charts", {})
        )
        visuals_html = markdown(visuals_md, extensions=["tables", "fenced_code"])  # ← 转换成HTML
        
        # 添加可视化HTML
        doc_html += visuals_html
        fam_html += visuals_html
        
        # 构建完整HTML（使用通用批注系统）
        doc_shell = HTMLBaseGenerator.build_html_shell(
            title="医生版报告",  # ← 改回原标题
            content=doc_html,
            patient_id=patient_id,
            report_type="compliance",
            extra_styles=ComplianceHTMLGenerator.COMPLIANCE_EXTRA_STYLES,
            section_kinds=ComplianceHTMLGenerator.SECTION_KINDS
        )
        
        fam_shell = HTMLBaseGenerator.build_html_shell(
            title="家属版报告",  # ← 改回原标题
            content=fam_html,
            patient_id=patient_id,
            report_type="compliance",
            extra_styles=ComplianceHTMLGenerator.COMPLIANCE_EXTRA_STYLES,
            section_kinds=ComplianceHTMLGenerator.SECTION_KINDS
        )
        
        return doc_shell, fam_shell