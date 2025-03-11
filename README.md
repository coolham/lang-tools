# Paper Analysis Tool

[English](README.md) | [中文](README_zh.md)

A PyQt6-based tool for batch analysis of PDF papers and summary report generation. This tool uses advanced AI models to analyze paper implementation types (official/unofficial) and provides detailed analysis evidence.

## ✨ Key Features

- 📄 **Batch PDF Analysis**: Support batch import and analysis of PDF papers
- 🤖 **AI-Powered Analysis**: Utilize advanced AI models for implementation type analysis
- 📊 **Auto Summary**: Automatically generate analysis summary reports
- 🔄 **Breakpoint Resume**: Support continuing analysis after interruption
- ⚡ **Timeout Retry**: Built-in timeout detection and automatic retry mechanism
- 📝 **Custom Prompts**: Support custom analysis and summary prompts
- 🔍 **File Indexing**: Automatic file index generation and maintenance
- 📈 **Progress Tracking**: Real-time analysis progress and status display
- 💾 **Result Saving**: Automatic saving of analysis results and summary reports

## 🚀 Quick Start

### Requirements

- Python 3.12+
- PyQt6
- PyMuPDF
- Other dependencies (see requirements.txt)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/paper-analysis-tool.git
cd paper-analysis-tool
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the program
```bash
python main.py
```

## 📖 Usage Guide

### Basic Workflow

1. **Select Directory**
   - Click "Select Directory" button to choose a folder containing PDF papers
   - System will automatically scan and build file index

2. **Select Files**
   - Check the papers you want to analyze in the file selection dialog
   - Support quick file location by index number

3. **Configure Analysis Parameters**
   - Choose AI service provider and model
   - Customize analysis and summary prompts if needed

4. **Start Analysis**
   - Click "Start Analysis" button to begin processing
   - System will automatically skip files larger than 30MB
   - Support pause and resume analysis at any time

5. **View Results**
   - Real-time display of analysis results for each paper
   - Generate summary reports
   - Export analysis results

### Advanced Features

- **Custom Prompts**: Save custom analysis and summary prompts
- **File Index**: Auto-generate file summary table with file size, analysis status, etc.
- **Timeout Handling**: Automatic timeout detection and retry
- **Breakpoint Resume**: Continue unfinished analysis after interruption

## 🔧 Configuration

### AI Service Configuration

Support multiple AI service providers:
- OpenAI
- Grok
- Deepseek

Each service provider supports multiple models that can be switched freely in the interface.

### Timeout Settings

Default timeout is 5 minutes with maximum 3 retries. These parameters can be adjusted in the code:
```python
TIMEOUT_SECONDS = 300  # 5 minutes timeout
MAX_RETRIES = 3       # Maximum retry attempts
```

## 📝 Output Files

- **Analysis Results**: Individual paper analysis results are saved as `{filename}_analysis.txt` in the same directory
- **Summary Reports**: Summary reports are saved in the `summaries` directory with timestamps
- **File Index**: File summary tables are saved in the `summaries` directory

## 🤝 Contributing

Contributions via Issues and Pull Requests are welcome! Before submitting code, please ensure:

1. Code follows project coding standards
2. Necessary comments and documentation are added
3. Related test cases are updated

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Thanks to all developers who have contributed to this project!

## 📞 Contact

For questions or suggestions, please:

- Submit an Issue
- Send email to: [xingshizhai@gmail.com]

---
If this project helps you, please consider giving it a ⭐️

