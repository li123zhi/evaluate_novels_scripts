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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'outputs')

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

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
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        # 如果都失败，使用 errors='ignore'
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()


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

        # 保存文件
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
        evaluator = ScriptEvaluator()
        result = evaluator.evaluate(actual_script_path, dimensions=dimension_list, show_progress=False)

        # 生成报告
        report_generator = ReportGenerator(output_dir=app.config['OUTPUT_FOLDER'])
        result['script_name'] = filename.rsplit('.', 1)[0]  # 去掉扩展名
        report_files = report_generator.generate(result, formats=['markdown', 'json'])

        # 获取报告文件名（用于下载）
        result['report_files'] = [os.path.basename(f) for f in report_files]

        # 清理上传的临时文件
        try:
            os.remove(script_path)
            if temp_txt_path and os.path.exists(temp_txt_path):
                os.remove(temp_txt_path)
        except:
            pass

        return jsonify({
            'success': True,
            'result': result
        })

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
