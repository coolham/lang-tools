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

#### 方式一：直接安装

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

#### 方式二：Docker 安装

1. 构建Docker镜像
```bash
docker build -t paper-analysis-tool .
```

2. 运行Docker容器
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

3. 查看容器日志
```bash
docker logs -f paper-analysis
```

注意：
- 使用Docker运行时，需要正确配置X11转发以显示GUI界面
- Windows用户需要安装X Server（如VcXsrv或Xming）
- 数据和配置文件建议使用卷挂载方式持久化

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

## �� 配置说明

### AI服务配置

本项目支持多个AI服务提供商，配置步骤如下：

1. 复制配置模板文件：
```bash
cp config/local.json.template config/local.json
```

2. 配置你需要的AI服务：

#### OpenAI (通过OpenRouter)
```json
"openai": {
    "default_provider": "openrouter",
    "default_model": "gpt-3.5-turbo",
    "providers": {
        "openrouter": {
            "api_key": "你的_OPENROUTER_API_密钥",
            "models": {
                "gpt-3.5-turbo": {
                    "internal_name": "openai/gpt-3.5-turbo",
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
                // ... 其他模型配置 ...
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
            "api_key": "你的_DEEPSEEK_API_密钥"
        },
        "zhipu": {
            "api_key": "你的_智谱_API_密钥"
        },
        "siliconflow": {
            "api_key": "你的_SILICONFLOW_API_密钥"
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
            "api_key": "你的_GROK_API_密钥",
            "enabled": true,
            "use_proxy": true,
            "base_url": "https://api.x.ai/v1"
        },
        "superlang": {
            "api_key": "你的_GROK_API_密钥",
            "enabled": true,
            "use_proxy": false,
            "base_url": "http://grok.superlang.top/v1"
        }
    }
}
```

### 代理配置

如果需要使用代理访问API：

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

### 日志配置

配置日志级别和文件处理：

```json
"logging": {
    "level": "INFO",
    "fixed_filename": true
}
```

### 数据库配置

如果需要数据库支持：

```json
"database": {
    "host": "localhost",
    "port": 5432,
    "username": "你的数据库用户名",
    "password": "你的数据库密码"
}
```

### Redis配置

Redis支持配置：

```json
"redis": {
    "host": "localhost",
    "port": 6379,
    "password": "你的Redis密码"
}
```

### 安全配置

```json
"jwt_secret": "你的JWT密钥",
"other_secrets": {}
```

### 重要注意事项

1. 切勿将 `local.json` 文件提交到版本控制系统
2. 妥善保管你的API密钥，不要分享给他人
3. 在生产环境中使用环境变量存储敏感信息
4. 如果在公司防火墙后面，请确保启用代理
5. 根据需要调整日志级别（DEBUG、INFO、WARNING、ERROR）

### 配置获取说明

1. **OpenRouter API密钥**：
   - 访问 [OpenRouter官网](https://openrouter.ai/)
   - 注册并创建API密钥

2. **Deepseek API密钥**：
   - 访问 [Deepseek官网](https://platform.deepseek.com/)
   - 注册账号并获取API密钥

3. **智谱API密钥**：
   - 访问 [智谱AI](https://open.bigmodel.cn/)
   - 注册开发者账号获取密钥

4. **Grok API密钥**：
   - 需要通过特定渠道申请
   - 或使用superlang提供的代理服务

### 模型选择建议

1. **论文分析推荐模型**：
   - GPT-4/Claude-2：分析准确度最高
   - GPT-3.5-turbo：性价比较高
   - Mixtral-8x7b：开源模型中表现最好

2. **批量处理建议**：
   - 使用OpenRouter可以自动负载均衡
   - 建议开启代理以提高连接稳定性
   - 对于大批量任务，建议使用较为经济的模型

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
