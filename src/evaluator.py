"""
剧本评测器
核心评测逻辑，调用 API 对剧本进行多维度评测
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm

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

        # 截断过长的剧本
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[内容过长，已截断...]"

        return content

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

        try:
            result = self.api_client.chat_with_json_response(prompt)
            # 验证返回结果是否为字典
            if not isinstance(result, dict):
                raise ValueError(f"API 返回结果不是字典类型，而是 {type(result).__name__}: {result}")
            return result
        except Exception as e:
            print(f"评测维度 {dimension} 时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
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
        # 确定要评测的维度
        if dimensions is None:
            dimensions = list(self.dimensions.keys())

        # 准备剧本内容
        script_content = self._prepare_script_content(script_path)

        # 获取剧本信息
        script_name = Path(script_path).stem

        result = {
            "script_name": script_name,
            "script_path": script_path,
            "dimensions": {}
        }

        # 评测各个维度
        dimension_iter = dimensions
        if show_progress:
            dimension_iter = tqdm(dimensions, desc="评测进度")

        for dimension in dimension_iter:
            dimension_result = self._evaluate_dimension(dimension, script_content)
            result["dimensions"][dimension] = dimension_result

        # 计算综合评分
        result["overall"] = self._calculate_overall_score(result["dimensions"])

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
