#!/usr/bin/env python3
"""
Flask Web 服务器
提供剧本评测的 Web 界面
"""

import os
import sys
import json
import uuid
import traceback
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.evaluator import ScriptEvaluator
from src.report_generator import ReportGenerator
from src.history_manager import HistoryManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'outputs')

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 初始化历史记录管理器
history_manager = HistoryManager()

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'txt'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    """从 PDF 文件中提取文本"""
    text = ""
    extraction_method = ""

    # 首先尝试 pdfplumber（通常对中文支持更好）
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        extraction_method = "pdfplumber"
        logger.info(f"使用 pdfplumber 成功提取文本，共 {len(text)} 字符")
    except Exception as e:
        logger.warning(f"pdfplumber 提取失败: {str(e)}，尝试 PyPDF2")
        # 回退到 PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            extraction_method = "PyPDF2"
            logger.info(f"使用 PyPDF2 成功提取文本，共 {len(text)} 字符")
        except Exception as e2:
            logger.error(f"PyPDF2 提取也失败: {str(e2)}")
            raise RuntimeError(f"无法解析 PDF 文件。请确保 PDF 包含可提取的文本（而非扫描图片）。错误: {str(e2)}")

    # 检查提取的有效性
    if len(text.strip()) < 50:
        raise RuntimeError(f"PDF 文本提取失败：提取的文本过短（{len(text.strip())} 字符）。可能是：1) 扫描版 PDF（图片格式）2) 加密或损坏的 PDF。请尝试使用可复制文本的 PDF 文件。")

    # 检查是否包含大量 PDF 底层代码（表示提取失败）
    pdf_indicators = ['/Rect', '/Font', '/Subtype', '/Resources', '/MediaBox', 'stream', 'endstream']
    indicator_count = sum(1 for indicator in pdf_indicators if indicator in text)
    if indicator_count >= 3:
        logger.error(f"检测到 PDF 底层代码，提取可能失败")
        raise RuntimeError(f"PDF 文本提取异常：内容包含 PDF 底层代码。这通常表示 PDF 文件格式特殊或损坏。请尝试重新导出 PDF 文件，或使用 TXT 格式。")

    # 清理文本，移除无效字符，保留中文、英文、数字和常用标点
    import re
    # 保留：中文字符、字母、数字、常用标点、换行符
    text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\s\.,!?;:：，。！？；、\(\)\[\]""''《》·—\n\r\t]', '', text)
    # 移除过多的空白行
    text = re.sub(r'\n\s*\n', '\n\n', text)

    logger.info(f"PDF 文本清理完成，最终长度: {len(text.strip())} 字符")
    return text.strip()


def extract_text_from_file(file_path, file_ext):
    """根据文件类型提取文本"""
    if file_ext == 'pdf':
        return extract_text_from_pdf(file_path)
    else:
        # txt 文件读取，尝试多种编码
        text = None
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue

        # 如果都失败，使用 errors='ignore'
        if text is None:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

        # 清理和规范化文本
        text = clean_script_text(text)
        return text


def clean_script_text(text: str) -> str:
    """
    清理和规范化剧本文本

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    import re

    # 1. 移除 BOM 标记
    text = text.replace('\ufeff', '')

    # 2. 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 3. 移除连续的空行（保留最多一个空行）
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # 4. 清理行首行尾空白
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # 5. 移除全角空格和半角空格的混合
    text = text.replace('\u3000', ' ')  # 全角空格转半角

    # 6. 移除不可见字符（保留换行、制表符、常用标点）
    # 保留中文、英文、数字、常用标点、换行符
    text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbfa-zA-Z0-9\s\.,!?;:：，。！？；、\(\)\[\]""''《》·—·…～–—/=@#\\%\^&\*\+\|\{\}\<\>\n\r\t]', '', text)

    # 7. 修复常见的格式问题
    # 修复括号不匹配问题（移除孤立的括号）
    text = re.sub(r'【([^】]*$)', r'【\1】', text)  # 缺失的右括号

    # 8. 移除过长的单行（可能是格式错误）
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # 如果单行超过500字符且没有标点，可能是格式错误，尝试分割
        if len(line) > 500 and not any(punct in line[-100:] for punct in ['。', '！', '？', '.', '!', '?', '】']):
            # 尝试按标点分割
            parts = re.split(r'([。！？\.!?])', line)
            if len(parts) > 1:
                # 重组句子
                new_line = ''
                for i in range(0, len(parts) - 1, 2):
                    if i + 1 < len(parts):
                        new_line += parts[i] + parts[i + 1] + '\n'
                    else:
                        new_line += parts[i]
                if parts[-1]:
                    new_line += parts[-1]
                cleaned_lines.append(new_line.strip())
            else:
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # 9. 最终清理多余的空行
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # 10. 记录清理信息
    original_len = len(text)
    logger.info(f"文本清理完成: 原始 {original_len} 字符 -> 最终 {len(text)} 字符")

    return text.strip()


@app.route('/')
def index():
    """首页"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        logger.error(traceback.format_exc())
        return f"<h1>Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"


