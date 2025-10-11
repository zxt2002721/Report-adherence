# -*- coding: utf-8 -*-
"""
报告生成器抽象基类 - 定义所有报告生成器的标准流程
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class BaseReportGenerator(ABC):
    """
    报告生成器抽象基类
    
    定义了所有报告生成器的标准流程（模板方法模式）：
    1. load_data() - 加载数据
    2. process_data() - 处理数据
    3. generate_charts() - 生成图表
    4. analyze() - AI分析
    5. render_html() - 渲染HTML
    
    子类必须实现所有抽象方法来定制特定类型的报告生成逻辑。
    """
    
    def __init__(self, patient_id: str, **kwargs):
        """
        初始化报告生成器
        
        Args:
            patient_id: 患者ID
            **kwargs: 额外配置参数，子类可以定义自己需要的参数
        """
        self.patient_id = patient_id
        self.config = kwargs
        
        # 数据存储
        self.raw_data: Optional[Dict[str, Any]] = None
        self.processed_data: Optional[Dict[str, Any]] = None
        self.charts: Optional[Dict[str, str]] = None
        self.analysis: Optional[Dict[str, str]] = None
        self.html_output: Optional[str] = None
        
        # 元数据
        self.report_type = self.__class__.__name__.replace('Generator', '').replace('Report', '')
        self.generated_at: Optional[datetime] = None
        
        # 验证患者ID
        if not patient_id or not isinstance(patient_id, str):
            raise ValueError(f"无效的患者ID: {patient_id}")
    
    # ==================== 抽象方法（子类必须实现） ====================
    
    @abstractmethod
    def load_data(self) -> Dict[str, Any]:
        """
        加载原始数据
        
        子类需要实现具体的数据加载逻辑，例如：
        - 依从性报告：加载用药记录、依从性统计等
        - 异常检测报告：加载生理监测数据、历史基线等
        - 分诊报告：加载症状、生命体征、病史等
        
        Returns:
            Dict[str, Any]: 原始数据字典
            
        Raises:
            FileNotFoundError: 数据文件不存在
            ValueError: 数据格式错误
        """
        pass
    
    @abstractmethod
    def process_data(self) -> Dict[str, Any]:
        """
        处理数据
        
        对加载的原始数据进行处理、计算、汇总等操作。
        
        Returns:
            Dict[str, Any]: 处理后的数据字典
            
        Raises:
            ValueError: 数据处理失败
        """
        pass
    
    @abstractmethod
    def generate_charts(self) -> Dict[str, str]:
        """
        生成图表
        
        根据处理后的数据生成可视化图表。
        
        Returns:
            Dict[str, str]: 图表字典，key为图表名称，value为图表路径或Base64编码
            
        Example:
            {
                'trend_chart': 'data:image/png;base64,iVBORw0KG...',
                'bar_chart': '/path/to/chart.png'
            }
        """
        pass
    
    @abstractmethod
    def analyze(self) -> Dict[str, str]:
        """
        AI分析
        
        调用AI模型对数据进行分析，生成文字描述和建议。
        
        Returns:
            Dict[str, str]: 分析结果字典
            
        Example:
            {
                'summary': '患者整体情况良好...',
                'risk_assessment': '存在以下风险...',
                'recommendations': '建议采取以下措施...'
            }
        """
        pass
    
    @abstractmethod
    def render_html(self) -> str:
        """
        渲染HTML报告
        
        将所有数据、图表、分析结果渲染为最终的HTML报告。
        
        Returns:
            str: 完整的HTML字符串
        """
        pass
    
    # ==================== 模板方法（定义标准流程） ====================
    
    def generate(self) -> str:
        """
        生成报告的主流程（模板方法）
        
        按照固定顺序执行所有步骤：
        1. 加载数据
        2. 处理数据
        3. 生成图表
        4. AI分析
        5. 渲染HTML
        
        Returns:
            str: 生成的HTML报告
            
        Raises:
            Exception: 任何步骤失败都会抛出异常
        """
        try:
            self.generated_at = datetime.now()
            
            print(f"\n{'='*60}")
            print(f"开始生成 {self.report_type} 报告")
            print(f"患者ID: {self.patient_id}")
            print(f"生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            
            # 步骤1: 加载数据
            print("📂 [1/5] 正在加载数据...")
            self.raw_data = self.load_data()
            print(f"✅ 数据加载完成 - 包含 {len(self.raw_data)} 个数据项\n")
            
            # 步骤2: 处理数据
            print("⚙️  [2/5] 正在处理数据...")
            self.processed_data = self.process_data()
            print(f"✅ 数据处理完成\n")
            
            # 步骤3: 生成图表
            print("📊 [3/5] 正在生成图表...")
            self.charts = self.generate_charts()
            print(f"✅ 图表生成完成 - 共 {len(self.charts)} 个图表\n")
            
            # 步骤4: AI分析
            print("🤖 [4/5] 正在进行AI分析...")
            self.analysis = self.analyze()
            print(f"✅ AI分析完成\n")
            
            # 步骤5: 渲染HTML
            print("🎨 [5/5] 正在渲染HTML...")
            self.html_output = self.render_html()
            print(f"✅ HTML渲染完成 - 共 {len(self.html_output):,} 字符\n")
            
            print(f"{'='*60}")
            print(f"✨ {self.report_type} 报告生成成功！")
            print(f"{'='*60}\n")
            
            return self.html_output
            
        except Exception as e:
            print(f"\n❌ 报告生成失败: {str(e)}")
            raise
    
    # ==================== 辅助方法（可选重写） ====================
    
    def validate_data(self, data: Dict[str, Any], required_keys: list) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据字典
            required_keys: 必需的键列表
            
        Returns:
            bool: 数据是否有效
        """
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"数据缺失必需字段: {missing_keys}")
        return True
    
    def save_to_file(self, output_path: Optional[Path] = None) -> Path:
        """保存报告到文件"""
        if not self.html_output:
            raise RuntimeError("报告尚未生成，请先调用 generate() 方法")
        
        if output_path is None:
            # 使用新的默认路径结构
            from report_modules.common import config
            
            # 生成时间戳
            timestamp = self.generated_at.strftime('%Y%m%d_%H%M%S')
            
            # 构建路径：output/患者ID/报告类型_时间戳/
            report_dir = config.OUT_DIR / self.patient_id / f"{self.report_type.lower()}_{timestamp}"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = report_dir / "doctor_report.html"
        else:
            output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.html_output, encoding='utf-8')
        print(f"📁 报告已保存到: {output_path.absolute()}")
        
        return output_path
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取报告摘要信息
        
        Returns:
            Dict[str, Any]: 报告摘要
        """
        return {
            'report_type': self.report_type,
            'patient_id': self.patient_id,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'data_items': len(self.raw_data) if self.raw_data else 0,
            'charts_count': len(self.charts) if self.charts else 0,
            'html_size': len(self.html_output) if self.html_output else 0,
            'config': self.config
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"<{self.__class__.__name__}("
                f"patient_id='{self.patient_id}', "
                f"generated={self.generated_at is not None})>")