# AI 剧本评测系统

使用豆包 seed-1.8 模型进行短剧剧本质量评测的 Python 工具。

## 功能特性

- **多维度评测**: 从5个专业维度评估剧本质量
  - 故事结构 (25%)
  - 人物塑造 (25%)
  - 对话质量 (20%)
  - 短剧特质 (15%)
  - 商业价值 (15%)

- **灵活输出**: 支持 Markdown 和 JSON 两种报告格式
- **批量处理**: 支持批量评测多个剧本并生成汇总报告
- **CLI 工具**: 命令行界面，操作简单便捷

## 项目结构

```
evaluate_novels_scripts/
├── main.py                 # 主程序入口
├── config.yml             # 评测配置文件
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量示例
├── src/
│   ├── api_client.py      # 豆包 API 客户端
│   ├── evaluator.py       # 剧本评测器
│   └── report_generator.py # 报告生成器
├── prompts/               # 提示词模板目录
│   ├── structure.txt      # 故事结构评测
│   ├── characters.txt     # 人物塑造评测
│   ├── dialogue.txt       # 对话质量评测
│   ├── drama_traits.txt   # 短剧特质评测
│   └── commercial.txt     # 商业价值评测
├── scripts/               # 待评测的剧本目录
│   └── example.txt        # 示例剧本
└── outputs/               # 评测报告输出目录
```

## 快速开始

### 1. 创建虚拟环境

```bash
cd evaluate_novels_scripts
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

复制 `.env.example` 为 `.env` 并填入豆包 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置：

```env
DOUBAO_API_KEY=your_actual_api_key_here
DOUBAO_API_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
MODEL_NAME=ep-20241227143231-pz6wm  # seed-1.8 模型 endpoint
```

### 4. 检查配置

```bash
python main.py check-config
```

## 使用方法

### 评测单个剧本

```bash
python main.py evaluate scripts/example.txt
```

### 指定评测维度

```bash
python main.py evaluate scripts/example.txt -d structure -d dialogue
```

### 指定输出格式

```bash
python main.py evaluate scripts/example.txt -f markdown -f json
```

### 批量评测

```bash
python main.py batch scripts/ --summary
```

### 查看所有可用维度

```bash
python main.py list-dimensions
```

### 命令行帮助

```bash
python main.py --help
```

## 评测维度说明

| 维度 | 权重 | 说明 |
|------|------|------|
| structure | 25% | 故事结构完整性、起承转合、情节节奏、高潮设置、逻辑连贯性 |
| characters | 25% | 人物塑造、角色性格、对话一致性、情感表达 |
| dialogue | 20% | 台词精彩度、口语化程度、潜台词、冲突性 |
| drama_traits | 15% | 开篇吸引力、反转设计、爽点密度 |
| commercial | 15% | 受众匹配度、传播潜力、变现能力 |

## 输出示例

评测完成后，会在 `outputs/` 目录生成报告文件：

- **Markdown 报告**: 包含详细分析和建议的可读报告
- **JSON 报告**: 机器可读的结构化数据

评分等级：
- **S级**: 90分及以上
- **A级**: 80-89分
- **B级**: 70-79分
- **C级**: 60-69分
- **D级**: 60分以下

## 依赖项

- Python 3.8+
- requests
- pyyaml
- python-dotenv
- orjson
- tqdm
- click

## 注意事项

1. 请确保已配置有效的豆包 API 密钥
2. 长剧本可能会被截断，可在 [config.yml](config.yml) 中调整 `script.max_length`
3. 批量评测会消耗较多 API 调用次数，请注意成本
4. 网络不稳定时可能需要重试

## License

MIT
