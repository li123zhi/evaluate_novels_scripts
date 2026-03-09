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

            # 对于长篇小说，需要增加max_tokens
            # 20章 * 每章1000字 = 20000字，大约需要30000-40000 tokens
            # 但豆包API有最大限制，我们设置为8000
            # 注意：由于token限制，可能无法一次生成完整的20章，这是正常的
            logger.info("使用高token限制生成小说（max_tokens=8000）")

            # 临时修改客户端的max_tokens
            original_max_tokens = self.ai_client.max_tokens
            self.ai_client.max_tokens = 8000

            try:
                # 调用AI生成
                response = self.ai_client.chat(
                    prompt=prompt,
                    system_prompt="你是一位专业的网络小说作家，擅长创作各种类型的小说。请务必尽可能生成完整的内容，包含尽可能多的章节。"
                )

                # 解析响应
                result = self._parse_generation_response(response, params)

                logger.info(f"小说生成成功，共{len(result.get('chapters', []))}章")
                return result
            finally:
                # 恢复原始max_tokens
                self.ai_client.max_tokens = original_max_tokens

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
        import re

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
            # 如果不是JSON，尝试从文本中提取标题
            title = params.get('title')

            if not title:
                # 尝试从响应中提取标题
                patterns = [
                    r'(?:标题|title|小说名|书名)[：:]\s*([^\n]+)',
                    r'^#\s+([^\n]+)',
                    r'^\*\*([^\*]+)\*\*',
                    r'《([^》]+)》',
                ]

                for pattern in patterns:
                    match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
                    if match:
                        extracted_title = match.group(1).strip()
                        if len(extracted_title) < 50:
                            title = extracted_title
                            break

            # 如果还是找不到，使用通用默认值
            if not title:
                title = '未命名小说'

            return {
                'success': True,
                'title': title,
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

    def generate_outline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整模式第1步：生成故事大纲和章节规划

        Args:
            params: 生成参数

        Returns:
            大纲结果
        """
        logger.info(f"开始生成大纲，题材：{params.get('genre')}")

        try:
            # 读取大纲生成prompt模板
            prompt_file = self.prompts_dir / "generate_outline.txt"
            if not prompt_file.exists():
                # 如果没有专门的模板，使用主模板的简化版
                prompt_file = self.prompts_dir / "generate_novel.txt"

            prompt_template = prompt_file.read_text(encoding='utf-8')

            # 构建prompt
            prompt = self._build_generation_prompt(prompt_template, params)

            # 调用AI生成大纲
            response = self.ai_client.chat(
                prompt=prompt + "\n\n请先输出完整的故事大纲和章节规划，不需要详细内容。",
                system_prompt="你是一位专业的网络小说作家，擅长创作各种类型的小说。"
            )

            # 解析大纲
            outline_data = self._parse_outline_response(response, params)

            logger.info("大纲生成成功")
            return {
                'success': True,
                **outline_data
            }

        except Exception as e:
            logger.error(f"生成大纲失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_all_chapters(self, outline: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整模式第3步：分批生成所有章节

        Args:
            outline: 大纲数据
            params: 生成参数

        Returns:
            完整小说数据
        """
        try:
            total_chapters = params.get('chapters', 20)
            batch_size = 3  # 每批生成3章（降低超时风险，提高成功率）
            all_chapters = []

            # 从大纲中提取章节规划
            chapter_plan = outline.get('chapter_plan', [])
            if not chapter_plan:
                # 如果大纲没有章节规划，根据章节数创建规划
                chapter_plan = [
                    f"第{i+1}章" for i in range(total_chapters)
                ]

            total_batches = (len(chapter_plan) + batch_size - 1) // batch_size

            logger.info(f"开始分批生成章节，总计{len(chapter_plan)}章，分{total_batches}批")

            failed_batches = []  # 记录失败的批次

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(chapter_plan))
                current_batch = batch_idx + 1

                logger.info(f"生成第{current_batch}/{total_batches}批章节（第{start_idx+1}-{end_idx}章）")

                try:
                    # 准备这批章节的prompt
                    batch_prompt = self._build_batch_prompt(outline, chapter_plan, start_idx, end_idx, params)

                    # 调用AI生成这批章节
                    response = self.ai_client.chat(
                        prompt=batch_prompt,
                        system_prompt="你是一位专业的网络小说作家。请严格按照JSON格式输出章节内容，必须返回有效的JSON对象。",
                        json_mode=True
                    )

                    logger.info(f"AI响应长度: {len(response)} 字符")
                    logger.info(f"AI响应前500字符: {response[:500]}")

                    # 解析这批章节
                    batch_chapters = self._parse_batch_chapters(response, start_idx)

                    if not batch_chapters:
                        logger.warning(f"第{current_batch}批未解析到任何章节，可能需要重试")
                        failed_batches.append(current_batch)
                    else:
                        all_chapters.extend(batch_chapters)
                        logger.info(f"第{current_batch}批完成，生成了{len(batch_chapters)}章，总计{len(all_chapters)}章")

                except Exception as e:
                    logger.error(f"第{current_batch}批生成失败: {str(e)}")
                    failed_batches.append(current_batch)
                    # 继续生成下一批，不中断整个流程
                    continue

            # 检查是否所有批次都失败
            if not all_chapters:
                raise Exception("所有批次都生成失败，请检查API配置或稍后重试")

            # 组装完整小说
            result = {
                'success': True,
                'title': outline.get('title', '未命名小说'),
                'genre': outline.get('genre', params.get('genre', '')),
                'outline': outline.get('outline', ''),
                'characters': outline.get('characters', []),
                'chapters': all_chapters,
                'total_word_count': sum(len(ch.get('content', '')) for ch in all_chapters),
                'themes': outline.get('themes', []),
                'target_audience': outline.get('target_audience', params.get('target_audience', '')),
                'partial_success': len(failed_batches) > 0,
                'failed_batches': failed_batches,
                'total_chapters_requested': len(chapter_plan),
                'total_chapters_generated': len(all_chapters)
            }

            if failed_batches:
                logger.warning(f"小说部分生成完成：成功{len(all_chapters)}章，失败批次：{failed_batches}")
            else:
                logger.info(f"完整小说生成成功，共{len(all_chapters)}章")

            return result

        except Exception as e:
            logger.error(f"分批生成章节失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_outline_response(self, response: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """解析大纲响应"""
        import re

        # 尝试从响应中提取title
        title = None

        # 1. 尝试解析JSON格式
        try:
            data = json.loads(response)
            title = data.get('title')
            if not title:
                title = data.get('novel_name')
                if not title:
                    title = data.get('name')
        except json.JSONDecodeError:
            pass

        # 2. 如果JSON解析失败，尝试从文本中提取标题
        if not title:
            # 匹配 "标题：" 或 "title:" 或 "小说名：" 等
            patterns = [
                r'(?:标题|title|小说名|书名)[：:]\s*([^\n]+)',
                r'^#\s+([^\n]+)',  # markdown标题
                r'^\*\*([^\*]+)\*\*',  # 加粗的标题
                r'《([^》]+)》',  # 书名号
            ]

            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
                if match:
                    extracted_title = match.group(1).strip()
                    if len(extracted_title) < 50:  # 标题不应该太长
                        title = extracted_title
                        break

        # 3. 如果还是找不到，使用默认值（但避免"都市故事"这种格式）
        if not title:
            title = params.get('title') or '未命名小说'

        # 提取大纲内容
        outline = response[:2000] if len(response) > 2000 else response

        # 尝试提取章节规划
        chapter_plan = []
        chapter_matches = re.findall(r'(?:第[一二三四五六七八九十\d]+章|Chapter\s+\d+)[：:]?\s*([^\n]+)', response)
        if chapter_matches:
            chapter_plan = [f"第{i+1}章 {match.strip()}" for i, match in enumerate(chapter_matches[:20])]  # 最多20章

        logger.info(f"解析大纲完成，标题: {title}, 章节数: {len(chapter_plan)}")

        return {
            'title': title,
            'genre': params.get('genre', ''),
            'outline': outline,
            'chapter_plan': chapter_plan,
            'characters': params.get('characters', []),
            'themes': [params.get('theme', '成长与爱情')],
            'target_audience': params.get('target_audience', '年轻读者')
        }

    def _build_batch_prompt(self, outline: Dict[str, Any], chapter_plan: List[str],
                           start_idx: int, end_idx: int, params: Dict[str, Any]) -> str:
        """构建分批生成prompt"""
        prompt_parts = []

        # 判断是否是最后一批
        is_last_batch = end_idx >= len(chapter_plan)
        total_chapters = len(chapter_plan)

        prompt_parts.append(f"请根据以下大纲生成第{start_idx+1}到第{end_idx}章的完整内容。\n\n")
        prompt_parts.append(f"小说标题：{outline.get('title', '未命名')}\n")
        prompt_parts.append(f"题材：{outline.get('genre', params.get('genre', ''))}\n")
        prompt_parts.append(f"风格：{params.get('style', '轻松')}\n")
        prompt_parts.append(f"总章节数：{total_chapters}章\n")
        prompt_parts.append(f"当前批次：第{start_idx+1}-{end_idx}章\n\n")

        prompt_parts.append("故事大纲：\n")
        prompt_parts.append(outline.get('outline', '')[:800])  # 增加大纲长度
        prompt_parts.append("\n\n")

        prompt_parts.append("章节规划：\n")
        for i in range(start_idx, end_idx):
            if i < len(chapter_plan):
                prompt_parts.append(f"- {chapter_plan[i]}\n")

        prompt_parts.append("\n\n请严格按照以下JSON格式输出（不要包含其他文字，只要纯JSON）：\n")
        prompt_parts.append('''{
  "chapters": [
    {
      "chapter_number": 章号,
      "title": "章节标题",
      "content": "章节完整内容（至少1500字）"
    }
  ]
}
''')

        prompt_parts.append("\n要求：\n")
        prompt_parts.append("- ⚠️ 每章至少1500字，必须包含完整的起承转合\n")
        prompt_parts.append("- 每章要有明确的开端、发展、高潮、结尾\n")
        prompt_parts.append("- 确保章节之间情节连贯，不脱节\n")

        if is_last_batch:
            prompt_parts.append("- ⭐ 最后一批章节，必须给出完整结局\n")
            prompt_parts.append("- ⭐ 所有情节线必须有收尾\n")
            prompt_parts.append("- ⭐ 主角的命运要有明确交代\n")
            prompt_parts.append("- ⭐ 给读者一个满意的结局\n")
        else:
            prompt_parts.append("- 非最后章节，结尾要留下悬念或钩子\n")

        prompt_parts.append("- 务必生成所有要求章节，不能遗漏\n")
        prompt_parts.append("- 内容要充实，不要水字数\n")

        return ''.join(prompt_parts)

    def _parse_batch_chapters(self, response: str, start_idx: int) -> List[Dict[str, Any]]:
        """解析批次章节响应"""
        try:
            # 尝试解析JSON
            data = json.loads(response)
            return data.get('chapters', [])
        except json.JSONDecodeError:
            # 如果不是JSON，尝试提取文本内容
            logger.warning("响应不是JSON格式，尝试从文本中提取章节")

            # 尝试从文本中提取章节
            return self._extract_chapters_from_text(response, start_idx)

    def _extract_chapters_from_text(self, text: str, start_idx: int) -> List[Dict[str, Any]]:
        """从文本中提取章节"""
        chapters = []

        # 尝试多种章节分隔模式
        import re

        # 模式1: "第1章" 或 "第一章"
        pattern1 = r'第(\d+)章[：:\s]*(.*?)(?=\n|$)'
        # 模式2: "Chapter 1" 或 "chapter 1"
        pattern2 = r'[Cc]hapter\s+(\d+)[：:\s]*(.*?)(?=\n|$)'
        # 模式3: "## " markdown标题
        pattern3 = r'##+\s*(第?\d*[章]*.*?)(?=\n|$)'

        # 使用模式1进行分割
        sections = re.split(f'第{start_idx + 1}章|第{start_idx + 2}章|第{start_idx + 3}章|第{start_idx + 4}章|第{start_idx + 5}章', text)

        # 如果分割成功，提取章节
        if len(sections) > 1:
            current_idx = start_idx
            for i, section in enumerate(sections[1:], 1):  # 跳过第一个（可能是序言）
                if not section.strip():
                    continue

                # 提取标题（第一行）
                lines = section.strip().split('\n')
                title = lines[0].strip() if lines else f'第{current_idx}章'
                content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else section.strip()

                if content and len(content) > 50:  # 至少50个字符
                    chapters.append({
                        'chapter_number': current_idx,
                        'title': title,
                        'content': content
                    })
                    current_idx += 1

        # 如果上述方法失败，尝试按markdown标题分割
        if not chapters:
            lines = text.split('\n')
            current_chapter = None
            current_content = []

            for line in lines:
                # 检查是否是章节标题行
                if re.match(r'^#+\s*第?\d+[章]|^第?\d+[章]', line):
                    # 保存上一章
                    if current_chapter and current_content:
                        chapters.append({
                            'chapter_number': current_chapter,
                            'title': current_title,
                            'content': '\n'.join(current_content).strip()
                        })

                    # 开始新章节
                    match = re.search(r'(\d+)', line)
                    if match:
                        current_chapter = int(match.group(1))
                    else:
                        current_chapter = start_idx + len(chapters) + 1
                    current_title = line.strip('# ').strip()
                    current_content = []
                else:
                    if current_chapter is not None:
                        current_content.append(line)

            # 保存最后一章
            if current_chapter and current_content:
                chapters.append({
                    'chapter_number': current_chapter,
                    'title': current_title,
                    'content': '\n'.join(current_content).strip()
                })

        # 如果还是失败，将整个文本作为一章
        if not chapters and len(text.strip()) > 100:
            chapters.append({
                'chapter_number': start_idx + 1,
                'title': f'第{start_idx + 1}章',
                'content': text.strip()
            })

        logger.info(f"从文本中提取了{len(chapters)}个章节")
        return chapters

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

    def evaluate_novel(self, novel_content: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        评测小说质量

        Args:
            novel_content: 小说内容
            params: 评测参数（可选）

        Returns:
            评测结果
        """
        logger.info("开始评测小说")

        try:
            # 读取prompt模板
            prompt_file = self.prompts_dir / "novel_evaluation.txt"
            if not prompt_file.exists():
                prompt_file = self.prompts_dir / "novel_evaluation.md"

            prompt_template = prompt_file.read_text(encoding='utf-8')

            # 构建prompt
            prompt = prompt_template.replace('{novel_content}', novel_content[:10000])  # 限制长度避免token过多

            # 调用AI评测
            response = self.ai_client.chat(
                prompt=prompt,
                system_prompt="你是一位专业的网络小说编辑和评论家，擅长评估小说质量。",
                response_format="json"
            )

            # 解析响应
            result = json.loads(response) if isinstance(response, str) else response

            logger.info(f"小说评测完成，总分: {result.get('total_score', 0)}")
            return {
                'success': True,
                'evaluation': result
            }

        except Exception as e:
            logger.error(f"小说评测失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def continue_failed_batches(self, outline: Dict[str, Any], params: Dict[str, Any],
                                 existing_chapters: List[Dict[str, Any]],
                                 failed_batches: List[int]) -> Dict[str, Any]:
        """
        继续生成失败的批次

        Args:
            outline: 大纲数据
            params: 生成参数
            existing_chapters: 已生成的章节
            failed_batches: 失败的批次列表（从1开始）

        Returns:
            完整小说数据
        """
        try:
            batch_size = 3
            chapter_plan = outline.get('chapter_plan', [])
            total_chapters = len(chapter_plan)

            logger.info(f"继续生成失败的批次：{failed_batches}，总计{total_chapters}章")

            new_failed_batches = []

            for batch_num in failed_batches:
                start_idx = (batch_num - 1) * batch_size
                end_idx = min(start_idx + batch_size, total_chapters)

                logger.info(f"重新生成第{batch_num}批章节（第{start_idx+1}-{end_idx}章）")

                try:
                    # 准备这批章节的prompt
                    batch_prompt = self._build_batch_prompt(outline, chapter_plan, start_idx, end_idx, params)

                    # 调用AI生成这批章节
                    response = self.ai_client.chat(
                        prompt=batch_prompt,
                        system_prompt="你是一位专业的网络小说作家。请严格按照JSON格式输出章节内容，必须返回有效的JSON对象。",
                        json_mode=True
                    )

                    logger.info(f"AI响应长度: {len(response)} 字符")

                    # 解析这批章节
                    batch_chapters = self._parse_batch_chapters(response, start_idx)

                    if not batch_chapters:
                        logger.warning(f"第{batch_num}批未解析到任何章节")
                        new_failed_batches.append(batch_num)
                    else:
                        existing_chapters.extend(batch_chapters)
                        logger.info(f"第{batch_num}批完成，生成了{len(batch_chapters)}章")

                except Exception as e:
                    logger.error(f"第{batch_num}批生成失败: {str(e)}")
                    new_failed_batches.append(batch_num)
                    continue

            # 检查是否所有批次都失败
            if not existing_chapters:
                raise Exception("所有批次都生成失败，请检查API配置或稍后重试")

            # 组装完整小说
            # 按章节号排序
            existing_chapters.sort(key=lambda x: x.get('chapter_number', 0))

            result = {
                'success': True,
                'title': outline.get('title', '未命名小说'),
                'genre': outline.get('genre', params.get('genre', '')),
                'outline': outline.get('outline', ''),
                'characters': outline.get('characters', []),
                'chapters': existing_chapters,
                'total_word_count': sum(len(ch.get('content', '')) for ch in existing_chapters),
                'themes': outline.get('themes', []),
                'target_audience': outline.get('target_audience', params.get('target_audience', '')),
                'partial_success': len(new_failed_batches) > 0,
                'failed_batches': new_failed_batches,
                'total_chapters_requested': total_chapters,
                'total_chapters_generated': len(existing_chapters),
                'chapter_plan': chapter_plan
            }

            if new_failed_batches:
                logger.warning(f"继续生成部分完成：成功{len(existing_chapters)}章，仍失败批次：{new_failed_batches}")
            else:
                logger.info(f"继续生成成功，共{len(existing_chapters)}章")

            return result

        except Exception as e:
            logger.error(f"继续生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