@app.route('/api/dimensions', methods=['GET'])
def get_dimensions():
    """获取所有评测维度"""
    try:
        evaluator = ScriptEvaluator()
        dimensions = evaluator.config.get('evaluation_dimensions', {})

        result = []
        for key, config in dimensions.items():
            result.append({
                'key': key,
                'name': config.get('name', key),
                'weight': config.get('weight', 0),
                'description': config.get('description', '')
            })

        return jsonify({
            'success': True,
            'dimensions': result
        })
    except Exception as e:
        logger.error(f"Error getting dimensions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """评测剧本"""
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未上传文件'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '未选择文件'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '只支持 .txt 格式的剧本文件'
            }), 400

        # 获取选中的维度
        dimensions = request.form.get('dimensions')
        dimension_list = dimensions.split(',') if dimensions else None

        # 保存原始文件名（用于显示）
        original_filename = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename

        # 保存文件（使用 secure_filename 处理，避免文件系统问题）
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())[:8]
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(script_path)

        # 如果是 PDF 文件，先转换为文本
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        temp_txt_path = None
        actual_script_path = script_path

        if file_ext == 'pdf':
            try:
                # 提取 PDF 文本
                text_content = extract_text_from_file(script_path, file_ext)

                # 保存为临时 txt 文件
                temp_txt_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}.txt")
                with open(temp_txt_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)

                actual_script_path = temp_txt_path
            except Exception as e:
                # 清理文件
                try:
                    os.remove(script_path)
                except:
                    pass
                raise RuntimeError(f"PDF 文件解析失败: {str(e)}")

        # 执行评测
        logger.info(f"开始评测剧本: {original_filename}, 维度: {dimension_list}")
        evaluator = ScriptEvaluator()
        result = evaluator.evaluate(actual_script_path, dimensions=dimension_list, show_progress=False)
        logger.info(f"评测完成，准备生成报告")

        # 生成报告
        logger.info("开始生成报告...")
        report_generator = ReportGenerator(output_dir=app.config['OUTPUT_FOLDER'])
        result['script_name'] = original_filename  # 使用原始文件名
        logger.info(f"剧本名称: {result['script_name']}")

        # 预检查：验证数据是否可序列化
        logger.info("验证数据可序列化...")
        try:
            json.dumps(result)
            logger.info("数据序列化检查通过")
        except Exception as e:
            logger.error(f"数据序列化失败: {e}")
            # 移除可能有问题的字段
            result_clean = {}
            for key, value in result.items():
                try:
                    json.dumps({key: value})
                    result_clean[key] = value
                except:
                    logger.warning(f"跳过无法序列化的字段: {key}")
            result = result_clean

        report_files = report_generator.generate(result, formats=['markdown', 'json', 'word', 'ppt'])
        logger.info(f"报告生成完成: {report_files}")

        # 获取报告文件名（用于下载）
        result['report_files'] = [os.path.basename(f) for f in report_files]

        # 保存历史记录
        try:
            record_id = history_manager.add_record(result)
            result['record_id'] = record_id
            logger.info(f"历史记录已保存: {record_id}")
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")

        # 清理上传的临时文件
        logger.info("清理临时文件...")
        try:
            os.remove(script_path)
            if temp_txt_path and os.path.exists(temp_txt_path):
                os.remove(temp_txt_path)
        except:
            pass

        logger.info("准备返回响应...")
        logger.info(f"响应数据大小估算: {len(str(result))} 字符")

        # 构建响应数据
        response_data = {
            'success': True,
            'result': result
        }

        logger.info("构建 JSON 响应...")
        logger.info(f"响应键: {list(response_data.keys())}")
        logger.info(f"结果键: {list(result.keys())}")

        # 尝试序列化
        try:
            json_response = jsonify(response_data)
            logger.info("JSONify 成功，准备返回")
            return json_response
        except Exception as e:
            logger.error(f"JSONify 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回简化版本
            simple_response = {
                'success': True,
                'result': {
                    'script_name': result.get('script_name', ''),
                    'overall': result.get('overall', {}),
                    'report_files': result.get('report_files', [])
                }
            }
            return jsonify(simple_response)

    except Exception as e:
        logger.error(f"Error in evaluate: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500


@app.route('/api/reports/<filename>', methods=['GET'])
def get_report(filename):
    """获取报告文件"""
    try:
        report_path = os.path.join(app.config['OUTPUT_FOLDER'], secure_filename(filename))
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    try:
        from dotenv import load_dotenv
        load_dotenv()

        model_endpoint = os.getenv("MODEL_ENDPOINT", "")
        base_url = os.getenv("ARK_BASE_URL", "")

        return jsonify({
            'success': True,
            'config': {
                'model_endpoint': model_endpoint,
                'base_url': base_url
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/improve', methods=['POST'])
def improve_script():
    """根据评测建议改进剧本"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '未请求数据'
            }), 400

        original_script_name = data.get('original_script_name', '剧本')
        suggestions = data.get('suggestions', {})
        evaluation_result = data.get('evaluation_result', {})

        # 读取原剧本内容
        script_path = evaluation_result.get('script_path', '')
        original_script_content = ""
        if script_path and os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    original_script_content = f.read()
                logger.info(f"成功读取原剧本，长度: {len(original_script_content)} 字符")
            except Exception as e:
                logger.error(f"读取原剧本失败: {e}")
                original_script_content = ""

        # 构建 AI 提示词
        prompt = build_improve_prompt(original_script_name, suggestions, evaluation_result, original_script_content)

        # 记录提示词中的集数要求，用于调试
        import re
        episode_match = re.search(r'原剧本共有 (\d+) 集', prompt)
        if episode_match:
            detected_episodes = episode_match.group(1)
            logger.info(f"📊 改进剧本: {original_script_name}, 要求集数: {detected_episodes}集")

        logger.info(f"开始根据建议改进剧本: {original_script_name}")

        # 调用 API 生成改进后的剧本
        from src.api_client import DoubaoAPIClient
        api_client = DoubaoAPIClient()

        system_prompt = """你是一位专业的短剧编剧，擅长根据反馈意见改进剧本。
请根据提供的修改建议，重新编写或改进原剧本的相应部分。
改进后的剧本应该：
1. 保持原有的风格和特色
2. 针对每个建议进行具体改进
3. 保持剧本的完整性和连贯性
4. 输出完整的改进后剧本，包含标题、人物设定、分集剧本等所有部分"""

        try:
            improved_script = api_client.chat(prompt, system_prompt)

            logger.info(f"剧本改进成功，生成 {len(improved_script)} 字符")

            return jsonify({
                'success': True,
                'improved_script': improved_script
            })

        except Exception as e:
            logger.error(f"API 调用失败: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f'生成改进剧本失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"Error in improve_script: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500


def build_improve_prompt(script_name, suggestions, evaluation_result, original_script_content=""):
    """
    构建剧本改进的提示词

    Args:
        script_name: 原剧本名称
        suggestions: 各维度的修改建议
        evaluation_result: 完整的评测结果
        original_script_content: 原剧本完整内容

    Returns:
        完整的提示词
    """

    # 尝试从原剧本内容中检测集数
    episode_count = 0  # 默认为0，确保是整数
    if original_script_content:
        # 检测常见的集数标记模式
        import re

        # 方法1: 匹配 "第X集"、"第 X 集"、"Episode X" 等模式
        episode_patterns = [
            r'第(\d+)集',
            r'第\s*(\d+)\s*集',
            r'Episode\s*(\d+)',
            r'EP[.\s]*(\d+)',
            r'第(\d+)章',
            r'第\s*(\d+)\s*章'
        ]
        episodes_found = []
        for pattern in episode_patterns:
            matches = re.findall(pattern, original_script_content, re.IGNORECASE)
            if matches:
                episodes_found.extend([int(m) for m in matches])

        # 方法2: 检测"分集剧本"部分后的数字行（格式如："1"、"2"、"3"等）
        if not episodes_found:
            # 查找"分集剧本"之后的内容
            episode_section_match = re.search(r'分集剧本\s*(.*?)(?=\n\s*\n|\Z)', original_script_content, re.DOTALL)
            if episode_section_match:
                episode_section = episode_section_match.group(1)
                # 匹配独立的数字行（集数标记）
                standalone_numbers = re.findall(r'^(\d+)$', episode_section, re.MULTILINE)
                if standalone_numbers:
                    episodes_found.extend([int(n) for n in standalone_numbers])

        # 方法3: 直接统计所有独立的数字行（作为后备方案）
        if not episodes_found:
            standalone_numbers = re.findall(r'^(\d+)$', original_script_content, re.MULTILINE)
            # 过滤掉可能是页码或其他数字的行（通常是连续的数字，如1,2,3...）
            if standalone_numbers:
                # 去重并排序
                unique_numbers = sorted(set([int(n) for n in standalone_numbers]))
                # 如果有连续的数字序列（1,2,3...），取最大的
                if len(unique_numbers) > 1:
                    episodes_found = unique_numbers

        if episodes_found:
            episode_count = max(episodes_found)  # 取最大的集数

    # 如果检测失败，至少设置为默认值20
    if episode_count == 0:
        episode_count = 20

    prompt = f"""⚠️⚠️⚠️ 重要：原剧本共有 {episode_count} 集，改进后的剧本必须是 {episode_count} 集 ⚠️⚠️⚠️

请根据以下评测建议，改进剧本《{script_name}》。

## 🔴 核心要求（必须严格遵守，不可违反）

1. **集数必须完全一致** - 原剧本共有 {episode_count} 集，改进后的剧本也必须是 {episode_count} 集，不能增加或减少任何一集
2. **保持原剧本格式** - 完全按照原剧本的格式结构输出，包括以下所有部分：
   - 剧本名称
   - 剧本风格
   - 故事概要
   - 人物设定（包含所有角色的外貌特征和功能）
   - 剧情大纲（opening/development/climax/ending）
   - 分集剧本（{episode_count} 集，每一集都要包含：时长、场景、影视化画面提示、第一人称旁白、动作/事件、结尾钩子）
3. **基于原剧本改进** - 在原剧本基础上进行针对性修改，不要重新创作
4. **保持原剧本风格** - 保留原有的语言风格、叙事节奏、人物设定等

## 📋 剧本格式模板

请严格按照以下格式输出改进后的剧本：

```
剧本名称
剧本风格：[风格1], [风格2], [风格3], ...
故事概要：[概要内容]

人物设定
[角色名]（[身份]） - [性格特征1]、[性格特征2]
外貌特征：[外貌描述]
功能：[角色功能]

[角色名]（[身份]） - [性格特征1]、[性格特征2]
外貌特征：[外貌描述]
功能：[角色功能]

剧情大纲
opening: [开篇内容]
development: [发展内容]
climax: [高潮内容]
ending: [结局内容]

分集剧本
1
【时长】：[秒数]
【场景】：[时间] [地点] [氛围描述]
【影视化画面提示】：[画面描述]
【第一人称旁白(OS)】：[旁白内容]
【动作 / 事件】：[动作描述]
【结尾钩子】：[钩子内容]

2
【时长】：[秒数]
【场景】：[时间] [地点] [氛围描述]
【影视化画面提示】：[画面描述]
【第一人称旁白(OS)】：[旁白内容]
【动作 / 事件】：[动作描述]
【结尾钩子】：[钩子内容]

3
【时长】：[秒数]
【场景】：[时间] [地点] [氛围描述]
【影视化画面提示】：[画面描述]
【第一人称旁白(OS)】：[旁白内容]
【动作 / 事件】：[动作描述]
【结尾钩子】：[钩子内容]

...（必须一直写到第 {episode_count} 集，不能省略任何一集）
```

## 原剧本完整内容

```
{original_script_content}
```

## 修改建议

"""

    # 添加各维度的修改建议
    for dim_key, dim_data in suggestions.items():
        dimension_name = dim_data.get('dimension_name', dim_key)
        dim_suggestions = dim_data.get('suggestions', [])

        if dim_suggestions:
            prompt += f"\n### {dimension_name}\n\n"
            for i, suggestion in enumerate(dim_suggestions, 1):
                prompt += f"{i}. {suggestion}\n"
            prompt += "\n"

    # 添加原剧本的总体信息（如果有的话）
    if evaluation_result.get('overall'):
        overall = evaluation_result['overall']
        prompt += f"\n## 原剧本评测概要\n\n"
        prompt += f"- 总分：{overall.get('total_score', 0)}/{overall.get('max_score', 100)}\n"
        prompt += f"- 等级：{overall.get('grade', 'N/A')}\n\n"

    prompt += f"""

## 📋 输出要求（必须严格遵守，不可违反）

请严格按照上面的【剧本格式模板】输出完整的改进后剧本：

1. **完整集数**：必须输出完整的 {episode_count} 集内容，从第1集到第{episode_count}集，不能省略任何一集
2. **格式完全一致**：严格按照格式模板，包含以下所有部分：
   - 剧本名称、剧本风格、故事概要
   - 人物设定（每个角色包含：角色名、身份、性格、外貌特征、功能）
   - 剧情大纲（包含 opening、development、climax、ending 四个部分）
   - 分集剧本（必须输出 {episode_count} 集，每集包含：时长、场景、影视化画面提示、第一人称旁白、动作/事件、结尾钩子）
3. **保持原剧本结构**：每集标题为数字"1"、"2"、"3"等，与原剧本格式完全一致
4. **针对性改进**：根据修改建议对相应内容进行改进，但保持整体结构不变
5. **输出顺序**：剧本名称 → 剧本风格 → 故事概要 → 人物设定 → 剧情大纲 → 分集剧本

🚨🚨🚨 超级重要（违反将被视为失败）🚨🚨🚨：

1. **集数必须准确**：必须是 {episode_count} 集，不能是 {episode_count - 1} 集、{episode_count - 2} 集或 {episode_count + 1} 集
2. **每集必须完整**：每一集都必须包含完整的6个要素（时长、场景、影视化画面提示、第一人称旁白、动作/事件、结尾钩子）
3. **不要省略中间集数**：如果原剧本有{episode_count}集，就不要输出"1...10"然后跳到"{episode_count}"，必须输出1到{episode_count}每一集
4. **格式符号一致**：【时长】：、【场景】：、【第一人称旁白(OS)】：、【动作 / 事件】：、【结尾钩子】：

示例：如果原剧本是{episode_count}集，你的输出必须包含：
1
【时长】：...
2
【时长】：...
3
【时长】：...
...
{episode_count}
【时长】：...

请直接输出改进后的剧本内容，不要添加任何额外的解释说明或开场白。"""

    return prompt


# ==================== 历史记录 API ====================

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取评测历史记录列表"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', None)

        result = history_manager.get_records(limit=limit, offset=offset, search=search)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/<record_id>', methods=['GET'])
def get_history_record(record_id):
    """获取单个历史记录详情"""
    try:
        load_full = request.args.get('full', 'false').lower() == 'true'
        record = history_manager.get_record(record_id, load_full=load_full)

        if record is None:
            return jsonify({
                'success': False,
                'error': '记录不存在'
            }), 404

        return jsonify({
            'success': True,
            'record': record
        })

    except Exception as e:
        logger.error(f"获取历史记录详情失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/<record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    """删除历史记录"""
    try:
        success = history_manager.delete_record(record_id)

        if not success:
            return jsonify({
                'success': False,
                'error': '记录不存在或删除失败'
            }), 404

        return jsonify({
            'success': True,
            'message': '删除成功'
        })

    except Exception as e:
        logger.error(f"删除历史记录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """清空所有历史记录"""
    try:
        success = history_manager.clear_all()

        if not success:
            return jsonify({
                'success': False,
                'error': '清空失败'
            }), 500

        return jsonify({
            'success': True,
            'message': '历史记录已清空'
        })

    except Exception as e:
        logger.error(f"清空历史记录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/statistics', methods=['GET'])
def get_history_statistics():
    """获取历史记录统计信息"""
    try:
        stats = history_manager.get_statistics()

        return jsonify({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/history/import', methods=['POST'])
def import_history():
    """从outputs目录导入历史评测记录"""
    try:
        result = history_manager.import_from_outputs()

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"导入历史记录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI 剧本评测系统 Web 服务')
    parser.add_argument('--port', '-p', type=int, default=None, help='指定端口号（默认自动查找可用端口）')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式')
    args = parser.parse_args()

    # 默认端口列表（按优先级）
    default_ports = [5000, 5001, 5002, 8000, 8001, 8080, 3000]

    if args.port:
        port = args.port
        app.run(debug=args.debug, host='0.0.0.0', port=port)
    else:
        # 自动查找可用端口
        import socket

        for try_port in default_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', try_port)) != 0:
                    port = try_port
                    print(f"\n🚀 启动 Web 服务")
                    print(f"📍 访问地址: http://localhost:{port}")
                    print(f"📝 按 Ctrl+C 停止服务\n")
                    app.run(debug=args.debug, host='0.0.0.0', port=port)
                    break
        else:
            print("❌ 无法找到可用端口，请使用 --port 参数手动指定")
            print(f"   示例: python app.py --port 9999")
