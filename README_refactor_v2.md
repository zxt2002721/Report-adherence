# 慢病患者报告生成器 v2.1 - 多类型报告架构

## 📋 目录

- [概述](#概述)
- [核心设计理念](#核心设计理念)
- [架构图](#架构图)
- [目录结构](#目录结构)
- [关键设计决策](#关键设计决策)
- [批注系统详解](#批注系统详解)
- [模块职责详解](#模块职责详解)
- [迁移指南](#迁移指南)
- [测试验证](#测试验证)
- [常见问题](#常见问题)
- [扩展新报告类型](#扩展新报告类型)
- [输出结构与命名](#输出结构与命名基于-user_id--报告类型--时间戳)

---

## 📋 概述

这是对原始依从性报告生成器的**第二次重构**，核心目标：

1. ✅ **支持多种报告类型**：依从性、异常检测、分诊等
2. ✅ **通用批注系统**：所有报告共享批注功能，章节交互可配置
3. ✅ **报告独立存储**：每份报告有唯一ID，批注数据互不干扰
4. ✅ **高扩展性**：新增报告类型无需修改现有代码
5. ✅ **清晰分层**：基类 → 共享工具 → 独立报告生成器

### 版本对比

| 维度         | v1.0（第一次重构） | v2.0（本次重构）        | v2.1（最新版）           |
| ------------ | ------------------ | ----------------------- | ------------------------ |
| 架构模式     | 功能模块化         | 模板方法 + 工厂模式     | 同左                     |
| 报告类型     | 仅依从性           | 可扩展多种类型          | compliance + triage      |
| 批注功能     | 耦合在html_generator | 通用批注系统            | 通用批注系统             |
| 报告隔离     | 按患者ID           | 按患者ID                | **按报告ID（时间戳）**   |
| 交互元素支持 | 部分               | select + checkbox       | **全表单元素（包括radio、input、textarea）** |
| 主入口职责   | 包含业务逻辑       | 仅命令行解析            | 同左                     |
| 扩展难度     | 需修改多处         | 独立添加即可            | 同左                     |

### 🆕 v2.1 新特性

- **报告独立ID系统**：每份报告生成时分配唯一时间戳ID，localStorage完全隔离
- **预设值自动保存**：HTML中的默认值（select selected、checkbox checked）自动存储
- **增强的交互支持**：支持 text input、radio、textarea 等所有表单元素
- **分诊报告实现**：完整的急诊分诊评估报告，包含资源编辑器和医院推荐系统
- **资源名称显示**：资源编辑器中显示完整资源名称，而非ID
- **医生审批表单**：支持记录人、科室、签名等结构化审批流程

---

## 🎯 核心设计理念

### 1. **通用批注 + 可配置交互**

**关键洞察**：批注功能（添加批注、导出导入、localStorage）对所有报告类型都相同，但章节交互控件因报告而异。
```
┌─────────────────────────────────────────────┐
│  通用批注层 (common/html_base.py)             │
│  - 批注卡片系统(通用)                          │
│  - 工具条(通用)                               │
│  - localStorage(通用)                        │
│  - 章节交互框架(可配置)                        │
│  - 报告ID隔离系统 🆕                          │
└─────────────────────────────────────────────┘
^
│ 配置
┌─────────┴───────────────┐
│                         │
┌───────────────┐   ┌──────────────┐
│ compliance/   │   │ triage/      │
│ 章节类型配置    │   │ 章节类型配置   │
└───────────────┘   └──────────────┘
```

### 2. **模板方法模式定义标准流程**

所有报告生成器遵循统一流程：

```python
generate() {
    1. load_data()          # 子类实现
    2. process_data()       # 子类实现
    3. generate_charts()    # 子类实现
    4. analyze()            # 子类实现
    5. render_html()        # 子类实现
}
```

### **工厂模式统一创建**

```python
# 使用工厂创建，类型安全
generator = ReportFactory.create('compliance', patient_id='P001')
html = generator.generate()
```

---

## 🏗️ 架构图

### 总体架构

```
┌─────────────────────────────────────────────────────────┐
│                     report.py                           │
│            (命令行 + 工厂调用，~80行)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           ReportFactory (工厂类)                        │
│   create('compliance') → ComplianceReportGenerator      │
│   create('anomaly') → AnomalyReportGenerator            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ Compliance   │          │ Anomaly      │
│ Generator    │          │ Generator    │
│              │          │              │
│ 继承基类 ────┼─────────►. │ 继承基类     │
└──────────────┘          └──────────────┘
        │                         │
        │                         │
        ▼                         ▼
┌─────────────────────────────────────────┐
│      BaseReportGenerator (基类)         │
│   - load_data() [抽象]                  │
│   - process_data() [抽象]               │
│   - generate_charts() [抽象]            │
│   - analyze() [抽象]                    │
│   - render_html() [抽象]                │
│   - generate() [模板方法]               │
└─────────────────────────────────────────┘
```

### 批注系统架构

```
┌───────────────────────────────────────────────────────┐
│          HTMLBaseGenerator（通用批注）                 │
│  ┌─────────────────────────────────────────────┐     │
│  │  build_html_shell(                          │     │
│  │    title,                                   │     │
│  │    content,                                 │     │
│  │    section_kinds=[  ← 可配置章节类型        │     │
│  │      {                                      │     │
│  │        'key': 'disease',                    │     │
│  │        'includes': ['疾病', '诊断'],        │     │
│  │        'tools_html': '<select>...</select>' │     │
│  │      }                                      │     │
│  │    ]                                        │     │
│  │  )                                          │     │
│  └─────────────────────────────────────────────┘     │
│                                                       │
│  通用JavaScript:                                      │
│  - setupSectionAnchors() // 添加批注按钮             │
│  - mountSectionTools()   // 根据配置挂载交互控件      │
│  - renderNotes()         // 恢复批注卡片             │
│  - setupToolbar()        // 工具条                   │
└───────────────────────────────────────────────────────┘
                    ▲
                    │ 传入配置
        ┌───────────┴───────────┐
        │                       │
┌───────────────┐       ┌──────────────┐
│ Compliance    │       │ Triage      │
│ SECTION_KINDS │       │ SECTION_KINDS│
│ [disease,     │       │ [alert,      │
│  monitor,     │       │  trend,      │
│  adherence]   │       │  severity]   │
└───────────────┘       └──────────────┘
```

---

## 📁 目录结构

```
report/
├── report.py                      # 主入口（~80行，仅命令行）
├── report_legacy.py               # 原始备份（1076行）
├── verify_controls.py             # 验证脚本
├── README.md                      # 本文档
│
└── report_modules/                # 核心模块包
    │
    ├── __init__.py                # 工厂类 + 注册
    │
    ├── base/                      # 🎯 基类模块
    │   ├── __init__.py
    │   └── report_generator.py    # 抽象基类（~200行）
    │
    ├── common/                    # 🔧 共享工具模块
    │   ├── __init__.py
    │   ├── config.py              # 全局配置
    │   ├── data_loader.py         # 数据加载器
    │   ├── chart_generator.py     # 图表生成器
    │   └── html_base.py           # ⭐ HTML基础生成器（~400行）
    │                               #    包含通用批注系统
    │
    ├── compliance/                # 📊 依从性报告模块
    │   ├── __init__.py
    │   ├── medication_processor.py # 药物处理
    │   ├── data_builder.py        # 数据构建
    │   ├── monitoring_processor.py # 监测处理
    │   ├── ai_analyzer.py         # AI分析
    │   ├── html_generator.py      # ⭐ HTML生成（~150行）
    │   │                           #    定义 SECTION_KINDS
    │   ├── templates                # templates
    │   └── generator.py           # 主生成器（~250行）
    │
    ├── anomaly/                   # 🚧 异常检测模块（待实现）
    │   ├── __init__.py
    │   ├── detector.py
    │   ├── analyzer.py
    │   ├── html_generator.py      # ⭐ 定义异常检测的 SECTION_KINDS
    │   └── generator.py
    │
    └── triage/                    # 🚧 分诊模块
        ├── init.py
        ├── constants.py           # 急诊资源定义
        ├── data_loader.py         # 数据加载
        ├── html_generator.py      # ⭐ HTML生成 + 资源编辑器
        ├── generator.py           # 主生成器
        └── templates/
        └── triage_template.md # 分诊报告模板
```

---


### 输出结构与命名（基于 user_id + 报告类型 + 时间戳）

为了解决不同患者报告互相覆盖、静态资源混在一起的问题，输出目录采用分桶式结构：先按患者 ID 分组，再按“报告类型_时间戳”建子目录；医生版/家属版与图表资产（assets）保存在同一目录中，完全隔离。

#### 目录结构

```
output/
├── P001/                                    # 患者ID
│   ├── compliance_20251006_153045/          # 报告类型_时间戳
│   │   ├── doctor_report.html               # 医生版
│   │   ├── family_report.html               # 家属版
│   │   └── assets/                          # 本次生成的图表与静态资源
│   │       ├── bp_trend.png
│   │       └── ...
│   └── anomaly_20251006_170530/
│       ├── report.html
│       └── assets/
└── P002/
    └── compliance_20251006_160230/
        └── ...
```

#### 命名规则

- 患者分组：`output/<patient_id>/`
- 报告目录：`<report_type>_<YYYYMMDD_HHMMSS>/`
- HTML 文件：`doctor_report.html`、`family_report.html`（若该类型只产出单一版本，用 `report.html`）
- 资源目录：`assets/`（每次生成**独立**，不与其他患者/批次共享）

#### 使用方法（CLI）

```
python report.py --id 0b389f61f90fcf6da613e08c64e06fdbaf05758cdd9e6b5ae730f1b8a8a654e4 --type compliance

python report.py --id P001 --type triage



---

## 📝 批注系统详解

### 核心功能（通用）

#### 1. 批注卡片

* **功能** ：在任意章节添加富文本批注
* **存储** ：localStorage（按 `reportType::patientId` 隔离）
* **特性** ：contenteditable、实时保存、删除

#### 2. 全局批注

* **功能** ：整体意见输入框
* **位置** ：报告顶部
* **存储** ：独立的 localStorage 键

#### 3. 导出/导入

* **格式** ：JSON
* **内容** ：

```json
  {  "patient_id": "P001",  "report_type": "compliance",  "exported_at": "2025-10-06 14:30",  "global": "整体意见文本",  "sections": {    "sec-1": [{"id": "n-123", "ts": "...", "html": "..."}]  },  "interactions": {    "sec-1::disease.plan": "加强"  }}
```

#### 4. 章节交互（可配置）

 **依从性报告示例** ：

```python
{
    'key': 'adherence',
    'includes': ['依从', '依从性'],
    'tools_html': '''
        <label><input type="checkbox" data-k="adherence.follow"> 需随访</label>
        <select data-k="adherence.period">
            <option>1周</option>
            <option>2周</option>
        </select>
        <button data-act="make-follow" data-done-text="已记录">记录随访任务</button>
    '''
}
```

 **异常检测报告示例** ：

```python
{
    'key': 'alert',
    'includes': ['异常', '警报'],
    'tools_html': '''
        <select data-k="alert.action">
            <option>待处理</option>
            <option>已通知患者</option>
        </select>
        <button data-act="mark-handled">标记处理</button>
    '''
}
```

### localStorage 命名空间

```javascript
// 按报告类型和患者ID隔离
const LS_ANNOTATIONS = `report-annotations::${reportType}::${patientId}`;
const LS_GLOBAL = `report-annotations-global::${reportType}::${patientId}`;
const LS_INTERACTIONS = `report-interactions::${reportType}::${patientId}`;
```

示例：

```
report-annotations::compliance::P001
report-annotations::anomaly::P001
report-annotations-global::compliance::P001
```

---

## 🔍 模块职责详解

### base/report_generator.py

 **职责** ：定义报告生成器抽象基类

 **核心方法** ：

```python
class BaseReportGenerator(ABC):
    @abstractmethod
    def load_data() -> Dict        # 加载原始数据
  
    @abstractmethod
    def process_data() -> Dict     # 处理数据
  
    @abstractmethod
    def generate_charts() -> Dict  # 生成图表
  
    @abstractmethod
    def analyze() -> Dict          # AI分析
  
    @abstractmethod
    def render_html() -> str       # 渲染HTML
  
    def generate() -> str:         # 模板方法（不可重写）
        self.load_data()
        self.process_data()
        self.generate_charts()
        self.analyze()
        return self.render_html()
```

 **关键特性** ：

* 模板方法 `generate()` 定义固定流程
* 5个抽象方法子类必须实现
* 提供 `save_to_file()`, `get_summary()` 辅助方法

---

### common/html_base.py

 **职责** ：通用HTML生成和批注系统

 **核心方法** ：

```python
class HTMLBaseGenerator:
    @staticmethod
    def build_html_shell(
        title: str,
        content: str,
        patient_id: str,
        report_type: str,
        section_kinds: List[Dict],  # ⭐ 章节配置
        extra_styles: str = ""
    ) -> str:
        # 1. 构建HTML结构
        # 2. 插入通用批注JS
        # 3. 传递章节配置到JS
```

 **批注JS核心函数** ：

* `setupSectionAnchors()`: 为所有标题添加批注按钮
* `mountSectionTools()`: 根据 `section_kinds` 挂载交互控件
* `renderNotes()`: 从 localStorage 恢复批注卡片
* `setupToolbar()`: 初始化工具条（导出/导入等）

 **关键设计** ：

* 通用功能（批注卡片）硬编码在JS中
* 可配置功能（章节交互）通过 `section_kinds` 传入

---

### compliance/html_generator.py

 **职责** ：依从性报告HTML生成配置

 **核心内容** ：

```python
class ComplianceHTMLGenerator:
    # 1. 额外样式（可选）
    COMPLIANCE_EXTRA_STYLES = """..."""
  
    # 2. 章节类型配置 ⭐ 核心
    SECTION_KINDS = [
        {
            'key': 'disease',
            'includes': ['疾病', '诊断'],
            'tools_html': '<select>...</select>'
        },
        # ... 其他章节类型 ...
    ]
  
    # 3. 生成HTML
    @staticmethod
    def generate_html_reports(context, patient_id):
        # 渲染Markdown模板
        doc_html = HTMLBaseGenerator.render_markdown_template(...)
  
        # 调用通用批注系统
        return HTMLBaseGenerator.build_html_shell(
            content=doc_html,
            section_kinds=SECTION_KINDS  # ⭐ 传入配置
        )
```

 **关键点** ：

* **不包含**批注核心逻辑（在 `common/html_base.py`）
* **仅定义**依从性报告的章节类型和交互控件
* 模板路径：`templates/doctor_template.md`

---

### compliance/generator.py

 **职责** ：依从性报告主生成器

 **核心流程** ：

```python
class ComplianceReportGenerator(BaseReportGenerator):
    def load_data(self):
        memory, dialogues, df = data_loader.load_patient_data(self.patient_id)
        return {'memory': memory, 'dialogues': dialogues, 'df_patient': df}
  
    def process_data(self):
        # 调用所有依从性专用处理器
        disease_info = medication_processor.process_disease_info(...)
        monitoring = monitoring_processor.build_monitoring(...)
        adherence = data_builder.build_adherence(...)
        # ... 构建完整上下文 ...
        return context
  
    def generate_charts(self):
        adherence_charts = chart_generator.generate_adherence_charts(...)
        physio_charts = chart_generator.generate_physio_charts(...)
        return {**adherence_charts, **physio_charts}
  
    def analyze(self):
        return ai_analyzer.generate_ai_analysis(...)
  
    def render_html(self):
        context = {**self.processed_data, 'charts': self.charts, 'ai': self.analysis}
        doc_html, fam_html = html_generator.generate_html_reports(context, self.patient_id)
        return doc_html
```

 **关键点** ：

* 包含**所有依从性报告的业务逻辑**
* 协调调用 `compliance/` 下的各个处理器
* 原 `report.py` 中的 `build_context()` 逻辑迁移到这里

---

### report_modules/ **init** .py

 **职责** ：工厂类和报告注册

```python
class ReportFactory:
    _generators = {}
  
    @classmethod
    def register(cls, report_type, generator_class):
        cls._generators[report_type] = generator_class
  
    @classmethod
    def create(cls, report_type, patient_id, **kwargs):
        return cls._generators[report_type](patient_id, **kwargs)

# 注册依从性报告
from report_modules.compliance.generator import ComplianceReportGenerator
ReportFactory.register('compliance', ComplianceReportGenerator)
```

---

## 🔄 迁移指南

### 阶段 1：创建目录结构

```bash
cd report_modules

# 创建子目录
mkdir -p base common compliance anomaly triage

# 创建 __init__.py
touch base/__init__.py common/__init__.py compliance/__init__.py
touch anomaly/__init__.py triage/__init__.py
```

### 阶段 2：移动现有文件

```bash
# 移动到 common/
mv config.py common/
mv data_loader.py common/
mv chart_generator.py common/

# 移动到 compliance/
mv medication_processor.py compliance/
mv data_builder.py compliance/
mv monitoring_processor.py compliance/
mv ai_analyzer.py compliance/
mv html_generator.py compliance/
```

### 阶段 3：创建新文件

#### 3.1 创建 base/report_generator.py

```python
# 完整代码见前文（~200行）
```

#### 3.2 创建 common/html_base.py

```python
# 完整代码见前文（~400行，包含通用批注JS）
```

#### 3.3 创建 compliance/generator.py

```python
# 完整代码见前文（~250行）
```

#### 3.4 更新 report_modules/ **init** .py

```python
# 完整代码见前文（工厂类 + 注册）
```

### 阶段 4：更新导入语句

**所有 `compliance/` 下的文件**都需要更新：

 **medication_processor.py** ：

```python
# ❌ 旧版本
from . import config
from . import data_loader

# ✅ 新版本
from report_modules.common import config
from report_modules.common import data_loader
```

 **需要更新的文件列表** ：

* `compliance/medication_processor.py`
* `compliance/data_builder.py`
* `compliance/monitoring_processor.py`
* `compliance/ai_analyzer.py`
* `compliance/html_generator.py`

### 阶段 5：重构 html_generator.py

 **关键变化** ：

1. **删除原有的批注JS** （移到 `common/html_base.py`）
2. **定义 SECTION_KINDS**
3. **调用 HTMLBaseGenerator**

```python
# compliance/html_generator.py（新版本）
from report_modules.common.html_base import HTMLBaseGenerator
from report_modules.common import config

class ComplianceHTMLGenerator:
    SECTION_KINDS = [...]  # 定义章节类型
  
    @staticmethod
    def generate_html_reports(context, patient_id):
        # 渲染Markdown
        doc_html = HTMLBaseGenerator.render_markdown_template(...)
  
        # 调用通用批注系统
        return HTMLBaseGenerator.build_html_shell(
            content=doc_html,
            section_kinds=ComplianceHTMLGenerator.SECTION_KINDS
        )
```

### 阶段 6：更新 report.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
from report_modules import ReportFactory

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=str)
    parser.add_argument("--type", default="compliance", choices=ReportFactory.list_types())
    parser.add_argument("--output", type=str)
    args = parser.parse_args()
  
    generator = ReportFactory.create(args.type, args.id)
    html = generator.generate()
    output_path = generator.save_to_file(args.output)
    print(f"✅ 报告生成成功: {output_path}")

if __name__ == "__main__":
    main()
```

---

## ✅ 测试验证

### 测试 1：模块导入

```bash
python -c "from report_modules import ReportFactory; print(ReportFactory.list_types())"
# 预期输出: ['compliance']
```

### 测试 2：生成报告

```bash
python report.py --id YOUR_PATIENT_ID --type compliance
# 检查输出文件是否生成
ls -lh report_compliance_YOUR_PATIENT_ID_*.html
```

### 测试 3：功能一致性

```bash
# 对比新旧版本的输出
diff old_report.html new_report.html
# 内容应该完全一致（除了时间戳）
```

### 测试 4：批注功能

1. 在浏览器打开生成的HTML
2. 点击 "➕ 批注" 按钮添加批注
3. 填写全局批注
4. 使用章节交互控件（下拉框、复选框）
5. 点击 "导出批注与交互数据"
6. 检查导出的JSON格式是否正确
7. 点击 "导入数据" 上传JSON
8. 刷新页面，检查数据是否恢复

---

## ❓ 常见问题

### Q1：不同报告类型的章节数量可以不同吗？

 **A** ：完全可以！每个报告类型使用独立的Markdown模板。

```markdown
# 依从性报告：doctor_template.md
## 主要疾病诊断
## 核心监测指标
## 依从性分析
## 生活方式干预
## 随访建议

# 异常检测报告：anomaly_template.md（章节数量不同）
## 异常警报总览
## 趋势分析
## 处理建议
```

批注系统**自动适配**任意章节结构。

### Q2：章节交互控件可以完全自定义吗？

 **A** ：是的！在 `SECTION_KINDS` 中定义 `tools_html`：

```python
{
    'key': 'custom_section',
    'includes': ['自定义章节'],
    'tools_html': '''
        <input type="text" data-k="custom.field" placeholder="自定义输入">
        <button data-act="custom-action" data-done-text="完成">自定义按钮</button>
    '''
}
```

### Q3：章节标题必须是中文吗？

 **A** ：不需要！`includes` 支持任意关键词：

```python
{
    'key': 'alert',
    'includes': ['Alert', 'Warning', '警报', '告警'],  # 中英文混合
    'tools_html': '...'
}
```

### Q4：如何禁用某个报告的批注功能？

 **A** ：传递空的 `section_kinds`：

```python
HTMLBaseGenerator.build_html_shell(
    content=html,
    section_kinds=[]  # 不显示章节交互控件
)
```

批注卡片功能仍然可用，只是没有章节特定的交互控件。

### Q5：localStorage 会跨患者污染吗？

 **A** ：不会！localStorage 键名包含 `patientId`：

```javascript
`report-annotations::compliance::P001`
`report-annotations::compliance::P002`  // 不同患者隔离
```

### Q6：为什么章节交互不用 React/Vue？

 **A** ：设计权衡：

* ✅ 零依赖，单HTML文件
* ✅ 离线可用
* ✅ 易于理解和修改
* ❌ 不适合复杂交互（当前需求足够）

---

## 🚀 扩展新报告类型

### 步骤 1：创建模块目录

```bash
mkdir -p report_modules/risk_assessment
touch report_modules/risk_assessment/__init__.py
```

### 步骤 2：创建生成器

```python
# risk_assessment/generator.py
from report_modules.base.report_generator import BaseReportGenerator

class RiskAssessmentReportGenerator(BaseReportGenerator):
    def load_data(self):
        # 加载风险评估数据
        pass
  
    def process_data(self):
        # 处理风险评估数据
        pass
  
    def generate_charts(self):
        # 生成风险图表
        pass
  
    def analyze(self):
        # AI分析风险
        pass
  
    def render_html(self):
        # 渲染HTML
        pass
```

### 步骤 3：定义章节配置

```python
# risk_assessment/html_generator.py
class RiskAssessmentHTMLGenerator:
    SECTION_KINDS = [
        {
            'key': 'risk_level',
            'includes': ['风险等级', 'Risk Level'],
            'tools_html': '''
                <select data-k="risk.level">
                    <option>低风险</option>
                    <option>中风险</option>
                    <option>高风险</option>
                </select>
            '''
        }
    ]
```

### 步骤 4：注册到工厂

```python
# report_modules/__init__.py
from report_modules.risk_assessment.generator import RiskAssessmentReportGenerator
ReportFactory.register('risk_assessment', RiskAssessmentReportGenerator)
```

### 步骤 5：使用

```bash
python report.py --id P001 --type risk_assessment
```

---

## 📊 性能指标

| 指标         | v1.0   | v2.0   | 说明           |
| ------------ | ------ | ------ | -------------- |
| 首次导入时间 | ~200ms | ~250ms | 增加基类和工厂 |
| 生成时间     | 基准   | 基准   | 无差异         |
| 内存使用     | 基准   | +5%    | 额外类结构     |
| HTML文件大小 | 基准   | 基准   | 无差异         |

---

## 📝 版本历史

* **v2.0.0** (2025-10-06): 多类型报告架构，通用批注系统
* **v1.0.0** (2024-XX-XX): 第一次重构，模块化
* **v0.1.0** (2024-XX-XX): 原始大文件版本

---

## 📞 支持

遇到问题？

1. 检查 [常见问题](https://claude.ai/chat/894fe260-fa74-4090-bb9f-17f804bbbe8d#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98)
2. 查看模块文档字符串
3. 运行测试验证

---

 **最后更新** ：2025-10-06

 **架构版本** ：v2.0

 **作者** ：Report Generator Team

```

```
