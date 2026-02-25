"""
评测报告生成器
将评测结果生成 Markdown 和 JSON 格式的报告
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class ReportGenerator:
    """评测报告生成器"""

    def __init__(self, output_dir: str = None):
        """
        初始化报告生成器

        Args:
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, evaluation_result: Dict[str, Any], formats: List[str] = None) -> str:
        """
        生成评测报告

        Args:
            evaluation_result: 评测结果
            formats: 输出格式列表 ["markdown", "json"]

        Returns:
            生成的文件路径
        """
        if formats is None:
            formats = ["markdown"]

        script_name = evaluation_result.get("script_name", "unnamed")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        generated_files = []

        if "markdown" in formats:
            md_path = self._generate_markdown(evaluation_result, script_name, timestamp)
            generated_files.append(md_path)

        if "json" in formats:
            json_path = self._generate_json(evaluation_result, script_name, timestamp)
            generated_files.append(json_path)

        return generated_files

    def _generate_markdown(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """
        生成 Markdown 格式报告

        Args:
            result: 评测结果
            script_name: 剧本名称
            timestamp: 时间戳

        Returns:
            生成的文件路径
        """
        filename = f"{script_name}_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            # 标题
            overall = result.get("overall", {})
            f.write(f"# 《{script_name}》剧本评测报告\n\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 综合评分
            f.write("## 综合评分\n\n")
            score = overall.get("total_score", 0)
            grade = overall.get("grade", "N/A")
            f.write(f"### {score}/100  |  等级: **{grade}**\n\n")

            # 分项评分表
            f.write("## 分项评分\n\n")
            f.write("| 维度 | 得分 | 满分 | 权重 | 加权得分 |\n")
            f.write("|------|------|------|------|----------|\n")

            for detail in overall.get("details", []):
                dim = detail.get("dimension", "")
                score = detail.get("score", 0)
                max_score = detail.get("max_score", 100)
                weight = detail.get("weight", 0)
                weighted = detail.get("weighted_score", 0)
                f.write(f"| {dim} | {score} | {max_score} | {weight*100:.0f}% | {weighted:.2f} |\n")

            f.write("\n")

            # 各维度详细分析
            f.write("## 详细分析\n\n")

            for dim_key, dim_result in result.get("dimensions", {}).items():
                if "error" in dim_result:
                    f.write(f"### {dim_result.get('dimension_name', dim_key)}\n\n")
                    f.write(f"❌ 评测失败: {dim_result['error']}\n\n")
                    continue

                f.write(f"### {dim_result.get('dimension_name', dim_key)}\n\n")
                f.write(f"**得分**: {dim_result.get('total_score', 0)}/{dim_result.get('max_score', 100)}\n\n")

                # 子项得分
                sub_scores = dim_result.get('sub_scores', {})
                if sub_scores:
                    f.write("#### 子项评分\n\n")
                    f.write("| 项目 | 得分 | 满分 |\n")
                    f.write("|------|------|------|\n")
                    for sub_key, sub_value in sub_scores.items():
                        name = sub_value.get("name", sub_key)
                        score = sub_value.get("score", 0)
                        max_score = sub_value.get("max_score", 100)
                        comment = sub_value.get("comment", "")
                        f.write(f"| {name} | {score} | {max_score} |\n")
                    f.write("\n")

                # 优点
                strengths = dim_result.get('strengths', [])
                if strengths:
                    f.write("#### 优点\n\n")
                    for strength in strengths:
                        f.write(f"- ✅ {strength}\n")
                    f.write("\n")

                # 待改进点
                weaknesses = dim_result.get('weaknesses', [])
                if weaknesses:
                    f.write("#### 待改进点\n\n")
                    for weakness in weaknesses:
                        f.write(f"- ⚠️ {weakness}\n")
                    f.write("\n")

                # 改进建议
                suggestions = dim_result.get('suggestions', [])
                if suggestions:
                    f.write("#### 改进建议\n\n")
                    for i, suggestion in enumerate(suggestions, 1):
                        f.write(f"{i}. {suggestion}\n")
                    f.write("\n")

                # 特殊内容
                if "notable_lines" in dim_result:
                    f.write("#### 精彩台词\n\n")
                    for line in dim_result["notable_lines"]:
                        f.write(f"> **{line.get('speaker', '')}**: {line.get('line', '')}\n")
                        f.write(f"> \n> *{line.get('reason', '')}*\n\n")

                if "character_analysis" in dim_result:
                    f.write("#### 人物分析\n\n")
                    for char in dim_result["character_analysis"]:
                        f.write(f"**{char.get('character', '')}** ({char.get('role', '')}) - "
                               f"{char.get('score', 0)}/{char.get('max_score', 10)}\n\n")
                        f.write(f"{char.get('analysis', '')}\n\n")

                if "twists_identified" in dim_result:
                    f.write("#### 反转分析\n\n")
                    for twist in dim_result["twists_identified"]:
                        f.write(f"- **{twist.get('position', '')}**: {twist.get('description', '')} "
                               f"({twist.get('effectiveness_score', 0)}/{twist.get('max_score', 10)})\n")
                    f.write("\n")

                if "target_audience" in dim_result:
                    audience = dim_result["target_audience"]
                    f.write("#### 目标受众\n\n")
                    if audience.get("primary"):
                        f.write(f"- **主要受众**: {', '.join(audience['primary'])}\n")
                    if audience.get("age_range"):
                        f.write(f"- **年龄范围**: {audience['age_range']}\n")
                    if audience.get("gender_preference"):
                        f.write(f"- **性别偏好**: {audience['gender_preference']}\n")
                    if audience.get("interest_tags"):
                        f.write(f"- **兴趣标签**: {', '.join(audience['interest_tags'])}\n")
                    f.write("\n")

            # 总结建议
            f.write("## 总结建议\n\n")
            f.write("### 核心优势\n\n")
            all_strengths = []
            for dim_result in result.get("dimensions", {}).values():
                all_strengths.extend(dim_result.get("strengths", []))

            # 去重并限制数量
            unique_strengths = list(dict.fromkeys(all_strengths))[:5]
            for strength in unique_strengths:
                f.write(f"- {strength}\n")
            f.write("\n")

            f.write("### 重点改进方向\n\n")
            all_suggestions = []
            for dim_result in result.get("dimensions", {}).values():
                all_suggestions.extend(dim_result.get("suggestions", []))

            unique_suggestions = list(dict.fromkeys(all_suggestions))[:5]
            for i, suggestion in enumerate(unique_suggestions, 1):
                f.write(f"{i}. {suggestion}\n")
            f.write("\n")

            f.write("---\n")
            f.write("*本报告由 AI 剧本评测系统生成，仅供参考*\n")

        return filepath

    def _generate_json(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """
        生成 JSON 格式报告

        Args:
            result: 评测结果
            script_name: 剧本名称
            timestamp: 时间戳

        Returns:
            生成的文件路径
        """
        filename = f"{script_name}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        # 添加元数据
        result["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "generator": "AI Script Evaluator v1.0",
            "script_name": script_name
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return filepath

    def generate_batch_summary(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        生成批量评测汇总报告

        Args:
            results: 评测结果列表

        Returns:
            生成的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_summary_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 批量评测汇总报告\n\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 评测剧本数量: {len(results)}\n\n")

            # 排行榜
            f.write("## 评测排行榜\n\n")
            f.write("| 排名 | 剧本名称 | 综合得分 | 等级 |\n")
            f.write("|------|----------|----------|------|\n")

            sorted_results = sorted(
                results,
                key=lambda x: x.get("overall", {}).get("total_score", 0),
                reverse=True
            )

            for i, result in enumerate(sorted_results, 1):
                script_name = result.get("script_name", "Unknown")
                score = result.get("overall", {}).get("total_score", 0)
                grade = result.get("overall", {}).get("grade", "N/A")
                f.write(f"| {i} | {script_name} | {score} | {grade} |\n")

            f.write("\n")

            # 统计信息
            f.write("## 统计信息\n\n")
            scores = [r.get("overall", {}).get("total_score", 0) for r in results]
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                f.write(f"- **平均分**: {avg_score:.2f}\n")
                f.write(f"- **最高分**: {max_score} ({sorted_results[0].get('script_name', 'Unknown')})\n")
                f.write(f"- **最低分**: {min_score}\n\n")

            # 等级分布
            grade_count = {}
            for result in results:
                grade = result.get("overall", {}).get("grade", "N/A")
                grade_count[grade] = grade_count.get(grade, 0) + 1

            f.write("### 等级分布\n\n")
            for grade in ["S", "A", "B", "C", "D"]:
                count = grade_count.get(grade, 0)
                bar = "█" * count
                f.write(f"- **{grade}级**: {count} {bar}\n")
            f.write("\n")

        return filepath
