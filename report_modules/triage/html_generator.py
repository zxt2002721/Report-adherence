# report_modules/triage/html_generator.py

from pathlib import Path
from report_modules.common.html_base import HTMLBaseGenerator
from report_modules.triage.constants import get_resources_json
import json

MODULE_DIR = Path(__file__).parent
TEMPLATE_DIR = MODULE_DIR / "templates"

class TriageHTMLGenerator:
    """分诊报告HTML生成器（职责分离最终版）"""

    @staticmethod
    def _get_extra_styles() -> str:
        """分诊报告的专属样式"""
        return """
        /* === 分诊报告专属样式 === */
        .decision {
            padding: 15px; border-radius: 8px; margin: 1.2em 0;
            border-left: 5px solid var(--bar); background: var(--card);
        }
        .summary.empty { background: #fff3cd; color: #856404; }
        .evidence {
            font-size: 0.9em; color: var(--muted); margin-top: 8px;
            padding-left: 15px; border-left: 3px solid var(--border);
        }
        .badge {
            display: inline-block; padding: 4px 12px; border-radius: 12px;
            font-size: 0.9em; font-weight: bold; color: white;
        }
        .badge-yes, .badge-high, .badge-高 { background: var(--warn); }
        .badge-no, .badge-low, .badge-低 { background: var(--pri); }
        .badge-medium, .badge-中 { background: #f39c12; }
        .badge-esi { background: var(--btn); }

        .resource-display-area { width: 100%; }
        .resource-list { list-style-type: none; padding-left: 0; font-size: 0.9em; }
        .resource-list li { margin-bottom: 5px; }
        .resource-item {
            display: inline-block; padding: 2px 8px; background: var(--card);
            border: 1px solid var(--border); border-radius: 6px; margin: 2px;
        }
        .resource-item.added-by-user {
            background: #fee2e2; color: #991b1b;
            border-color: #fecaca; font-weight: bold;
        }

        /* === 医院推荐样式 === */
        .hospital-recommendation {
            background: #fff; border: 1px solid var(--border);
            border-radius: 10px; padding: 16px; margin: 16px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .hospital-recommendation[data-priority="1"] {
            border-left: 5px solid #2e7d32;
        }
        .hospital-recommendation[data-priority="2"] {
            border-left: 5px solid #0ea5e9;
        }
        .hospital-header {
            display: flex; align-items: center; gap: 12px;
            margin-bottom: 12px; flex-wrap: wrap;
        }
        .hospital-header h5 {
            margin: 0; font-size: 1.1em; color: #111;
        }
        .priority-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 4px 10px; border-radius: 12px;
            font-size: 0.85em; font-weight: bold;
        }
        .hospital-details {
            line-height: 1.8; color: var(--fg-soft);
        }
        .hospital-details p {
            margin: 6px 0;
        }
        .hospital-details strong {
            color: var(--fg);
        }
        .hospital-details code {
            background: #f1f5f9; padding: 2px 6px; border-radius: 4px;
            font-size: 0.9em; color: #0ea5e9;
        }
        .critical-info {
            background: #e9f5eb; padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid var(--pri);
        }
        .warning-info {
            background: #fff3cd; padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid #f39c12; color: #856404;
        }
        .hospital-details details {
            margin: 10px 0; padding: 10px;
            background: var(--card); border-radius: 8px;
        }
        .hospital-details summary {
            cursor: pointer; font-weight: 600;
            color: var(--btn); user-select: none;
        }
        .hospital-details summary:hover {
            color: var(--btn-hover);
        }
        .hospital-details ul {
            margin: 8px 0; padding-left: 20px;
        }
        .hospital-details li {
            margin: 4px 0;
        }
        .risk-无, .risk-极低 { color: var(--pri); font-weight: bold; }
        .risk-低 { color: #2e7d32; }
        .risk-中, .risk-中等 { color: #f39c12; font-weight: bold; }
        .risk-高 { color: var(--warn); font-weight: bold; }

        /* === 资源编辑器弹窗 (Modal) 样式 === */
        body.modal-open { overflow: hidden; }
        .resource-modal {
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0;
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.6);
            z-index: 10000; 
            align-items: center; 
            justify-content: center;
        }
        .resource-modal-content {
            background: white; width: 90%; max-width: 800px;
            border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: flex; flex-direction: column; max-height: 85vh;
        }
        .resource-modal-header {
            padding: 16px 24px; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .resource-modal-header h3 { margin: 0; font-size: 1.2em; }
        .resource-modal-body { padding: 24px; overflow-y: auto; }
        .resource-modal-footer {
            padding: 16px 24px; border-top: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items:center; gap: 12px;
            background: var(--card);
        }
        .resource-modal-footer button {
            padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);
            background: #fff; cursor: pointer; font-size: 14px; transition: background 0.2s;
        }
        .resource-modal-footer button:hover { background: #e9ecef; }
        .resource-modal-footer button.primary {
            background: var(--btn); color: #fff; border-color: var(--btn);
        }
        .resource-modal-footer button.primary:hover { background: var(--btn-hover); }
        .resource-modal-body h4 {
            color:#34495e; margin-bottom:10px; font-size:1.1em;
        }
        .resource-modal-body label {
            display: block; padding: 8px 12px; margin-bottom: 5px; 
            background: #f8f9fa; border-radius: 6px; cursor: pointer;
            transition: background 0.2s; display: flex; align-items: center;
        }
        .resource-modal-body label:hover {
            background: #e9ecef;
        }
        .resource-modal-body input[type="checkbox"] {
            margin-right: 10px; width: 16px; height: 16px;
        }
        .system-badge {
            color:var(--btn); font-size:0.8em; margin-left:8px; font-weight: 500;
        }

        /* === 医生审批表单样式 === */
        .physician-approval-form {
            background: #fff;
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .approval-table {
            width: 100%;
            border-collapse: collapse;
        }
        .approval-table td {
            padding: 12px 8px;
            border-bottom: 1px solid #e9ecef;
        }
        .approval-table tr:last-child td {
            border-bottom: none;
        }
        .form-input {
            font-family: inherit;
            font-size: 14px;
        }
        .signature-input {
            border-bottom: 2px solid #0ea5e9 !important;
            background: #f8f9fa;
        }
        .approval-table input[type="radio"] {
            margin-right: 6px;
            transform: scale(1.2);
        }
        """
    SECTION_KINDS = []
    @staticmethod
    def render_and_build_report(context: dict, patient_id: str) -> str:
        from datetime import datetime
        
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        template_path = TEMPLATE_DIR / "triage_template.md"
        report_content_html = HTMLBaseGenerator.render_markdown_template(template_path, context)

        all_resources_json = get_resources_json()
        suggested_ids_json = json.dumps(context.get('system_resources', []))
        
        modal_html = TriageHTMLGenerator._get_resource_editor_modal()
        final_content = f"{report_content_html}{modal_html}"

        return HTMLBaseGenerator.build_html_shell(
            title=f"分诊报告 - {patient_id}",
            content=final_content,
            patient_id=patient_id,
            report_type='triage',
            report_id=report_id,  # ✅ 已有report_id
            section_kinds=TriageHTMLGenerator.SECTION_KINDS,
            extra_styles=TriageHTMLGenerator._get_extra_styles(),
            triage_resources_data={  # ✅ 正确：通过triage_resources_data字典传递
                'all_resources_json': all_resources_json,
                'suggested_ids_json': suggested_ids_json
            }
        )
    @staticmethod
    def _get_resource_editor_modal() -> str:
        """资源编辑模态框HTML，现在只负责提供纯净的HTML结构"""
        return """
        <div id="resourceEditorModal" class="resource-modal">
            <div class="resource-modal-content">
                <div class="resource-modal-header">
                    <h3>编辑急诊资源需求</h3>
                    <button id="closeResourceEditorBtn" style="border:none;background:none;font-size:24px;cursor:pointer;">&times;</button>
                </div>
                <div id="resourceEditorContent" class="resource-modal-body"></div>
                <div class="resource-modal-footer">
                    <div id="resourceCount">已选择 <strong>0</strong> 项</div>
                    <div>
                        <button id="cancelResourceSelectionBtn">取消</button>
                        <button id="saveResourceSelectionBtn" class="primary">确认修改</button>
                    </div>
                </div>
            </div>
        </div>
        """