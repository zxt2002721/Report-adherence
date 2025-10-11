# triage/generator.py

from report_modules.base.report_generator import BaseReportGenerator
from report_modules.triage.data_loader import TriageDataLoader
from report_modules.triage.html_generator import TriageHTMLGenerator
from typing import Dict

class TriageReportGenerator(BaseReportGenerator):

    def __init__(self, patient_id: str, data_dir: str = "data_triage", **kwargs):
        """
        Args:
            patient_id: 患者ID
            data_dir: 数据目录（从 data_dir/patient_id.json 加载数据）
        """
        super().__init__(patient_id, **kwargs)
        self.data_dir = data_dir

    def load_data(self) -> Dict:
        """从本地文件加载患者数据"""
        test_case = TriageDataLoader.load_test_case(self.patient_id, self.data_dir)
        
        return {
            'hpi': test_case.get('hpi', {}),
            'ph': test_case.get('ph', {}),
            'system_suggested_resources': test_case.get('RE_resources', {}),
            'pre_triage_summary': test_case.get('pre_triage_summary', ''),
            'go_to_hospital': test_case.get('go_to_hospital', {}),
            'max_time_to_doctor': test_case.get('max_time_to_doctor', {}),
            'deterioration_risk': test_case.get('deterioration_risk', {}),
            'hospital_recommendation': test_case.get('hospital_recommendation', {}),
            # 居家观察路径的数据
            'followup_time': test_case.get('followup_time', {}),
            'care_measures': test_case.get('care_measures', {}),
            'warning_signs': test_case.get('warning_signs', {})
        }
    
    def process_data(self) -> Dict:
        """处理分诊数据，根据决策路径准备不同的数据"""
        
        hpi = self.raw_data['hpi']
        ph = self.raw_data['ph']
        ed_snapshot = hpi.get('ed_snapshot', {})
        
        # 基本信息
        patient_info = {
            'age': hpi.get('meta', {}).get('age'),
            'sex': hpi.get('meta', {}).get('sex'),
            'chief_complaint': hpi.get('chief_complaint', ''),
        }
        
        # 生命体征
        vital_signs = {
            'temperature': ed_snapshot.get('temperature'),
            'heartrate': ed_snapshot.get('heartrate'),
            'resprate': ed_snapshot.get('resprate'),
            'o2sat': ed_snapshot.get('o2sat'),
            'sbp': ed_snapshot.get('sbp'),
            'dbp': ed_snapshot.get('dbp'),
            'pain': ed_snapshot.get('pain'),
            'esi': ed_snapshot.get('ESI')
        }
        
        # 扁平化病史数据
        medical_history = self._flatten_medical_history(ph)
        
        # 判断决策路径
        go_to_hospital = self.raw_data['go_to_hospital'].get('chose', 'yes')
        decision_path = 'immediate_care' if go_to_hospital == 'yes' else 'home_observation'
        
        immediate_care_data = self._process_immediate_care()
        home_observation_data = self._process_home_observation()

        hospital_rec_raw = self.raw_data.get('hospital_recommendation', {})
        hospital_rec_enriched = self._enrich_hospital_recommendations(hospital_rec_raw)
        
        
        return {
            'decision_path': decision_path,
            'patient_info': patient_info,
            'vital_signs': vital_signs,
            'medical_history': medical_history,
            'pre_triage_summary': self.raw_data.get('pre_triage_summary', ''),
            'go_to_hospital': self.raw_data['go_to_hospital'],
            'hospital_recommendation': hospital_rec_enriched,
            **immediate_care_data,
            **home_observation_data
        }

    def _flatten_medical_history(self, ph: Dict) -> Dict:
        """
        扁平化病史数据
        
        Args:
            ph: 患者病史原始数据
            
        Returns:
            扁平化后的病史字典
        """
        # 提取主要诊断列表
        problems = ph.get('problems', [])
        diagnosis_list = [p['diagnosis'] for p in problems if 'diagnosis' in p]
        
        # 提取手术史
        surgeries = ph.get('surgeries', [])
        surgery_list = [s['procedure'] for s in surgeries if 'procedure' in s]
        
        # 提取过敏史
        allergies = ph.get('allergies', [])
        allergy_list = [a.get('agent', a.get('allergen', '未知')) for a in allergies]
        
        # 提取用药史
        medications = ph.get('meds', [])
        medication_list = [
            f"{m['drug']} {m.get('dose', '')} {m.get('route', '')} {m.get('freq', '')}".strip()
            for m in medications if 'drug' in m
        ]
        
        # 提取家族史
        social = ph.get('social', {})
        family_history = social.get('familyHistory', '无特殊家族史')
        
        # 提取社会史
        tobacco_status = social.get('tobacco', {}).get('status', '未知')
        alcohol_status = social.get('alcohol', {}).get('status', '未知')
        
        return {
            'diagnoses': diagnosis_list,
            'diagnoses_str': '、'.join(diagnosis_list) if diagnosis_list else '无',
            
            'surgeries': surgery_list,
            'surgeries_str': '、'.join(surgery_list) if surgery_list else '无',
            
            'allergies': allergy_list,
            'allergies_str': '、'.join(allergy_list) if allergy_list else '无过敏史',
            
            'medications': medication_list,
            'medications_str': '; '.join(medication_list) if medication_list else '无',
            
            'family_history': family_history,
            
            'social_history': {
                'tobacco': tobacco_status,
                'alcohol': alcohol_status
            }
        }
    
    def _process_immediate_care(self) -> Dict:
        """处理立即就医路径的数据"""
        # system_resources = self._extract_resource_ids(
        #     self.raw_data['system_suggested_resources']
        # )
        system_resources= self._extract_resource_ids(self.raw_data.get('system_suggested_resources', {}))
        
        # return {
        #     'max_time_to_doctor': self.raw_data['max_time_to_doctor'],
        #     'deterioration_risk': self.raw_data['deterioration_risk'],
        #     'hospital_recommendation': self.raw_data['hospital_recommendation'],
        #     'system_resources': system_resources,
        #     'resource_details': self._get_resource_details(system_resources)
        # }
        return {
            'max_time_to_doctor': self.raw_data.get('max_time_to_doctor', {'chose': '30', 'evidence': '（默认值）'}),
            'deterioration_risk': self.raw_data.get('deterioration_risk', {'chose': '中', 'evidence': '（默认值）'}),
            'hospital_recommendation': self.raw_data.get('hospital_recommendation', {}),
            'system_resources': system_resources,
            'resource_details': self._get_resource_details(system_resources)
        }
    
    def _process_home_observation(self) -> Dict:
        """处理居家观察路径的数据"""
        return {
            'followup_time': self.raw_data.get('followup_time', {'chose': '24', 'evidence': '（默认值）'}),
            'care_measures': self.raw_data.get('care_measures', {'chose': [], 'evidence': '（默认值）'}),
            'warning_signs': self.raw_data.get('warning_signs', {'chose': [], 'evidence': ''}),
            # 居家观察也可能需要评估恶化风险，如果数据中没有，就提供一个默认值
            'home_deterioration_risk': self.raw_data.get('deterioration_risk', {'chose': '低', 'evidence': '（默认值）'})
        }
    
    def _extract_resource_ids(self, resources_dict: Dict) -> list:
        """从系统推荐资源中提取所有 testId"""
        resource_ids = []
        
        for category, subcategories in resources_dict.items():
            for subcategory, tests in subcategories.items():
                for test in tests:
                    if 'testId' in test:
                        resource_ids.append(test['testId'])
        
        return resource_ids
    
    def _get_resource_details(self, resource_ids: list) -> dict:
        """获取资源的详细信息（按类别分组）"""
        categories = {
            '床旁评估': [],
            '实验室检查': [],
            '影像检查': [],
            '诊断性操作': []
        }
        
        resources = self.raw_data['system_suggested_resources']
        
        for category, subcategories in resources.items():
            for subcategory, tests in subcategories.items():
                for test in tests:
                    test_id = test.get('testId')
                    test_name = test.get('testName')
                    
                    if test_id in resource_ids:
                        if test_id.startswith('BS-'):
                            categories['床旁评估'].append({
                                'id': test_id,
                                'name': test_name
                            })
                        elif test_id.startswith('LAB-'):
                            categories['实验室检查'].append({
                                'id': test_id,
                                'name': test_name
                            })
                        elif test_id.startswith('DX-IM-'):
                            categories['影像检查'].append({
                                'id': test_id,
                                'name': test_name
                            })
                        elif test_id.startswith('DX-'):
                            categories['诊断性操作'].append({
                                'id': test_id,
                                'name': test_name
                            })
        
        return {k: v for k, v in categories.items() if v}
    
    def generate_charts(self) -> Dict:
        """生成图表（暂时返回空）"""
        return {}
    
    def analyze(self) -> Dict:
        """AI分析（暂时返回空）"""
        return {}
    
    def render_html(self) -> str:
        """渲染HTML"""
        from datetime import datetime
        
        context = {
            "patient_id": self.patient_id,
            "report_generated_time": datetime.now().strftime("%Y-%m-%d %H:%M"),  # 🔧 新增
            **self.processed_data
        }
        
        full_html = TriageHTMLGenerator.render_and_build_report(
            context=context,
            patient_id=self.patient_id
        )
        
        return full_html
    
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    


    def _get_resource_name_by_id(self, resource_id: str) -> str:
        """通过资源ID获取资源名称"""
        from report_modules.triage.constants import EMERGENCY_RESOURCES
        
        # 遍历所有分类
        for category, resources in EMERGENCY_RESOURCES.items():
            # resources 是一个列表，每个元素有 'id' 和 'name'
            for resource in resources:
                if resource.get('id') == resource_id:
                    return resource.get('name', resource_id)
        
        # 如果找不到，返回ID本身
        return resource_id

    def _enrich_hospital_recommendations(self, hospital_rec: dict) -> dict:
        """为医院推荐数据添加资源名称"""
        if not hospital_rec or 'recommendations' not in hospital_rec:
            return hospital_rec
        
        enriched_rec = hospital_rec.copy()
        
        for rec in enriched_rec.get('recommendations', []):
            # 为matched_resources添加名称
            if 'resource_match' in rec:
                matched = rec['resource_match'].get('matched_resources', [])
                rec['resource_match']['matched_resources_with_names'] = [
                    {'id': res_id, 'name': self._get_resource_name_by_id(res_id)}
                    for res_id in matched
                ]
                
                # 为critical_resources添加名称
                critical = rec['resource_match'].get('critical_resources', [])
                rec['resource_match']['critical_resources_with_names'] = [
                    {'id': res_id, 'name': self._get_resource_name_by_id(res_id)}
                    for res_id in critical
                ]
                
                # 为missing_resources添加名称
                missing = rec['resource_match'].get('missing_resources', [])
                rec['resource_match']['missing_resources_with_names'] = [
                    {'id': res_id, 'name': self._get_resource_name_by_id(res_id)}
                    for res_id in missing
                ]
        
        return enriched_rec