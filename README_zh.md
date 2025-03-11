# 论文分析工具 (Paper Analysis Tool)

[English](README.md) | [中文](README_zh.md)

一个基于PyQt6开发的论文分析工具，支持批量分析PDF论文并生成汇总报告。该工具使用先进的AI模型来分析论文的实现类型（official/unofficial），并提供详细的分析依据。

## ✨ 主要特性

- 📄 **批量PDF分析**：支持批量导入和分析PDF论文
- 🤖 **AI智能分析**：使用先进的AI模型分析论文实现类型
- 📊 **自动汇总**：自动生成分析汇总报告
- 🔄 **断点续传**：支持分析中断后继续分析
- ⚡ **超时重试**：内置超时检测和自动重试机制
- 📝 **自定义提示词**：支持自定义分析和汇总提示词
- 🔍 **文件索引**：自动生成和维护文件索引
- 📈 **进度跟踪**：实时显示分析进度和状态
- 💾 **结果保存**：自动保存分析结果和汇总报告

## 🚀 快速开始

### 环境要求

- Python 3.12+
- 主要依赖包：
  ```bash
  pip install pyyaml        # YAML配置文件支持
  pip install markdown      # Markdown处理
  pip install markitdown    # Markdown转换工具
  pip install python-docx   # Word文档处理
  pip install beautifulsoup4 # HTML解析
  pip install PyMuPDF       # PDF文件处理
  pip install PyQt6         # GUI界面
  pip install PySide6       # Qt6 Python绑定
  ```

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/paper-analysis-tool.git
cd paper-analysis-tool
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python main.py
```

## 📖 使用说明

### 基本使用流程

1. **选择目录**
   - 点击"选择目录"按钮选择包含PDF论文的文件夹
   - 系统会自动扫描并建立文件索引

2. **选择文件**
   - 在文件选择对话框中勾选需要分析的论文
   - 支持按序号快速定位文件

3. **配置分析参数**
   - 选择AI服务提供商和模型
   - 可以自定义分析提示词和汇总提示词

4. **开始分析**
   - 点击"开始分析"按钮开始处理
   - 系统会自动跳过大于30MB的文件
   - 支持随时暂停和继续分析

5. **查看结果**
   - 实时显示每篇论文的分析结果
   - 可以生成汇总报告
   - 支持导出分析结果

### 高级功能

- **自定义提示词**：可以保存自定义的分析和汇总提示词
- **文件索引**：自动生成文件汇总表格，包含文件大小、分析状态等信息
- **超时处理**：自动检测分析超时并重试
- **断点续传**：支持分析中断后继续未完成的分析

## 🔧 配置说明

### AI服务配置

支持多个AI服务提供商：
- OpenAI
- Grok
- Deepseek

每个服务提供商支持多个模型，可以在界面上自由切换。

### 超时设置

默认超时时间为5分钟，最大重试次数为3次。这些参数可以在代码中调整：
```python
TIMEOUT_SECONDS = 300  # 5分钟超时
MAX_RETRIES = 3       # 最大重试次数
```

## 📝 输出文件

- **分析结果**：每篇论文的分析结果保存在同目录下的`{文件名}_analysis.txt`文件中
- **汇总报告**：汇总报告保存在`summaries`目录下，文件名包含时间戳
- **文件索引**：文件汇总表格保存在`summaries`目录下

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目。在提交代码前，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的注释和文档
3. 更新了相关的测试用例

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者们！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[xingshizhai@gmail.com]

---
如果这个项目对您有帮助，请考虑给它一个 ⭐️
