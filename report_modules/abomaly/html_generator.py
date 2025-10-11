# -*- coding: utf-8 -*-
"""
异常检测报告HTML生成器 - 定义异常检测专用配置
"""

class AnomalyHTMLGenerator:
    """异常检测报告专用HTML生成器"""
    
    # 异常检测专用样式
    ANOMALY_EXTRA_STYLES = """
.anomaly-alert {
    background: #fef2f2;
    border-left: 4px solid #dc2626;
    padding: 12px;
    margin: 8px 0;
    border-radius: 8px;
}
"""
    
    # 异常检测章节类型配置 ⭐ 不同于依从性
    SECTION_KINDS = [
        {
            'key': 'alert',
            'includes': ['异常警报', '告警', 'Alert'],
            'tools_html': '''
                <span class="chip">处理：</span>
                <select data-k="alert.action">
                    <option value="">待处理</option>
                    <option>已通知患者</option>
                    <option>需进一步检查</option>
                    <option>假阳性</option>
                </select>
                <button class="btn-mini" data-act="mark-handled" data-done-text="已处理">标记处理</button>
            '''
        },
        {
            'key': 'trend',
            'includes': ['趋势分析', 'Trend'],
            'tools_html': '''
                <label class="chip"><input type="checkbox" data-k="trend.confirm"> 趋势确认</label>
                <button class="btn-mini" data-act="adjust-threshold" data-done-text="已调整">调整阈值</button>
            '''
        }
    ]
    
    @staticmethod
    def generate_html_report(context: dict, patient_id: str) -> str:
        """生成异常检测报告"""
        from report_modules.common.html_base import HTMLBaseGenerator
        
        # ... 渲染逻辑 ...
        
        return HTMLBaseGenerator.build_html_shell(
            title="异常检测报告",
            content=content_html,
            patient_id=patient_id,
            report_type="anomaly",  # 不同的报告类型
            extra_styles=AnomalyHTMLGenerator.ANOMALY_EXTRA_STYLES,
            section_kinds=AnomalyHTMLGenerator.SECTION_KINDS  # 不同的章节配置
        )