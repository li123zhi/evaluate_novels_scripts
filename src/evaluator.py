"""
剧本评测器
核心评测逻辑，调用 API 对剧本进行多维度评测
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .api_client import DoubaoAPIClient


class ScriptEvaluator:
    """剧本评测器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化评测器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 初始化 API 客户端
        self.api_client = DoubaoAPIClient()

        # 获取评测维度配置
        self.dimensions = self.config.get('evaluation_dimensions', {})

        # 获取提示词模板目录
        self.prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

    def _load_prompt(self, dimension: str) -> str:
        """
        加载指定维度的提示词模板

        Args:
            dimension: 维度名称

        Returns:
            提示词模板内容
        """
        prompt_file = self.dimensions[dimension].get('prompt_file')
        if not prompt_file:
            raise ValueError(f"维度 {dimension} 没有配置提示词文件")

        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), prompt_file)

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _prepare_script_content(self, script_path: str, max_length: int = 50000) -> str:
        """
        读取并准备剧本内容

        Args:
            script_path: 剧本文件路径
            max_length: 最大字符数

        Returns:
            剧本内容
        """
        # 尝试多种编码读取文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        content = None

        for encoding in encodings:
            try:
                with open(script_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        # 如果所有编码都失败，使用 errors='ignore'
        if content is None:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        # 预处理剧本内容
        content = self._preprocess_script(content)

        # 截断过长的剧本
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[内容过长，已截断...]"

        return content

    def _preprocess_script(self, content: str) -> str:
        """
        预处理剧本内容，优化格式

        Args:
            content: 原始剧本内容

        Returns:
            处理后的剧本内容
        """
        import re

        # 1. 移除 BOM 标记
        content = content.replace('\ufeff', '')

        # 2. 统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 3. 移除全角空格
        content = content.replace('\u3000', ' ')

        # 4. 移除连续的空行（保留最多一个空行）
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # 5. 智能识别剧本格式并添加结构化标记
        script_info = self._analyze_script_structure(content)

        # 如果识别为短剧剧本，添加格式说明
        if script_info['is_short_drama']:
            # 在开头添加结构说明，帮助 AI 更好理解
            header = f"""# 短剧剧本结构分析

标题：{script_info.get('title', '未知')}
总集数：{script_info.get('total_episodes', '未知')}
人物数量：{script_info.get('character_count', '未知')}

包含部分：
"""
            if script_info.get('has_style'):
                header += "- 剧本风格设定\n"
            if script_info.get('has_summary'):
                header += "- 故事概要\n"
            if script_info.get('has_characters'):
                header += "- 人物设定\n"
            if script_info.get('has_plot_outline'):
                header += "- 剧情大纲\n"
            if script_info.get('has_episodes'):
                header += "- 分集剧本\n"

            header += f"\n--- 剧本内容 ---\n\n"

            # 只在内容足够长时添加头部（避免影响短剧本）
            if len(content) > 2000:
                content = header + content

        return content.strip()

    def _analyze_script_structure(self, content: str) -> dict:
        """
        分析剧本结构，识别是否为短剧剧本

        Args:
            content: 剧本内容

        Returns:
            结构分析结果字典
        """
        import re

        result = {
            'is_short_drama': False,
            'title': None,
            'total_episodes': 0,
            'character_count': 0,
            'has_style': False,
            'has_summary': False,
            'has_characters': False,
            'has_plot_outline': False,
            'has_episodes': False
        }

        lines = content.split('\n')

        # 1. 检测标题（第一行通常是标题）
        if len(lines) > 0:
            first_line = lines[0].strip()
            if len(first_line) < 50 and not any(char in first_line for char in ['【', '】', ':', '：']):
                result['title'] = first_line

        # 2. 检测剧本风格
        style_patterns = ['剧本风格', '风格', '类型', '改编']
        result['has_style'] = any(any(pattern in line for pattern in style_patterns) for line in lines[:20])

        # 3. 检测故事概要
        summary_patterns = ['故事概要', '剧情简介', '内容简介', '梗概']
        result['has_summary'] = any(any(pattern in line for pattern in summary_patterns) for line in lines[:30])

        # 4. 检测人物设定
        character_patterns = ['人物设定', '角色介绍', '主要人物', '人物小传']
        result['has_characters'] = any(any(pattern in line for pattern in character_patterns) for line in lines[:50])

        # 统计人物数量
        if result['has_characters']:
            # 查找人物设定块
            in_character_section = False
            for line in lines:
                if any(pattern in line for pattern in character_patterns):
                    in_character_section = True
                    continue
                if in_character_section:
                    # 检测人物条目（通常是 - 开头或者名字 - 描述格式）
                    if line.strip() and not line.startswith(' '):
                        if line[0] in '-•●○':
                            result['character_count'] += 1
                        elif ' - ' in line or '——' in line:
                            result['character_count'] += 1
                    # 跳出人物设定块
                    if any(keyword in line for keyword in ['剧情', '分集', 'opening', 'development']):
                        break

        # 5. 检测剧情大纲
        plot_patterns = ['剧情大纲', '故事线', '结构', 'opening', 'development', 'climax', 'ending']
        result['has_plot_outline'] = any(any(pattern in line.lower() for pattern in plot_patterns) for line in lines)

        # 6. 检测分集剧本
        episode_patterns = [
            r'^\d+\s*$',  # 单独的数字（集数）
            r'【时长】',  # 时长标记
            r'【场景】',  # 场景标记
            r'分集剧本',  # 分集剧本标题
            r'^第\d+集'  # 第X集
        ]

        episode_count = 0
        for line in lines:
            if any(re.match(pattern, line.strip()) for pattern in episode_patterns):
                episode_count += 1

        result['has_episodes'] = episode_count > 3
        result['total_episodes'] = episode_count

        # 7. 判断是否为短剧剧本（至少满足3个特征）
        feature_count = sum([
            result['has_style'],
            result['has_summary'],
            result['has_characters'],
            result['has_plot_outline'],
            result['has_episodes']
        ])

        result['is_short_drama'] = feature_count >= 3

        return result

    def _evaluate_dimension(
        self,
        dimension: str,
        script_content: str
    ) -> Dict[str, Any]:
        """
        评测单个维度

        Args:
            dimension: 维度名称
            script_content: 剧本内容

        Returns:
            评测结果
        """
        # 加载提示词模板
        prompt_template = self._load_prompt(dimension)

        # 替换剧本内容
        prompt = prompt_template.replace('{script_content}', script_content)

        # 调用 API
        dimension_name = self.dimensions[dimension].get('name', dimension)
        print(f"\n正在评测维度: {dimension_name}...")

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"开始评测维度: {dimension_name} ({dimension})")

        try:
            result = self.api_client.chat_with_json_response(prompt)
            # 验证返回结果是否为字典
            if not isinstance(result, dict):
                raise ValueError(f"API 返回结果不是字典类型，而是 {type(result).__name__}: {result}")
            logger.info(f"维度 {dimension_name} 评测成功，得分: {result.get('total_score', 0)}")
            return result
        except Exception as e:
            print(f"评测维度 {dimension} 时出错: {str(e)}")
            logger.error(f"评测维度 {dimension} 失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            logger.error(traceback.format_exc())
            # 返回错误结果
            return {
                "dimension": dimension,
                "dimension_name": dimension_name,
                "error": str(e),
                "total_score": 0,
                "max_score": 100
            }

    def evaluate(
        self,
        script_path: str,
        dimensions: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        对剧本进行全面评测

        Args:
            script_path: 剧本文件路径
            dimensions: 要评测的维度列表，None 表示评测所有维度
            show_progress: 是否显示进度条

        Returns:
            完整评测结果
        """
        import logging
        logger = logging.getLogger(__name__)

        # 确定要评测的维度
        if dimensions is None:
            dimensions = list(self.dimensions.keys())

        logger.info(f"开始评测，共 {len(dimensions)} 个维度: {dimensions}")

        # 准备剧本内容
        logger.info("正在准备剧本内容...")
        script_content = self._prepare_script_content(script_path)
        logger.info(f"剧本内容准备完成，长度: {len(script_content)} 字符")

        # 获取剧本信息
        script_name = Path(script_path).stem

        result = {
            "script_name": script_name,
            "script_path": script_path,
            "dimensions": {}
        }

        # 使用线程池并发评测各个维度
        logger.info(f"开始并发评测 {len(dimensions)} 个维度...")

        # 创建线程安全的进度条
        if show_progress:
            progress_bar = tqdm(total=len(dimensions), desc="评测进度")
        else:
            progress_bar = None

        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=5) as executor:  # 最多5个并发
            # 提交所有评测任务
            future_to_dimension = {
                executor.submit(self._evaluate_dimension, dimension, script_content): dimension
                for dimension in dimensions
            }

            # 收集结果
            for future in as_completed(future_to_dimension):
                dimension = future_to_dimension[future]
                try:
                    dimension_result = future.result()
                    result["dimensions"][dimension] = dimension_result
                    logger.info(f"维度 {dimension} 评测完成，得分: {dimension_result.get('total_score', 0)}")
                except Exception as e:
                    logger.error(f"维度 {dimension} 评测失败: {str(e)}")
                    result["dimensions"][dimension] = {
                        "dimension": dimension,
                        "dimension_name": self.dimensions.get(dimension, {}).get('name', dimension),
                        "error": str(e),
                        "total_score": 0,
                        "max_score": 100
                    }

                if progress_bar:
                    progress_bar.update(1)

        if progress_bar:
            progress_bar.close()

        # 计算综合评分
        logger.info("正在计算综合评分...")
        result["overall"] = self._calculate_overall_score(result["dimensions"])
        logger.info(f"评测全部完成，总分: {result['overall'].get('total_score', 0)}")

        return result

    def _calculate_overall_score(
        self,
        dimension_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算综合评分

        Args:
            dimension_results: 各维度评测结果

        Returns:
            综合评分信息
        """
        total_weighted_score = 0
        total_weight = 0
        details = []

        for dimension, result in dimension_results.items():
            if "error" in result:
                continue

            weight = self.dimensions.get(dimension, {}).get('weight', 0)
            score = result.get('total_score', 0)
            max_score = result.get('max_score', 100)
            dimension_name = result.get('dimension_name', dimension)

            weighted_score = (score / max_score) * weight * 100

            total_weighted_score += weighted_score
            total_weight += weight

            details.append({
                "dimension": dimension_name,
                "score": score,
                "max_score": max_score,
                "weight": weight,
                "weighted_score": weighted_score
            })

        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0

        return {
            "total_score": round(overall_score, 2),
            "max_score": 100,
            "details": details,
            "grade": self._get_grade(overall_score)
        }

    def _get_grade(self, score: float) -> str:
        """
        根据分数获取等级

        Args:
            score: 分数

        Returns:
            等级 (S/A/B/C/D)
        """
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"

    def evaluate_batch(
        self,
        script_paths: List[str],
        dimensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量评测多个剧本

        Args:
            script_paths: 剧本文件路径列表
            dimensions: 要评测的维度列表

        Returns:
            评测结果列表
        """
        results = []

        for script_path in tqdm(script_paths, desc="批量评测"):
            result = self.evaluate(script_path, dimensions, show_progress=False)
            results.append(result)

        return results
