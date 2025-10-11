# -*- coding: utf-8 -*-
"""
慢病患者报告生成器模块包
v2.0 - 多类型报告架构版

架构设计：
- 基于模板方法模式 + 工厂模式
- 支持多种类型的患者报告生成
- 模块化、可扩展、职责清晰

目录结构：
├── base/                      # 基类模块
│   └── report_generator.py    # 抽象基类：定义报告生成标准流程
│
├── common/                    # 共享工具模块
│   ├── config.py              # 全局配置和常量
│   ├── data_loader.py         # 通用数据加载器
│   ├── chart_generator.py     # 通用图表生成器
│   └── html_base.py           # HTML基础生成器
│
├── compliance/                # 依从性报告模块
│   ├── medication_processor.py # 药物信息处理
│   ├── data_builder.py        # 依从性数据构建
│   ├── monitoring_processor.py # 监测数据处理
│   ├── ai_analyzer.py         # AI分析（依从性专用）
│   ├── html_generator.py      # HTML生成（依从性专用）
│   └── generator.py           # 依从性报告生成器
│
├── anomaly/                   # 异常检测报告模块（待实现）
│   ├── detector.py            # 异常检测算法
│   ├── analyzer.py            # 异常分析器
│   ├── html_generator.py      # HTML生成（异常检测专用）
│   └── generator.py           # 异常检测报告生成器
│
└── triage/                    # 分诊报告模块（待实现）
    ├── classifier.py          # 分诊分类器
    ├── priority.py            # 优先级评估
    ├── html_generator.py      # HTML生成（分诊专用）
    └── generator.py           # 分诊报告生成器

使用方式：
>>> from report_modules import ReportFactory
>>> 
>>> # 列出所有支持的报告类型
>>> print(ReportFactory.list_types())
>>> # ['compliance']
>>> 
>>> # 创建依从性报告生成器
>>> generator = ReportFactory.create('compliance', patient_id='P001')
>>> 
>>> # 生成报告
>>> html = generator.generate()
>>> 
>>> # 保存到文件
>>> output_path = generator.save_to_file()

扩展新报告类型：
1. 在 report_modules/ 下创建新子模块（如 risk_assessment/）
2. 创建 generator.py 继承 BaseReportGenerator
3. 实现 load_data(), process_data(), generate_charts(), analyze(), render_html()
4. 在本文件的 ReportFactory 中注册新类型
"""

from typing import Type, Dict
from report_modules.base.report_generator import BaseReportGenerator


class ReportFactory:
    """
    报告生成器工厂类
    
    使用工厂模式统一管理所有报告类型的创建。
    新增报告类型时，只需在此注册即可。
    """
    
    # 注册表：存储所有已注册的报告生成器
    _generators: Dict[str, Type[BaseReportGenerator]] = {}
    
    @classmethod
    def register(cls, report_type: str, generator_class: Type[BaseReportGenerator]):
        """
        注册报告生成器
        
        Args:
            report_type: 报告类型标识（如 'compliance', 'anomaly', 'triage'）
            generator_class: 报告生成器类（必须继承 BaseReportGenerator）
        
        Raises:
            TypeError: 如果 generator_class 不是 BaseReportGenerator 的子类
        """
        if not issubclass(generator_class, BaseReportGenerator):
            raise TypeError(
                f"{generator_class.__name__} 必须继承 BaseReportGenerator"
            )
        
        cls._generators[report_type] = generator_class
        print(f"[ReportFactory] 已注册报告类型: '{report_type}' -> {generator_class.__name__}")
    
    @classmethod
    def create(cls, report_type: str, patient_id: str, **kwargs) -> BaseReportGenerator:
        """
        创建指定类型的报告生成器
        
        Args:
            report_type: 报告类型（'compliance', 'anomaly', 'triage'）
            patient_id: 患者ID
            **kwargs: 额外配置参数，传递给生成器构造函数
        
        Returns:
            BaseReportGenerator: 报告生成器实例
        
        Raises:
            ValueError: 未知的报告类型
        
        Example:
            >>> generator = ReportFactory.create('compliance', patient_id='P001')
            >>> generator = ReportFactory.create('anomaly', patient_id='P001', threshold=2.5)
        """
        generator_class = cls._generators.get(report_type)
        
        if not generator_class:
            available = ', '.join(f"'{t}'" for t in cls._generators.keys())
            raise ValueError(
                f"未知的报告类型: '{report_type}'\n"
                f"可用类型: {available or '(无)'}"
            )
        
        return generator_class(patient_id, **kwargs)
    
    @classmethod
    def list_types(cls) -> list:
        """
        列出所有支持的报告类型
        
        Returns:
            list: 报告类型列表
        
        Example:
            >>> ReportFactory.list_types()
            ['compliance', 'anomaly', 'triage']
        """
        return list(cls._generators.keys())
    
    @classmethod
    def is_registered(cls, report_type: str) -> bool:
        """
        检查报告类型是否已注册
        
        Args:
            report_type: 报告类型标识
        
        Returns:
            bool: 是否已注册
        """
        return report_type in cls._generators


# ==================== 注册已实现的报告类型 ====================

# 1. 依从性报告（已实现）
try:
    from report_modules.compliance.generator import ComplianceReportGenerator
    ReportFactory.register('compliance', ComplianceReportGenerator)
except ImportError as e:
    print(f"[警告] 依从性报告模块加载失败: {e}")

# 2. 异常检测报告（待实现）
# try:
#     from report_modules.anomaly.generator import AnomalyReportGenerator
#     ReportFactory.register('anomaly', AnomalyReportGenerator)
# except ImportError:
#     pass

#3. 分诊报告（待实现）
try:
    from report_modules.triage.generator import TriageReportGenerator
    ReportFactory.register('triage', TriageReportGenerator)
except ImportError as e:
    print(f"[警告] 分诊报告模块加载失败: {e}")
    # pass


# ==================== 导出公共接口 ====================

__all__ = [
    'ReportFactory',
    'BaseReportGenerator',
]

# 版本信息
__version__ = '2.0.0'
__author__ = 'Report Generator Team'
__description__ = '慢病患者多类型报告生成器'


# ==================== 模块初始化检查 ====================

def _check_dependencies():
    """检查必需的依赖模块"""
    required_modules = [
        'jinja2',
        'markdown',
        'matplotlib',
        'pandas',
    ]
    
    missing = []
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(module_name)
    
    if missing:
        print(f"[警告] 缺少以下依赖: {', '.join(missing)}")
        print(f"       请运行: pip install {' '.join(missing)}")


# 执行初始化检查（可选）
# _check_dependencies()


# ==================== 便捷导入（可选） ====================

# 如果需要快速访问常用模块，可以在这里导入：
# from report_modules.common import config, data_loader, chart_generator
# from report_modules.base.report_generator import BaseReportGenerator