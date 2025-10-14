# 简化版慢性病报告生成系统

一个极简的患者报告生成工具，只需输入患者ID即可自动查找数据并生成健康报告。

## 🎯 核心功能

- **输入患者ID** - 支持 P001, P002, P003
- **自动查找数据** - 从现有数据文件中匹配患者信息
- **生成报告** - 支持服药依从性评估和分诊评估两种类型
- **即时预览** - 生成后直接在浏览器中查看报告

## 🚀 快速开始

### 方法1: 一键启动（推荐）
```bash
python start_simple.py
```

### 方法2: 分别启动
```bash
# 启动后端服务
python simple_server.py

# 然后在浏览器中打开
frontend/simple.html
```

## 📁 文件结构

```
├── start_simple.py           # 一键启动脚本
├── simple_server.py          # 简化版后端API
├── frontend/
│   └── simple.html          # 简化版前端界面
└── data/                    # 患者数据目录
    └── dialogue_data/       # 对话数据文件
```

## 💡 使用说明

1. **启动系统**: 运行 `python start_simple.py`
2. **输入患者ID**: 在界面中输入 P001、P002 或 P003
3. **选择报告类型**: 选择"服药依从性评估"或"分诊评估"
4. **生成报告**: 点击"生成报告"按钮
5. **查看结果**: 等待生成完成，点击查看报告链接

## 🔧 API接口

- `GET /api/patients/{patient_id}` - 获取患者信息
- `POST /api/generate-report` - 生成报告
- `GET /api/reports/{patient_id}/{type}.html` - 查看报告

## 📋 测试数据

| 患者ID | 姓名 | 年龄 | 诊断 |
|--------|------|------|------|
| P001   | 张三 | 65岁 | 2型糖尿病,高血压 |
| P002   | 李四 | 58岁 | 高血压,冠心病 |
| P003   | 王五 | 72岁 | 慢性肾病,糖尿病 |

## ⚠️ 注意事项

- 确保 `data/dialogue_data/` 目录中有对应的患者数据文件
- 首次使用需要安装 Flask: `pip install flask`
- 报告生成需要调用现有的报告生成模块

## 🛠️ 自定义配置

### 添加新患者
在 `simple_server.py` 中的 `PATIENT_MAPPING` 字典添加新的映射：

```python
PATIENT_MAPPING = {
    'P004': 'your_data_file_id_here'
}
```

### 修改界面
编辑 `frontend/simple.html` 文件的样式和功能

### 连接现有系统
修改 `simple_server.py` 中的报告生成逻辑，调用您现有的Python报告生成模块

## 📞 问题排查

**问题**: 找不到患者数据
**解决**: 检查患者ID是否正确，确保数据文件存在

**问题**: 报告生成失败
**解决**: 检查报告生成模块是否正常工作

**问题**: 无法访问界面
**解决**: 确保服务器正常启动，端口5000未被占用