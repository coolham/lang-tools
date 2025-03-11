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
- Key Dependencies:
  ```bash
  pip install pyyaml        # YAML configuration support
  pip install markdown      # Markdown processing
  pip install markitdown    # Markdown conversion tool
  pip install python-docx   # Word document processing
  pip install beautifulsoup4 # HTML parsing
  pip install PyMuPDF       # PDF file processing
  pip install PyQt6         # GUI interface
  pip install PySide6       # Qt6 Python bindings
  ```

### Installation

#### Option 1: Direct Installation

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

#### Option 2: Docker Installation

1. Build Docker image
```bash
docker build -t paper-analysis-tool .
```

2. Run Docker container
```bash
# Linux/macOS
docker run -d \
  --name paper-analysis \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  paper-analysis-tool

# Windows (PowerShell)
docker run -d `
  --name paper-analysis `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/config:/app/config `
  -e DISPLAY=host.docker.internal:0 `
  paper-analysis-tool
```

3. View container logs
```bash
docker logs -f paper-analysis
```

Note:
- X11 forwarding needs to be properly configured to display the GUI interface when using Docker
- Windows users need to install an X Server (such as VcXsrv or Xming)
- Data and configuration files should be persisted using volume mounts

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

The project supports multiple AI service providers. To configure them:

1. Copy the template configuration file:
```bash
cp config/local.json.template config/local.json
```

2. Configure your preferred AI service:

#### OpenAI (via OpenRouter)
```json
"openai": {
    "default_provider": "openrouter",
    "default_model": "gpt-3.5-turbo",
    "providers": {
        "openrouter": {
            "api_key": "YOUR_OPENROUTER_API_KEY",
            "models": {
                "gpt-3.5-turbo": {
                    "internal_name": "openai/gpt-3.5-turbo",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
                // ... other models ...
            }
        }
    }
}
```

#### Deepseek
```json
"deepseek": {
    "providers": {
        "official": {
            "api_key": "YOUR_DEEPSEEK_API_KEY"
        },
        "zhipu": {
            "api_key": "YOUR_ZHIPU_API_KEY"
        },
        "siliconflow": {
            "api_key": "YOUR_SILICONFLOW_API_KEY"
        }
    }
}
```

#### Grok
```json
"grok": {
    "default_provider": "official",
    "default_model": "grok-2",
    "providers": {
        "official": {
            "api_key": "YOUR_GROK_API_KEY",
            "enabled": true,
            "use_proxy": true,
            "base_url": "https://api.x.ai/v1"
        },
        "superlang": {
            "api_key": "YOUR_GROK_API_KEY",
            "enabled": true,
            "use_proxy": false,
            "base_url": "http://grok.superlang.top/v1"
        }
    }
}
```

### Proxy Configuration

If you need to use a proxy for API access:

```json
"proxy": {
    "http": {
        "enabled": true,
        "host": "127.0.0.1",
        "port": 10808,
        "username": "",
        "password": ""
    },
    "https": {
        "enabled": true,
        "host": "127.0.0.1",
        "port": 10808,
        "username": "",
        "password": ""
    }
}
```

### Logging Configuration

Configure logging level and file handling:

```json
"logging": {
    "level": "INFO",
    "fixed_filename": true
}
```

### Database Configuration

If you need database support:

```json
"database": {
    "host": "localhost",
    "port": 5432,
    "username": "YOUR_DB_USERNAME",
    "password": "YOUR_DB_PASSWORD"
}
```

### Redis Configuration

For Redis support:

```json
"redis": {
    "host": "localhost",
    "port": 6379,
    "password": "YOUR_REDIS_PASSWORD"
}
```

### Security Configuration

```json
"jwt_secret": "YOUR_JWT_SECRET",
"other_secrets": {}
```

### Important Notes

1. Never commit your `local.json` file to version control
2. Keep your API keys secure and never share them
3. Use environment variables for sensitive information in production
4. Make sure to enable the proxy if you're behind a corporate firewall
5. Adjust the logging level based on your needs (DEBUG, INFO, WARNING, ERROR)

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

