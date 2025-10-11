# triage/data_loader.py (新建)

import json
from pathlib import Path
from typing import Dict, Optional

class TriageDataLoader:
    """分诊数据加载器"""
    
    @staticmethod
    def load_test_case(patient_id: str, data_dir: str = "data/triage") -> Dict:
        """
        从测试数据文件加载
        
        Args:
            patient_id: 患者ID
            data_dir: 数据目录路径
            
        Returns:
            测试数据字典
        """
        data_path = Path(data_dir) / f"{patient_id}.json"
        
        if not data_path.exists():
            raise FileNotFoundError(f"Triage test data not found: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)