"""
小说生成器模块
支持AI生成小说、评测小说、剧本改小说、AI改进小说
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class NovelGenerator:
    """小说生成器"""

    def __init__(self, ai_client):
        """
        初始化小说生成器

        Args:
            ai_client: AI客户端（Doubao等）
        """
        self.ai_client = ai_client
        self.prompts_dir = Path(__file__).parent.parent / "prompts" / "novel"

    def generate_novel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI生成小说

        Args:
            params: 生成参数
                - genre: 题材（言情、玄幻、都市等）
                - style: 风格（轻松、沉重、幽默等）
                - length: 字数
                - chapters: 章节数
                - outline: 大纲（可选）
                - characters: 人物设定（可选）
                - world_setting: 世界观设定（可选）

        Returns:
            生成结果
        """
        logger.info(f"开始生成小说，题材：{params.get('genre')}, 字数：{params.get('length')}")

        try:
            # 读取prompt模板
            prompt_file = self.prompts_dir / "generate_novel.txt"
            if not prompt_file.exists():
                prompt_file = self.prompts_dir / "generate_novel.md"

            prompt_template = prompt_file.read_text(encoding='utf-8')

            # 构建prompt
            prompt = self._build_generation_prompt(prompt_template, params)

            # 调用AI生成
            response = self.ai_client.chat(
                prompt=prompt,
                system_prompt="你是一位专业的网络小说作家，擅长创作各种类型的小说。"
            )

            # 解析响应
            result = self._parse_generation_response(response, params)

            logger.info(f"小说生成成功，共{len(result.get('chapters', []))}章")
            return result

        except Exception as e:
            logger.error(f"生成小说失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _build_generation_prompt(self, template: str, params: Dict[str, Any]) -> str:
        """构建生成prompt"""
        prompt = template

        # 替换参数
        replacements = {
            '{genre}': params.get('genre', '都市'),
            '{style}': params.get('style', '轻松'),
            '{length}': str(params.get('length', 50000)),
            '{chapters}': str(params.get('chapters', 20)),
            '{outline}': params.get('outline', '无'),
            '{characters}': self._format_characters(params.get('characters', [])),
            '{world_setting}': params.get('world_setting', '无特殊设定'),
            '{target_audience}': params.get('target_audience', '年轻女性读者'),
            '{tone}': params.get('tone', '轻松愉快'),
            '{theme}': params.get('theme', '成长与爱情'),
        }

        for old, new in replacements.items():
            prompt = prompt.replace(old, new)

        return prompt

    def _format_characters(self, characters: List[Dict[str, str]]) -> str:
        """格式化人物设定"""
        if not characters:
            return "无特殊人物设定"

        formatted = []
        for char in characters:
            formatted.append(
                f"- {char.get('name', '未命名')}: {char.get('description', '无描述')}"
            )
        return '\n'.join(formatted)

    def _parse_generation_response(self, response: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI生成响应"""
        # 尝试解析JSON格式
        try:
            data = json.loads(response)
            return {
                'success': True,
                'title': data.get('title', '未命名小说'),
                'chapters': data.get('chapters', []),
                'outline': data.get('outline', ''),
                'characters': data.get('characters', []),
                'metadata': params
            }
        except json.JSONDecodeError:
            # 如果不是JSON，尝试解析为纯文本
            return {
                'success': True,
                'title': params.get('title', f"{params.get('genre', '小说')}"),
                'content': response,
                'metadata': params
            }

    def script_to_novel(self, script_content: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        剧本改写成小说

        Args:
            script_content: 剧本内容
            params: 改写参数
                - style: 改写风格（详实、简洁、文艺等）
                - expand_psychology: 是否扩充心理描写
                - expand_environment: 是否扩充环境描写
                - first_person: 是否使用第一人称

        Returns:
            改写结果
        """
        logger.info("开始剧本改小说")

        try:
            # 读取prompt模板
            prompt_file = self.prompts_dir / "script_to_novel.txt"
            if not prompt_file.exists():
                prompt_file = self.prompts_dir / "script_to_novel.md"

            prompt_template = prompt_file.read_text(encoding='utf-8')

            # 构建prompt
            prompt = prompt_template.replace('{script_content}', script_content)
            prompt = prompt.replace('{style}', params.get('style', '详实'))
            prompt = prompt.replace('{expand_psychology}', str(params.get('expand_psychology', True)))
            prompt = prompt.replace('{expand_environment}', str(params.get('expand_environment', True)))
            prompt = prompt.replace('{first_person}', str(params.get('first_person', False)))

            # 调用AI改写
            response = self.ai_client.chat(
                prompt=prompt,
                system_prompt="你是一位专业的小说编辑和作家，擅长将剧本改写成小说。"
            )

            logger.info("剧本改小说完成")
            return {
                'success': True,
                'content': response,
                'metadata': params
            }

        except Exception as e:
            logger.error(f"剧本改小说失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def improve_novel(self, novel_content: str, evaluation_result: Dict[str, Any],
                     improvement_focus: List[str]) -> Dict[str, Any]:
        """
        AI改进小说

        Args:
            novel_content: 小说内容
            evaluation_result: 评测结果
            improvement_focus: 改进重点（如：['人物刻画', '节奏', '对话']）

        Returns:
            改进结果
        """
        logger.info(f"开始AI改进小说，重点：{improvement_focus}")

        try:
            # 读取prompt模板
            prompt_file = self.prompts_dir / "improve_novel.txt"
            if not prompt_file.exists():
                prompt_file = self.prompts_dir / "improve_novel.md"

            prompt_template = prompt_file.read_text(encoding='utf-8')

            # 提取问题维度
            issues = self._extract_issues(evaluation_result, improvement_focus)

            # 构建prompt
            prompt = prompt_template.replace('{novel_content}', novel_content)
            prompt = prompt.replace('{issues}', json.dumps(issues, ensure_ascii=False))
            prompt = prompt.replace('{improvement_focus}', '、'.join(improvement_focus))

            # 调用AI改进
            response = self.ai_client.chat(
                prompt=prompt,
                system_prompt="你是一位专业的小说编辑，擅长改进和优化小说内容。"
            )

            logger.info("AI改进小说完成")
            return {
                'success': True,
                'improved_content': response,
                'focus_areas': improvement_focus,
                'issues_addressed': issues
            }

        except Exception as e:
            logger.error(f"AI改进小说失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_issues(self, evaluation_result: Dict[str, Any],
                       focus_areas: List[str]) -> List[Dict[str, Any]]:
        """从评测结果中提取问题"""
        issues = []

        dimensions = evaluation_result.get('dimensions', {})

        for area in focus_areas:
            # 查找相关维度的问题
            for dim_name, dim_result in dimensions.items():
                if area in dim_result.get('dimension_name', ''):
                    weaknesses = dim_result.get('weaknesses', [])
                    suggestions = dim_result.get('suggestions', [])

                    issues.append({
                        'area': area,
                        'score': dim_result.get('total_score', 0),
                        'weaknesses': weaknesses,
                        'suggestions': suggestions
                    })

        return issues
