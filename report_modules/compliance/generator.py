
# -*- coding: utf-8 -*-
"""
generator.py
依从性报告生成器 - 完整业务逻辑实现
"""

from typing import Dict, Any
from datetime import datetime
from report_modules.base.report_generator import BaseReportGenerator
from report_modules.common import config, data_loader, chart_generator
from report_modules.compliance import (
    medication_processor,
    monitoring_processor,
    data_builder,
    ai_analyzer,
    html_generator
)


class ComplianceReportGenerator(BaseReportGenerator):
    """依从性报告生成器"""
    
    def __init__(self, patient_id: str, **kwargs):
        """
        初始化依从性报告生成器
        
        Args:
            patient_id: 患者ID（如果为None，使用最新患者数据）
            **kwargs: 额外配置参数
        """
        # 如果未提供patient_id，获取最新的
        if not patient_id:
            patient_id, _ = data_loader.get_patient_id_from_args_or_latest(None)
        
        super().__init__(patient_id, **kwargs)
    
    def load_data(self) -> Dict[str, Any]:
        """加载依从性报告所需的原始数据"""
        print(f"  → 加载患者数据文件...")
        
        # 加载所有原始数据
        memory, dialogues, df_patient = data_loader.load_patient_data(self.patient_id)
        
        print(f"  → Memory数据: {len(memory)} 个字段")
        print(f"  → 对话记录: {len(dialogues)} 条")
        print(f"  → 生理数据: {len(df_patient)} 行")
        
        return {
            'memory': memory,
            'dialogues': dialogues,
            'df_patient': df_patient
        }
    
    def process_data(self) -> Dict[str, Any]:
        """处理依从性报告数据"""
        memory = self.raw_data['memory']
        dialogues = self.raw_data['dialogues']
        df_patient = self.raw_data['df_patient']
        
        print(f"  → 处理疾病和药物信息...")
        disease_info = medication_processor.process_disease_info_medications(memory)
        
        print(f"  → 构建监测数据...")
        monitoring = monitoring_processor.build_monitoring_from_df(df_patient)
        status = monitoring_processor.compute_status(monitoring)
        
        print(f"  → 构建依从性数据...")
        adherence_std = data_builder.build_adherence(memory)
        
        print(f"  → 构建生活方式数据...")
        lifestyle_std = data_builder.build_lifestyle(memory)
        
        print(f"  → 构建应用使用数据...")
        app_overview = data_builder.build_app(memory, dialogues)
        
        print(f"  → 构建建议提示...")
        tips_block = data_builder.build_tips(memory, monitoring, status, adherence_std)
        
        # 获取目标值和报告周期
        targets = memory.get("targets", config.DEFAULT_TARGETS)
        report_period = monitoring_processor.get_report_period(df_patient)
        
        # 构建患者基础信息
        basic = memory.get("basic_info", {})
        patient_context = self._build_patient_context(basic, disease_info)
        
        return {
            'patient': patient_context,
            'disease_info': disease_info,
            'monitoring': monitoring,
            'targets': targets,
            'status': status,
            'adherence': adherence_std,
            'lifestyle': lifestyle_std,
            'app': app_overview,
            'tips': tips_block,
            'report_period': report_period,
            'references': memory.get("references", [])
        }
    
    def generate_charts(self) -> Dict[str, str]:
        """生成依从性报告的所有图表"""
        memory = self.raw_data['memory']
        df_patient = self.raw_data['df_patient']
        
        # 为每个报告创建独立的assets目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        assets_dir = config.OUT_DIR / self.patient_id / f"compliance_{timestamp}" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  → 生成依从性图表（保存到 {assets_dir}）...")
        adherence_charts = chart_generator.generate_adherence_charts(
            memory, 
            assets_dir,
            assets_dir.parent  # out_dir 设为报告目录
        )
        
        print(f"  → 生成生理数据图表...")
        physio_charts = chart_generator.generate_physio_charts(
            df_patient, 
            assets_dir,
            assets_dir.parent
        )
        
        all_charts = {**physio_charts, **adherence_charts}
        print(f"  → 共生成 {len(all_charts)} 个图表")
        
        return all_charts

    
    def analyze(self) -> Dict[str, str]:
        """AI分析依从性数据"""
        print(f"  → 调用AI生成完整分析报告...")
        
        ai_analysis = ai_analyzer.generate_ai_analysis(
            monitoring=self.processed_data['monitoring'],
            adherence=self.processed_data['adherence'],
            lifestyle=self.processed_data.get('lifestyle', {}),
            patient_info=self.processed_data.get('patient', {})
        )
        
        return ai_analysis
    
    def render_html(self) -> str:
        """渲染依从性报告HTML"""
        context = {
            "report": {
                "period": self.processed_data['report_period'],
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "patient": self.processed_data['patient'],
            "disease_info": self.processed_data['disease_info'],
            "monitoring": self.processed_data['monitoring'],
            "targets": self.processed_data['targets'],
            "status": self.processed_data['status'],
            "adherence": self.processed_data['adherence'],
            "lifestyle": self.processed_data['lifestyle'],
            "app": self.processed_data['app'],
            "tips": self.analysis.get('tips', self.processed_data['tips']),  # 优先使用AI生成的tips
            "tips_source": "AI智能分析" if 'tips' in self.analysis else "系统模板",
            "ai": {
                "summary": self.analysis.get('summary', ''),
                "risk_assessment": self.analysis.get('risk_assessment', ''),
                "recommendations": self.analysis.get('recommendations', '')
            },
            "references": self.processed_data['references'],
            "charts": self.charts,
        }
        
        doc_html, fam_html = html_generator.ComplianceHTMLGenerator.generate_html_reports(
            context, 
            self.patient_id
        )
        
        # 保存家属版到同一目录
        timestamp = self.generated_at.strftime('%Y%m%d_%H%M%S')
        report_dir = config.OUT_DIR / self.patient_id / f"compliance_{timestamp}"
        fam_path = report_dir / "family_report.html"
        fam_path.parent.mkdir(parents=True, exist_ok=True)
        fam_path.write_text(fam_html, encoding='utf-8')
        print(f"📁 家属版已保存到: {fam_path}")
        
        return doc_html

    
    def _build_patient_context(self, basic: dict, disease_info: dict) -> dict:
        """构建患者基础信息上下文（内部辅助方法）"""
        patient_context = {
            "name": basic.get("name", self.patient_id),
            "gender": basic.get("sex", "—"),
            "age": basic.get("age", "—"),
            "occupation": basic.get("occupation", "—"),
            "education": basic.get("education", "—"),
            "family": basic.get("living_situation", "—"),
            "phone": basic.get("contact_phone", "—"),
            "support": basic.get("support", "—"),
            "allergies": "、".join(disease_info.get("allergies", [])) or "未记录",
            "history": "、".join([
                d.get("disease_name", "") 
                for d in disease_info.get("primary_diseases", [])
            ]) or "未记录",
            "current_medications": disease_info.get("current_medications_text", "—"),
        }
        
        return patient_context
    
    def get_adherence_stats(self) -> dict:
        """获取依从性统计信息（便捷方法）"""
        if not self.raw_data:
            raise RuntimeError("数据尚未加载，请先调用 generate() 方法")
        
        stats = data_builder.build_adherence_stats(self.raw_data['memory'])
        return stats.get('summary', {})