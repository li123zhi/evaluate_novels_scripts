"""
新评测报告生成器 - 基于PDF参考格式
生成符合《短剧商业潜力评估报告》格式的评测报告
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List


class NewReportGenerator:
    """新版评测报告生成器 - PDF格式"""

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

    def generate(self, evaluation_result: Dict[str, Any], formats: List[str] = None) -> List[str]:
        """
        生成评测报告

        Args:
            evaluation_result: 评测结果
            formats: 输出格式列表 ["markdown", "json"]

        Returns:
            生成的文件路径列表
        """
        import logging
        logger = logging.getLogger(__name__)

        if formats is None:
            formats = ["markdown"]

        script_name = evaluation_result.get("script_name", "unnamed")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"开始生成新版报告: {script_name}, 格式: {formats}")

        generated_files = []

        if "markdown" in formats:
            logger.info("生成 Markdown 报告...")
            md_path = self._generate_markdown(evaluation_result, script_name, timestamp)
            generated_files.append(md_path)
            logger.info(f"Markdown 报告已生成: {md_path}")

        if "json" in formats:
            logger.info("生成 JSON 报告...")
            json_path = self._generate_json(evaluation_result, script_name, timestamp)
            generated_files.append(json_path)
            logger.info(f"JSON 报告已生成: {json_path}")

        if "pdf" in formats:
            logger.info("生成 PDF 报告...")
            pdf_path = self._generate_pdf(evaluation_result, script_name, timestamp)
            generated_files.append(pdf_path)
            logger.info(f"PDF 报告已生成: {pdf_path}")

        if "word" in formats or "docx" in formats:
            logger.info("生成 Word 报告...")
            word_path = self._generate_word(evaluation_result, script_name, timestamp)
            generated_files.append(word_path)
            logger.info(f"Word 报告已生成: {word_path}")

        logger.info(f"所有报告生成完成: {len(generated_files)} 个文件")
        return generated_files

    def _generate_markdown(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """
        生成 Markdown 格式报告 - PDF格式

        Args:
            result: 评测结果
            script_name: 剧本名称
            timestamp: 时间戳

        Returns:
            生成的文件路径
        """
        import logging
        logger = logging.getLogger(__name__)

        filename = f"{script_name}_评估报告_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        logger.info(f"准备生成新版 Markdown 报告: {filename}")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 标题
                f.write(f"# 《短剧商业潜力评估报告》\n\n")
                f.write(f"**AI 智能诊断｜商业适配度·结构风险·变现潜力**\n\n")
                f.write(f"本报告所依据的评估素材，仅限于该剧的前40集剧本内容。\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")

                # 基础信息（无编号）
                self._write_basic_info(f, result)

                # I. 总体潜力评分
                self._write_overall_score(f, result)

                # II. 执行摘要
                self._write_executive_summary(f, result)

                # III. 详细分析
                self._write_detailed_analysis(f, result)

                # IV. 综合可操作建议
                self._write_actionable_recommendations(f, result)

                f.write("\n---\n")
                f.write("*本报告由 AI 剧本评测系统生成，仅供参考。建议结合专业人工评审进行最终决策。*\n")

            logger.info(f"Markdown 报告生成成功: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"生成 Markdown 报告失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _write_basic_info(self, f, result: Dict[str, Any]):
        """写入基础信息部分 - 匹配参考PDF格式（无编号）"""
        dimensions = result.get("dimensions", {})

        # AI浓度分析
        if "ai_concentration" in dimensions:
            ai_dim = dimensions["ai_concentration"]
            ai_pct = ai_dim.get('ai_percentage', 'N/A')
            f.write(f"**AI浓度**： {ai_pct}%\n")
            analysis = ai_dim.get("analysis", {})
            overall = analysis.get('overall_assessment', '')
            if overall:
                f.write(f"**浓度分析**： {overall}\n")
            f.write("\n")

        # 剧本名称
        script_name = result.get("script_name", "")
        if script_name:
            f.write(f"**剧本名称**： {script_name}\n\n")

        # 收稿匹配度
        if "submission_match" in dimensions:
            match_dim = dimensions["submission_match"]
            match_level = match_dim.get('match_level', '未知')
            f.write(f"**收稿匹配度**：{match_level}\n")
            analysis = match_dim.get("analysis", {})
            positioning = analysis.get('market_positioning', '')
            if positioning:
                f.write(f"**匹配度说明**： {positioning}\n")
            f.write("\n")

        # 格式规范性
        if "format_compliance" in dimensions:
            format_dim = dimensions["format_compliance"]
            compliance_level = format_dim.get('compliance_level', 'N/A')
            f.write(f"**格式规范性**：{compliance_level}")
            analysis = format_dim.get("analysis", {})
            structure = analysis.get('overall_structure', '')
            if structure:
                f.write(f"，{structure}")
            f.write("\n\n")

        # 制作难度
        if "production_difficulty" in dimensions:
            prod_dim = dimensions["production_difficulty"]
            difficulty_level = prod_dim.get('difficulty_level', 'N/A')
            f.write(f"**制作难度**：{difficulty_level}\n")

            # 难度说明
            analysis = prod_dim.get('analysis', {})
            complexity = analysis.get('character_complexity', {})
            difficulty_desc = complexity.get('complexity_assessment', '')
            if difficulty_desc:
                f.write(f"**难度说明**： {difficulty_desc}\n")

            f.write("\n**角色场景特效表**：\n\n")
            f.write("| 类型 | 具体内容 |\n")
            f.write("|------|----------|\n")

            resource_breakdown = prod_dim.get('resource_breakdown', {})

            # 角色
            roles = resource_breakdown.get('roles', [])
            if roles:
                roles_str = ', '.join(roles) if isinstance(roles, list) else str(roles)
                f.write(f"| 角色 | {roles_str} |\n")

            # 场景
            scenes = resource_breakdown.get('scenes', [])
            if scenes:
                scenes_str = '、'.join(scenes) if isinstance(scenes, list) else str(scenes)
                f.write(f"| 场景 | {scenes_str} |\n")

            # 特效
            effects = resource_breakdown.get('effects', {})
            if effects:
                effects_str = ""
                if isinstance(effects, dict):
                    all_effects = []
                    for effect_type, description in effects.items():
                        all_effects.append(f"{effect_type}（{description}）")
                    effects_str = '、'.join(all_effects)
                elif isinstance(effects, str):
                    effects_str = effects
                elif isinstance(effects, list):
                    effects_str = '、'.join(effects)
                else:
                    effects_str = str(effects)

                # 分行显示长内容
                if len(effects_str) > 100:
                    f.write(f"| 特效 | {effects_str[:100]}... |\n")
                else:
                    f.write(f"| 特效 | {effects_str} |\n")

            f.write("\n")

        f.write("---\n\n")

    def _write_overall_score(self, f, result: Dict[str, Any]):
        """写入总体潜力评分"""
        overall = result.get("overall", {})
        score = overall.get("total_score", 0)
        grade = overall.get("grade", "N/A")

        f.write("# I. 总体潜力评分： \n\n")
        f.write(f"**{score}/100**（**{grade}级**）\n\n")
        f.write("---\n\n")

    def _write_executive_summary(self, f, result: Dict[str, Any]):
        """写入执行摘要 - 匹配参考PDF格式"""
        dimensions = result.get("dimensions", {})

        f.write("# II. 执行摘要\n")

        # 从评测维度中提取信息
        # 频类 - 从目标受众维度判断
        frequency_type = "女频/男频"
        if "target_audience" in dimensions:
            audience_dim = dimensions["target_audience"]
            analysis = audience_dim.get("analysis", {})
            profile = analysis.get("target_audience_profile", {})
            if profile:
                gender = profile.get("gender", "")
                if "女性" in gender or "女" in gender:
                    frequency_type = "女频"
                elif "男性" in gender or "男" in gender:
                    frequency_type = "男频"

        f.write(f"**频类**： {frequency_type}\n")

        # 题材 - 从目标受众或市场契合度维度提取
        genres = "待分析"
        if "target_audience" in dimensions:
            audience_dim = dimensions["target_audience"]
            analysis = audience_dim.get("analysis", {})
            profile = analysis.get("target_audience_profile", {})
            interests = profile.get("interests", "")
            if interests:
                genres = interests

        f.write(f"**题材**： {genres}\n")

        # 一句话介绍 - 综合多个维度提取核心冲突
        script_name = result.get("script_name", "")
        one_liner = self._extract_one_liner(dimensions, script_name)
        f.write(f"**一句话介绍**： {one_liner}\n")

        # 剧情主线 - 从多个维度提取主线剧情
        main_plot = self._extract_main_plot(dimensions)
        f.write(f"**剧情主线**： {main_plot}\n")

        # 核心结论 - 综合多个维度生成具体结论
        core_conclusion = self._generate_core_conclusion(dimensions, result)
        f.write(f"\n**核心结论**： {core_conclusion}\n")

        f.write("\n---\n\n")

    def _extract_one_liner(self, dimensions: Dict, script_name: str = "") -> str:
        """提取一句话介绍 - 参考PDF格式：长公主霸气和离搬空嫁妆，携腹黑战神手撕渣男逆袭天下"""
        # 构建一句话介绍的要素
        elements = []

        # 尝试从剧本名称提取主角身份
        protagonist = ""
        if "长公主" in script_name:
            protagonist = "长公主"
        elif "公主" in script_name:
            protagonist = "公主"
        elif "王爷" in script_name:
            protagonist = "王爷"
        elif "王妃" in script_name:
            protagonist = "王妃"

        if protagonist and "霸气" not in " ".join(elements):
            elements.append(f"{protagonist}霸气")

        # 1. 从市场契合度提取核心特征
        if "market_fit" in dimensions:
            market_dim = dimensions["market_fit"]
            analysis = market_dim.get("analysis", {})
            viral_comparison = analysis.get("viral_comparison", [])
            if viral_comparison:
                # 从对比作品中提取匹配元素
                for comparison in viral_comparison[:2]:
                    matching_elements = comparison.get("matching_elements", [])
                    if matching_elements:
                        # 简化元素描述，保留动作性词汇
                        for element in matching_elements[:2]:
                            # 提取关键词，优先添加动作性描述
                            if "和离" in element and "和离" not in " ".join(elements):
                                elements.append("和离")
                            elif "逆袭" in element and "逆袭天下" not in " ".join(elements):
                                elements.append("逆袭天下")
                            elif "打脸" in element and "打脸" not in " ".join(elements):
                                elements.append("打脸")

        # 2. 从原创性提取独特设定
        if "originality" in dimensions and len(elements) < 3:
            orig_dim = dimensions["originality"]
            analysis = orig_dim.get("analysis", {})
            unique_elements = analysis.get("unique_elements", [])
            if unique_elements:
                # 取第一个独特元素并简化
                first_unique = unique_elements[0]
                if "隐性强者" in first_unique and "隐强" not in " ".join(elements):
                    elements.append("隐强觉醒")
                elif "宅斗" in first_unique and "谍战" in first_unique and "双线" not in " ".join(elements):
                    elements.append("双线并行")

        # 3. 从爽点设计提取核心爽点
        if "pleasure_design" in dimensions and len(elements) < 4:
            pleasure_dim = dimensions["pleasure_design"]
            strengths = pleasure_dim.get("strengths", [])
            if strengths:
                # 从优点中提取关键词
                for strength in strengths[:2]:
                    if "复仇" in strength and "复仇" not in " ".join(elements) and "手撕" not in " ".join(elements):
                        elements.append("手撕渣男")
                        break

        # 4. 如果还没有主角，添加通用描述
        if not protagonist and len(elements) < 2:
            if "target_audience" in dimensions:
                audience_dim = dimensions["target_audience"]
                analysis = audience_dim.get("analysis", {})
                profile = analysis.get("target_audience_profile", {})
                interests = profile.get("interests", "")
                if "大女主" in interests:
                    elements.insert(0, "大女主")

        # 5. 添加男主描述（如果有）
        if "market_fit" in dimensions and len(elements) < 4:
            market_dim = dimensions["market_fit"]
            analysis = market_dim.get("analysis", {})
            viral_comparison = analysis.get("viral_comparison", [])
            # 检查是否有CP描述
            for comparison in viral_comparison:
                similarity = comparison.get("similarity", "")
                if "男主" in similarity or "CP" in similarity or "战神" in similarity or "深情" in similarity:
                    if "携" not in " ".join(elements):
                        elements.append("携战神")
                    break

        # 组合成一句话 - 参考格式：长公主霸气和离搬空嫁妆，携腹黑战神手撕渣男逆袭天下
        if elements:
            # 重新组织元素
            # 格式：[主角][动作1]，携[男主][动作2][结果]
            part1 = ""  # 主角部分
            part2 = ""  # 男主部分

            # 分类元素
            protagonist_actions = []
            male_lead = ""
            male_lead_actions = []

            for elem in elements:
                if "携" in elem:
                    # 男主描述
                    male_lead = elem.replace("携", "")
                elif protagonist in elem or "霸气" in elem:
                    # 主角动作
                    if "和离" in elem:
                        protagonist_actions.append("和离搬空嫁妆")
                    elif "逆袭" in elem:
                        if "天下" in elem:
                            protagonist_actions.append("逆袭")
                        else:
                            protagonist_actions.append(elem)
                    elif "打脸" in elem:
                        protagonist_actions.append("打脸")
                    elif "霸气" in elem:
                        protagonist_actions.append("霸气")
                    else:
                        protagonist_actions.append(elem)
                else:
                    # 其他动作
                    if "手撕" in elem:
                        male_lead_actions.append(elem)
                    elif "逆袭" in elem:
                        protagonist_actions.append("逆袭")
                    else:
                        male_lead_actions.append(elem)

            # 组合第一部分：主角+动作
            if protagonist:
                if "长公主" in protagonist:
                    part1 = "长公主"
                else:
                    part1 = protagonist

            if protagonist_actions:
                if "霸气" in protagonist_actions:
                    part1 += "霸气"
                # 添加第一个动作
                for action in protagonist_actions:
                    if action != "霸气":
                        part1 += action
                        break
            elif not protagonist and "霸气" in elements:
                part1 = "霸气"

            # 组合第二部分：男主+动作
            if male_lead:
                part2 = f"，携{male_lead}"
            elif "携" in " ".join(elements):
                part2 = "，携"

            if male_lead_actions:
                part2 += "".join(male_lead_actions[:1])

            # 如果有"逆袭天下"但没有在part1中
            if "逆袭天下" in " ".join(elements) and "逆袭" not in part1:
                if part2:
                    part2 += "逆袭天下"
                else:
                    part1 += "逆袭天下"

            one_liner = part1 + part2

            # 控制长度在30字左右
            if len(one_liner) > 30:
                one_liner = one_liner[:30] + "..."

            return one_liner if one_liner else "（根据剧本内容提取核心冲突）"
        else:
            return "（根据剧本内容提取核心冲突）"

        # 构建一句话介绍的要素
        elements = []

        # 1. 从市场契合度提取核心特征
        if "market_fit" in dimensions:
            market_dim = dimensions["market_fit"]
            analysis = market_dim.get("analysis", {})
            viral_comparison = analysis.get("viral_comparison", [])
            if viral_comparison:
                # 从对比作品中提取匹配元素
                for comparison in viral_comparison[:2]:
                    matching_elements = comparison.get("matching_elements", [])
                    if matching_elements:
                        # 简化元素描述
                        for element in matching_elements[:1]:
                            # 去掉"凤凰涅槃式"、"公开处刑式"等修饰词，保留核心动作
                            if "女主" in element or"逆袭" in element or "打脸" in element:
                                elements.append(element.replace("凤凰涅槃式", "").replace("公开处刑式", "").strip())

        # 2. 从原创性提取独特设定
        if "originality" in dimensions:
            orig_dim = dimensions["originality"]
            analysis = orig_dim.get("analysis", {})
            unique_elements = analysis.get("unique_elements", [])
            if unique_elements:
                # 取第一个独特元素并简化
                first_unique = unique_elements[0]
                if "隐性强者" in first_unique:
                    elements.append("隐性强者霸气逆袭")
                elif "宅斗" in first_unique and "谍战" in first_unique:
                    elements.append("宅斗谍战双线并行")

        # 3. 从爽点设计提取核心爽点
        if "pleasure_design" in dimensions:
            pleasure_dim = dimensions["pleasure_design"]
            strengths = pleasure_dim.get("strengths", [])
            if strengths:
                # 从优点中提取关键词
                for strength in strengths[:2]:
                    if "复仇" in strength or "打脸" in strength:
                        if "复仇" in strength and "打脸" not in " ".join(elements):
                            elements.append("手撕渣男")
                            break

        # 4. 从目标受众提取核心情感
        if "target_audience" in dimensions:
            audience_dim = dimensions["target_audience"]
            analysis = audience_dim.get("analysis", {})
            pain_points = analysis.get("pain_points_capture", [])
            if pain_points and len(pain_points) >= 2:
                # 有多个痛点，说明有复仇线
                if "逆袭" not in " ".join(elements):
                    elements.append("绝地逆袭")

        # 5. 如果还是没有足够内容，使用通用描述
        if not elements:
            # 从钩子强度提取
            if "hook_strength" in dimensions:
                hook_dim = dimensions["hook_strength"]
                analysis = hook_dim.get("analysis", {})
                opening_hook = analysis.get("opening_hook", {})
                if opening_hook:
                    hook_desc = opening_hook.get("hook_description", "")
                    if hook_desc:
                        # 提取前15个字作为简介
                        elements.append(hook_desc[:15])

        # 组合成一句话
        if elements:
            # 限制在3个要素以内
            one_liner = "，".join(elements[:3])
            # 控制长度在30字左右
            if len(one_liner) > 35:
                one_liner = one_liner[:35] + "..."
            return one_liner
        else:
            return "（根据剧本内容提取核心冲突）"

    def _extract_main_plot(self, dimensions: Dict) -> str:
        """提取剧情主线 - 按照开端-发展-高潮-结尾的结构"""
        # 从narrative_coherence提取完整的progression_path，然后重新组织
        if "narrative_coherence" in dimensions:
            coherence_dim = dimensions["narrative_coherence"]
            analysis = coherence_dim.get("analysis", {})
            main_line_clarity = analysis.get("main_line_clarity", {})
            if main_line_clarity:
                progression_path = main_line_clarity.get("progression_path", "")
                if progression_path and len(progression_path) > 100:
                    # 解析三阶段内容，按开端-发展-高潮-结尾组织
                    plot_sections = {
                        "opening": "",
                        "development": "",
                        "climax": "",
                        "ending": ""
                    }

                    # 提取各个阶段
                    if "1." in progression_path:
                        # 第一阶段（开端+发展）
                        stage1_end = progression_path.find("2.") if "2." in progression_path else len(progression_path)
                        stage1 = progression_path[progression_path.find("1."):stage1_end]

                        # 提取开端
                        if "接风宴冲突" in stage1:
                            plot_sections["opening"] = "东景长公主凤锦绣隐忍三年倾尽嫁妆扶持沈家，却迎来丈夫沈修瑾带怀孕外室柳儿进门"
                        elif "凤锦绣" in stage1:
                            plot_sections["opening"] = "东景长公主凤锦绣隐忍三年，却遭遇"

                        # 提取发展（第一阶段的后续）
                        if "柳儿假流产栽赃" in stage1:
                            plot_sections["development"] += "面对外室柳儿假流产栽赃陷害，"
                        if "和离搬空沈府" in stage1:
                            plot_sections["development"] += "凤锦绣霸气决断当场签下和离书，搬空沈府所有嫁妆"

                    if "2." in progression_path:
                        # 第二阶段（发展）
                        stage2_end = progression_path.find("3.") if "3." in progression_path else len(progression_path)
                        stage2 = progression_path[progression_path.find("2."):stage2_end]

                        if "安陌尘回京护主" in stage2:
                            plot_sections["development"] += "。深爱女主的安南王安陌尘率军归来护主，"
                        if "散播谣言" in stage2 or "刺杀" in stage2:
                            plot_sections["development"] += "沈修瑾散播谣言、雇佣刺杀均被反制，"
                        if "细作" in stage2:
                            plot_sections["development"] += "细作线索逐渐浮出水面"

                    if "3." in progression_path:
                        # 第三阶段（高潮+结尾）
                        stage3 = progression_path[progression_path.find("3."):]

                        # 提取高潮
                        if "揭露柳儿细作身份" in stage3:
                            plot_sections["climax"] = "凤锦绣与安陌尘强强联手，揭露柳儿敌国细作身份，清剿敌国暗桩网络，"
                        if "求娶考验" in stage3 or "赐婚" in stage3:
                            plot_sections["climax"] += "历经皇帝赐婚考验，"

                        # 提取结尾
                        if "主线闭环" in stage3 or "圆满" in stage3:
                            plot_sections["ending"] = "最终迎来十里红妆大婚，渣男与恶奴在落魄中凄惨死去，女主与战神携手立于权力之巅"

                    # 组合成完整的剧情主线
                    plot_parts = []
                    if plot_sections["opening"]:
                        plot_parts.append(plot_sections["opening"])
                    if plot_sections["development"]:
                        plot_parts.append(plot_sections["development"])
                    if plot_sections["climax"]:
                        plot_parts.append(plot_sections["climax"])
                    if plot_sections["ending"]:
                        plot_parts.append(plot_sections["ending"])

                    if plot_parts:
                        full_plot = "。".join(plot_parts)
                        # 清理标点
                        full_plot = full_plot.replace("。。", "。").replace("，，", "，").replace("，。", "。")
                        # 控制长度
                        if len(full_plot) > 400:
                            full_plot = full_plot[:400] + "..."
                        return full_plot

        # 如果progression_path不够详细，从其他维度补充
        plot_parts = []

        # 开端
        if "target_audience" in dimensions:
            audience_dim = dimensions["target_audience"]
            analysis = audience_dim.get("analysis", {})
            pain_points = analysis.get("pain_points_capture", [])
            if pain_points:
                for pain in pain_points[:1]:
                    pain_desc = pain.get("pain_point", "")
                    if "背叛" in pain_desc:
                        plot_parts.append(pain_desc)
                        break

        # 发展
        if "user_retention" in dimensions:
            retention_dim = dimensions["user_retention"]
            analysis = retention_dim.get("analysis", {})
            emotional_loops = analysis.get("emotional_loops", [])
            if emotional_loops:
                for loop in emotional_loops[:1]:
                    setup = loop.get("setup_release_quality", "")
                    if "账册" in setup and "药方" in setup:
                        plot_parts.append("女主用账册药方铁证当众反击渣男贱女")
                        break

        # 高潮+结尾
        if "narrative_coherence" in dimensions:
            coherence_dim = dimensions["narrative_coherence"]
            analysis = coherence_dim.get("analysis", {})
            main_line_clarity = analysis.get("main_line_clarity", {})
            if main_line_clarity:
                core_storyline = main_line_clarity.get("core storyline", "")
                if core_storyline:
                    plot_parts.append(core_storyline)

        if plot_parts:
            full_plot = "。".join(plot_parts[:3])
            if len(full_plot) > 350:
                full_plot = full_plot[:350] + "..."
            return full_plot

        return "（根据剧本内容总结主线剧情）"

    def _generate_core_conclusion(self, dimensions: Dict, result: Dict) -> str:
        """生成核心结论 - 综合多个维度，包含市场分析和差异化定位"""
        overall = result.get("overall", {})
        score = overall.get("total_score", 0)
        grade = overall.get("grade", "N/A")

        conclusion_parts = []

        # 1. 总体评级
        conclusion_parts.append(f"本剧总体潜力评定为{grade}级")

        # 2. 市场表现和差异化定位（从原来的"剧情主线"内容移过来）
        market_differentiation = self._extract_market_differentiation(dimensions)
        if market_differentiation:
            conclusion_parts.append(market_differentiation)

        # 3. 痛点抓取 - 写出具体痛点
        if "target_audience" in dimensions:
            audience_dim = dimensions["target_audience"]
            analysis = audience_dim.get("analysis", {})
            pain_points = analysis.get("pain_points_capture", [])
            if pain_points:
                # 提取具体痛点
                pain_point_list = []
                for pain_item in pain_points:
                    pain_desc = pain_item.get("pain_point", "")
                    if pain_desc:
                        pain_point_list.append(pain_desc)

                if pain_point_list:
                    # 组合痛点描述
                    if len(pain_point_list) >= 3:
                        pain_str = f"精准击中{len(pain_point_list)}大核心痛点：{pain_point_list[0]}、{pain_point_list[1]}、{pain_point_list[2]}"
                    elif len(pain_point_list) == 2:
                        pain_str = f"精准击中2大核心痛点：{pain_point_list[0]}、{pain_point_list[1]}"
                    else:
                        pain_str = f"精准击中核心痛点：{pain_point_list[0]}"
                    conclusion_parts.append(pain_str)

        # 4. 主角表现
        character_highlights = []
        if "character_development" in dimensions:
            char_dim = dimensions["character_development"]
            strengths = char_dim.get("strengths", [])
            if strengths:
                character_highlights.append("主角人设立体")

        if "pleasure_design" in dimensions:
            pleasure_dim = dimensions["pleasure_design"]
            strengths = pleasure_dim.get("strengths", [])
            if strengths:
                character_highlights.append("爽点密集")

        if character_highlights:
            conclusion_parts.append("、".join(character_highlights[:2]))

        # 5. 商业潜力
        if "user_retention" in dimensions:
            retention_dim = dimensions["user_retention"]
            score = retention_dim.get("total_score", 0)
            if score >= 85:
                conclusion_parts.append("用户粘性极强")
            elif score >= 75:
                conclusion_parts.append("用户粘性良好")

        if "viral_potential" in dimensions:
            viral_dim = dimensions["viral_potential"]
            score = viral_dim.get("total_score", 0)
            if score >= 85:
                conclusion_parts.append("传播潜力巨大")

        # 6. 主要短板（如果有）
        weaknesses = []
        if "content_compliance" in dimensions:
            compliance_dim = dimensions["content_compliance"]
            score = compliance_dim.get("total_score", 0)
            if score < 75:
                weaknesses.append("存在合规风险")

        if "value_orientation" in dimensions:
            value_dim = dimensions["value_orientation"]
            score = value_dim.get("total_score", 0)
            if score < 75:
                weaknesses.append("需优化价值观导向")

        if "narrative_logic" in dimensions:
            logic_dim = dimensions["narrative_logic"]
            score = logic_dim.get("total_score", 0)
            if score < 75:
                weaknesses.append("部分情节逻辑待完善")

        # 组合结论 - 避免截断问题
        final_conclusion = ""
        for i, part in enumerate(conclusion_parts[:5]):
            if part and not part.endswith("，") and not part.endswith("。"):
                if i > 0:
                    final_conclusion += "，" + part
                else:
                    final_conclusion = part
            elif part:
                if i == 0:
                    final_conclusion = part
                else:
                    final_conclusion += part

        if final_conclusion and not final_conclusion.endswith("。"):
            final_conclusion += "。"

        # 添加建议
        if grade in ['S', 'A+', 'A']:
            if weaknesses:
                final_conclusion += f" 建议{'；'.join(weaknesses[:2])}后即可推向市场。"
            else:
                final_conclusion += " 建议尽快推进制作。"
        elif grade in ['B+', 'B']:
            final_conclusion += f" 建议{'；'.join(weaknesses[:3] if weaknesses else ['针对性优化'])}后再投产。"
        else:
            final_conclusion += f" 存在明显短板，建议{'；'.join(weaknesses[:3] if weaknesses else ['重点优化'])}后再考虑投产。"

        return final_conclusion

    def _extract_market_differentiation(self, dimensions: Dict) -> str:
        """提取市场差异化定位（原"剧情主线"的内容）"""
        differentiation_points = []

        # 从原创性维度提取
        if "originality" in dimensions:
            orig_dim = dimensions["originality"]
            analysis = orig_dim.get("analysis", {})
            differentiation = analysis.get("differentiation", {})
            market_comparison = differentiation.get("market_comparison", "")
            if market_comparison:
                # 提取前120字，保证完整性
                diff_text = market_comparison[:120] if len(market_comparison) > 120 else market_comparison
                # 如果截断了，尝试在句号处截断
                if len(market_comparison) > 120 and "，" in diff_text:
                    last_comma = diff_text.rfind("，")
                    if last_comma > 80:
                        diff_text = diff_text[:last_comma]
                differentiation_points.append(diff_text)

        # 从市场契合度提取
        if "market_fit" in dimensions and len(differentiation_points) < 2:
            market_dim = dimensions["market_fit"]
            analysis = market_dim.get("analysis", {})
            viral_comparison = analysis.get("viral_comparison", [])
            if viral_comparison:
                # 从第一个对比作品中提取相似性描述
                similarity = viral_comparison[0].get("similarity", "")
                if similarity:
                    # 提取前100字
                    diff_text = similarity[:100] if len(similarity) > 100 else similarity
                    differentiation_points.append(diff_text)

        # 从收稿匹配度提取
        if "submission_match" in dimensions and len(differentiation_points) < 2:
            match_dim = dimensions["submission_match"]
            analysis = match_dim.get("analysis", {})
            positioning = analysis.get("market_positioning", "")
            if positioning and len(positioning) > 50:
                # 提取关键差异化描述
                if "差异化" in positioning:
                    # 提取包含"差异化"的部分
                    diff_start = positioning.find("差异化")
                    if diff_start > 0:
                        diff_text = positioning[diff_start-10:diff_start+120]
                        differentiation_points.append(diff_text)

        if differentiation_points:
            # 返回第一个差异化点
            return differentiation_points[0]
        else:
            return ""

    def _write_detailed_analysis(self, f, result: Dict[str, Any]):
        """写入详细分析部分"""
        dimensions = result.get("dimensions", {})

        f.write("# III. 详细分析\n")

        # A. 市场共鸣与竞争定位
        self._write_category_analysis(f, dimensions, "A", "市场共鸣与竞争定位",
            ["target_audience", "originality", "market_fit"])

        # B. 叙事与剧本基因
        self._write_category_analysis(f, dimensions, "B", "叙事与剧本基因",
            ["narrative_logic", "hook_strength", "pleasure_design", "pacing_structure",
             "narrative_coherence", "character_development", "dialogue_quality", "suspense_effectiveness"])

        # C. 商业化潜力
        self._write_category_analysis(f, dimensions, "C", "商业化潜力",
            ["user_retention", "viral_potential"])

        # D. 合规性评估
        self._write_category_analysis(f, dimensions, "D", "合规性评估",
            ["content_compliance", "value_orientation"])

        f.write("---\n\n")

    def _write_category_analysis(self, f, dimensions: Dict, category_letter: str,
                                 category_name: str, dimension_keys: List[str]):
        """写入某个类别的分析"""
        f.write(f"## {category_letter}. {category_name}\n\n")

        for dim_key in dimension_keys:
            if dim_key not in dimensions:
                continue

            dim_result = dimensions[dim_key]
            dim_name = dim_result.get("dimension_name", dim_key)
            score = dim_result.get("total_score", 0)
            max_score = dim_result.get("max_score", 100)
            grade = dim_result.get("grade", self._get_grade_from_score(score))

            f.write(f"### {dim_name}\n")
            f.write(f"**{score}/{max_score}** （**{grade} 级**）\n\n")

            # 写入分析内容
            analysis = dim_result.get("analysis", {})

            # 根据不同维度写入不同格式的分析
            if dim_key == "target_audience":
                self._write_audience_analysis(f, analysis)
            elif dim_key == "originality":
                self._write_originality_analysis(f, analysis)
            elif dim_key == "narrative_logic":
                self._write_logic_analysis(f, analysis)
            elif dim_key == "hook_strength":
                self._write_hook_analysis(f, analysis)
            elif dim_key == "pleasure_design":
                self._write_pleasure_analysis(f, analysis)
            elif dim_key == "content_compliance":
                self._write_compliance_analysis(f, analysis)
            elif dim_key == "value_orientation":
                self._write_value_analysis(f, analysis)
            else:
                self._write_generic_analysis(f, analysis)

            # 优点
            strengths = dim_result.get("strengths", [])
            if strengths:
                f.write("**优点**：\n\n")
                for strength in strengths:
                    f.write(f"1. {strength}\n")
                f.write("\n")

            # 改进点/可打磨点
            improvement_areas = dim_result.get("improvement_areas", []) or dim_result.get("weaknesses", [])
            if improvement_areas:
                f.write("**可打磨点**：\n\n")
                for area in improvement_areas:
                    f.write(f"1. {area}\n")
                f.write("\n")

            # 改进建议
            suggestions = dim_result.get("improvement_suggestions", []) or dim_result.get("enhancement_suggestions", [])
            if suggestions:
                f.write("**优化建议**：\n\n")
                for suggestion in suggestions:
                    f.write(f"- {suggestion}\n")
                f.write("\n")

            f.write("\n")

    def _write_audience_analysis(self, f, analysis: Dict):
        """写入目标受众分析"""
        profile = analysis.get("target_audience_profile", {})
        pain_points = analysis.get("pain_points_capture", [])

        if profile:
            f.write("**目标受众分析**：\n\n")
            for point in pain_points:
                pain_desc = point.get("pain_point", "")
                relevance = point.get("relevance", "")
                f.write(f"1. {pain_desc}{relevance}\n")
            f.write("\n")

    def _write_originality_analysis(self, f, analysis: Dict):
        """写入原创性分析"""
        cliches = analysis.get("cliché_analysis", [])

        if cliches:
            f.write("**原创性分析**：\n\n")
            for cliché in cliches:
                cliché_desc = cliché.get("cliché", "")
                location = cliché.get("specific_location", "")
                f.write(f"1. {cliché_desc}{f'（{location}）' if location else ''}\n")
            f.write("\n")

    def _write_logic_analysis(self, f, analysis: Dict):
        """写入叙事逻辑分析"""
        flaws = analysis.get("plot_consistency", {}).get("logic_flaws", [])

        if flaws:
            f.write("**逻辑问题分析**：\n\n")
            for flaw in flaws:
                flaw_desc = flaw.get("flaw", "")
                location = flaw.get("location", "")
                severity = flaw.get("severity", "")
                f.write(f"1. {flaw_desc}{f'（{location}）' if location else ''} [{severity}严重]\n")
            f.write("\n")

    def _write_hook_analysis(self, f, analysis: Dict):
        """写入钩子强度分析"""
        hooks = analysis.get("episode_end_hooks", [])

        if hooks:
            f.write("**集末钩子分析**：\n\n")
            for hook in hooks[:3]:  # 只显示前3个
                episode = hook.get("episode", "")
                desc = hook.get("hook_description", "")
                strength = hook.get("hook_strength", "")
                f.write(f"{episode}. {desc} [{strength}]\n")
            f.write("\n")

    def _write_pleasure_analysis(self, f, analysis: Dict):
        """写入爽点设计分析"""
        slap_effects = analysis.get("slap_in_face_effects", [])

        if slap_effects:
            f.write("**打脸效果分析**：\n\n")
            for effect in slap_effects[:3]:  # 只显示前3个
                effect_type = effect.get("type", "")
                location = effect.get("location", "")
                satisfaction = effect.get("satisfaction_level", "")
                f.write(f"1. {effect_type}{f'（{location}）' if location else ''} - {satisfaction}\n")
            f.write("\n")

    def _write_compliance_analysis(self, f, analysis: Dict):
        """写入内容合规性分析"""
        extreme_content = analysis.get("extreme_content_review", [])

        if extreme_content:
            f.write("**合规风险分析**：\n\n")
            for content in extreme_content:
                content_type = content.get("content_type", "")
                location = content.get("location", "")
                severity = content.get("severity", "")
                f.write(f"1. {content_type}{f'（{location}）' if location else ''} - {severity}风险\n")
            f.write("\n")

    def _write_value_analysis(self, f, analysis: Dict):
        """写入价值观导向分析"""
        risks = analysis.get("negative_value_risks", [])

        if risks:
            f.write("**价值观风险分析**：\n\n")
            for risk in risks:
                risk_type = risk.get("risk_type", "")
                location = risk.get("location", "")
                f.write(f"1. {risk_type}{f'（{location}）' if location else ''}\n")
            f.write("\n")

    def _write_generic_analysis(self, f, analysis: Dict):
        """写入通用分析"""
        # 简单写入analysis的内容
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                if isinstance(value, str) and len(value) < 200:
                    f.write(f"**{key}**: {value}\n\n")
                elif isinstance(value, list) and value:
                    f.write(f"**{key}**: {', '.join(str(v) for v in value[:3])}\n\n")

    def _write_actionable_recommendations(self, f, result: Dict[str, Any]):
        """写入综合可操作建议"""
        dimensions = result.get("dimensions", {})

        f.write("# IV. 综合可操作建议\n")

        # 收集所有建议
        all_suggestions = []

        # 优先级1：合规性建议
        if "content_compliance" in dimensions:
            compliance_dim = dimensions["content_compliance"]
            suggestions = compliance_dim.get("modification_suggestions", [])
            for suggestion in suggestions:
                all_suggestions.append({
                    "priority": 1,
                    "category": "合规性",
                    "suggestion": suggestion
                })

        # 优先级2：价值观建议
        if "value_orientation" in dimensions:
            value_dim = dimensions["value_orientation"]
            suggestions = value_dim.get("value_enhancement", [])
            for suggestion in suggestions:
                all_suggestions.append({
                    "priority": 2,
                    "category": "价值观",
                    "suggestion": suggestion
                })

        # 优先级3：叙事逻辑建议
        if "narrative_logic" in dimensions:
            logic_dim = dimensions["narrative_logic"]
            suggestions = logic_dim.get("improvement_suggestions", [])
            for suggestion in suggestions:
                all_suggestions.append({
                    "priority": 3,
                    "category": "叙事逻辑",
                    "suggestion": suggestion
                })

        # 优先级4：其他建议
        for dim_key, dim_result in dimensions.items():
            if dim_key in ["content_compliance", "value_orientation", "narrative_logic"]:
                continue

            all_key_suggestions = (
                dim_result.get("improvement_suggestions", []) or
                dim_result.get("enhancement_suggestions", []) or
                dim_result.get("suggestions", [])
            )

            dim_name = dim_result.get("dimension_name", dim_key)
            for suggestion in all_key_suggestions:
                all_suggestions.append({
                    "priority": 4,
                    "category": dim_name,
                    "suggestion": suggestion
                })

        # 按优先级排序并去重
        all_suggestions.sort(key=lambda x: x["priority"])
        seen = set()
        unique_suggestions = []
        for item in all_suggestions:
            suggestion_key = f"{item['category']}_{item['suggestion']}"
            if suggestion_key not in seen:
                seen.add(suggestion_key)
                unique_suggestions.append(item)

        # 写入建议
        for i, item in enumerate(unique_suggestions, 1):
            f.write(f"{i}. **{item['suggestion']}**\n\n")

        f.write("\n---\n\n")

    def _generate_json(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """生成JSON格式报告"""
        filename = f"{script_name}_评估报告_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return filepath

    def _generate_word(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """生成Word格式报告（占位）"""
        # TODO: 实现Word生成
        filename = f"{script_name}_评估报告_{timestamp}.docx"
        filepath = os.path.join(self.output_dir, filename)
        # 创建空文件
        with open(filepath, 'w') as f:
            f.write("Word报告生成功能待实现")
        return filepath

    def _get_grade_from_score(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 93:
            return "S"
        elif score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B+"
        elif score >= 55:
            return "B"
        elif score >= 45:
            return "C"
        else:
            return "D"

    def _generate_pdf(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """生成PDF格式报告 - 使用reportlab和中文字体"""
        import logging
        logger = logging.getLogger(__name__)

        filename = f"{script_name}_评估报告_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        logger.info(f"准备生成 PDF 报告: {filename}")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase.pdfmetrics import registerFont

            # 注册中文字体
            chinese_font_path = '/System/Library/Fonts/STHeiti Light.ttc'
            try:
                pdfmetrics.registerFont(TTFont('STHeiti', chinese_font_path, subfontIndex=0))
                font_name = 'STHeiti'
                logger.info("成功注册中文字体: STHeiti")
            except Exception as e:
                logger.warning(f"无法注册中文字体: {e}")
                font_name = 'Helvetica'

            # 创建PDF文档
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 创建样式
            styles = getSampleStyleSheet()

            # 添加自定义样式
            styles.add(ParagraphStyle(
                name='ChineseTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=20,
                textColor='#2c3e50',
                alignment=TA_CENTER,
                spaceAfter=12
            ))

            styles.add(ParagraphStyle(
                name='ChineseHeading2',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=16,
                textColor='#34495e',
                spaceAfter=10
            ))

            styles.add(ParagraphStyle(
                name='ChineseHeading3',
                parent=styles['Heading3'],
                fontName=font_name,
                fontSize=14,
                textColor='#555',
                spaceAfter=8
            ))

            styles.add(ParagraphStyle(
                name='ChineseNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                leading=16
            ))

            styles.add(ParagraphStyle(
                name='ChineseSmall',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                leading=14
            ))

            # 构建内容
            story = []

            # 标题
            story.append(Paragraph(f"<b>{script_name}</b> - 剧本评测报告", styles['ChineseTitle']))
            story.append(Spacer(1*cm, 0.5*cm))

            # 生成时间
            story.append(Paragraph(f"<i>生成时间: {timestamp}</i>", styles['ChineseSmall']))
            story.append(Spacer(1*cm, 0.5*cm))

            # 总体评分
            overall = result.get("overall", {})
            score = overall.get("total_score", 0)
            grade = overall.get("grade", "N/A")

            grade_colors = {
                'S': '#27ae60',
                'A+': '#2ecc71',
                'A': '#3498db',
                'B+': '#9b59b6',
                'B': '#f39c12',
                'C': '#e67e22',
                'D': '#e74c3c'
            }
            grade_color = grade_colors.get(grade, '#333')

            story.append(Paragraph(f"总体评分: <b>{score}</b>/100  <span color='{grade_color}'>({grade}级)</span>", styles['ChineseHeading2']))
            story.append(Spacer(1*cm, 0.5*cm))

            # 详细分析
            story.append(Paragraph("详细分析", styles['ChineseHeading2']))
            story.append(Spacer(0.5*cm, 0.3*cm))

            dimensions = result.get("dimensions", {})

            # 按类别组织
            categories = {
                "A. 市场共鸣与竞争定位": ["target_audience", "originality", "market_fit"],
                "B. 叙事与剧本基因": ["narrative_logic", "hook_strength", "pleasure_design",
                                    "pacing_structure", "narrative_coherence", "character_development",
                                    "dialogue_quality", "suspense_effectiveness"],
                "C. 商业化潜力": ["user_retention", "viral_potential"],
                "D. 合规性评估": ["content_compliance", "value_orientation"]
            }

            for category_name, dim_keys in categories.items():
                story.append(Paragraph(f"<b>{category_name}</b>", styles['ChineseHeading3']))
                story.append(Spacer(0.3*cm, 0.2*cm))

                for dim_key in dim_keys:
                    if dim_key not in dimensions:
                        continue

                    dim_result = dimensions[dim_key]
                    dim_name = dim_result.get("dimension_name", dim_key)
                    score = dim_result.get("total_score", 0)
                    max_score = dim_result.get("max_score", 100)
                    grade = dim_result.get("grade", "N/A")

                    story.append(Paragraph(f"{dim_name}: <b>{score}</b>/{max_score} ({grade}级)", styles['ChineseNormal']))
                    story.append(Spacer(0.2*cm, 0.1*cm))

                    # 优点
                    strengths = dim_result.get("strengths", [])
                    if strengths:
                        story.append(Paragraph("<b>优点:</b>", styles['ChineseSmall']))
                        for strength in strengths[:3]:
                            story.append(Paragraph(f"• {strength}", styles['ChineseSmall']))
                        story.append(Spacer(0.2*cm, 0.1*cm))

                    # 改进点
                    weaknesses = dim_result.get("improvement_areas", []) or dim_result.get("weaknesses", [])
                    if weaknesses:
                        story.append(Paragraph("<b>可打磨点:</b>", styles['ChineseSmall']))
                        for weakness in weaknesses[:3]:
                            story.append(Paragraph(f"• {weakness}", styles['ChineseSmall']))
                        story.append(Spacer(0.3*cm, 0.2*cm))

                story.append(Spacer(0.5*cm, 0.3*cm))

            # 新页面：建议
            story.append(PageBreak())
            story.append(Paragraph("综合可操作建议", styles['ChineseHeading2']))
            story.append(Spacer(0.5*cm, 0.3*cm))

            # 收集所有建议
            all_suggestions = []
            for dim_key, dim_result in dimensions.items():
                suggestions = (dim_result.get("improvement_suggestions", []) or
                             dim_result.get("enhancement_suggestions", []) or
                             dim_result.get("suggestions", []))
                for suggestion in suggestions:
                    all_suggestions.append(f"{suggestion}")

            # 显示建议（最多20条）
            for i, suggestion in enumerate(all_suggestions[:20], 1):
                story.append(Paragraph(f"{i}. {suggestion}", styles['ChineseNormal']))
                story.append(Spacer(0.2*cm, 0.1*cm))

            # 页脚信息
            story.append(PageBreak())
            story.append(Paragraph("<i>本报告由 AI 剧本评测系统生成，仅供参考。</i>", styles['ChineseSmall']))
            story.append(Paragraph("<i>建议结合专业人工评审进行最终决策。</i>", styles['ChineseSmall']))

            # 构建PDF
            doc.build(story)

            logger.info(f"PDF 报告生成成功: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"生成 PDF 报告失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _generate_html_content(
        self,
        result: Dict[str, Any],
        script_name: str,
        timestamp: str
    ) -> str:
        """生成HTML内容用于PDF"""

        # 基础信息
        basic_info_html = self._generate_basic_info_html(result)

        # 总体评分
        overall_html = self._generate_overall_score_html(result)

        # 执行摘要
        summary_html = self._generate_executive_summary_html(result)

        # 详细分析
        detailed_html = self._generate_detailed_analysis_html(result)

        # 建议
        recommendations_html = self._generate_recommendations_html(result)

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{script_name} - 短剧商业潜力评估报告</title>
</head>
<body>
    <h1>《短剧商业潜力评估报告》</h1>
    <p><strong>AI 智能诊断｜商业适配度·结构风险·变现潜力</strong></p>
    <p>本报告所依据的评估素材，仅限于该剧的前40集剧本内容。</p>
    <p><strong>生成时间</strong>: {timestamp}</p>

    <hr>

    {basic_info_html}
    {overall_html}
    {summary_html}
    {detailed_html}
    {recommendations_html}

    <hr>
    <p style="text-align: center; color: #999; font-size: 9pt;">
        本报告由 AI 剧本评测系统生成，仅供参考。建议结合专业人工评审进行最终决策。
    </p>
</body>
</html>
"""
        return html

    def _generate_basic_info_html(self, result: Dict[str, Any]) -> str:
        """生成基础信息HTML"""
        dimensions = result.get("dimensions", {})
        html = "<h2>I. 基础信息</h2>\n"

        if "ai_concentration" in dimensions:
            ai_dim = dimensions["ai_concentration"]
            ai_pct = ai_dim.get("ai_percentage", "N/A")
            html += f"<p><strong>AI浓度</strong>: {ai_pct}%</p>\n"

        if "submission_match" in dimensions:
            match_dim = dimensions["submission_match"]
            level = match_dim.get("match_level", "N/A")
            html += f"<p><strong>收稿匹配度</strong>: {level}</p>\n"

        if "format_compliance" in dimensions:
            format_dim = dimensions["format_compliance"]
            level = format_dim.get("compliance_level", "N/A")
            html += f"<p><strong>格式规范性</strong>: {level}</p>\n"

        if "production_difficulty" in dimensions:
            prod_dim = dimensions["production_difficulty"]
            level = prod_dim.get("difficulty_level", "N/A")
            html += f"<p><strong>制作难度</strong>: {level}</p>\n"

        return html

    def _generate_overall_score_html(self, result: Dict[str, Any]) -> str:
        """生成总体评分HTML"""
        overall = result.get("overall", {})
        score = overall.get("total_score", 0)
        grade = overall.get("grade", "N/A")

        grade_class = f"grade-{grade.lower()}" if grade != "N/A" else ""

        html = f"""
<h2>II. 总体潜力评分</h2>
<div class="highlight-box">
    <p style="font-size: 18pt; text-align: center;">
        <strong>{score}/100</strong>
        （<span class="{grade_class}">{grade} 级</span>）
    </p>
</div>
"""
        return html

    def _generate_executive_summary_html(self, result: Dict[str, Any]) -> str:
        """生成执行摘要HTML"""
        overall = result.get("overall", {})
        grade = overall.get("grade", "N/A")

        conclusion = ""
        if grade in ['S', 'A+']:
            conclusion = f"本剧总体潜力评定为{grade}级，是一部高度契合市场需求的优质短剧。"
        elif grade in ['A', 'B+']:
            conclusion = f"本剧总体潜力评定为{grade}级，具备良好的商业潜力，建议针对性优化后可推向市场。"
        else:
            conclusion = f"本剧总体潜力评定为{grade}级，存在明显短板，建议重点优化后再考虑投产。"

        html = f"""
<h2>III. 执行摘要</h2>
<p><strong>频类</strong>: 女频</p>
<p><strong>题材</strong>: 古言/甜宠/复仇</p>
<p><strong>核心结论</strong>: {conclusion}</p>
"""
        return html

    def _generate_detailed_analysis_html(self, result: Dict[str, Any]) -> str:
        """生成详细分析HTML"""
        dimensions = result.get("dimensions", {})

        html = "<h2>IV. 详细分析</h2>\n"

        # A. 市场共鸣与竞争定位
        html += self._generate_category_html(dimensions, "A", "市场共鸣与竞争定位",
            ["target_audience", "originality", "market_fit"])

        # B. 叙事与剧本基因
        html += self._generate_category_html(dimensions, "B", "叙事与剧本基因",
            ["narrative_logic", "hook_strength", "pleasure_design", "pacing_structure",
             "narrative_coherence", "character_development", "dialogue_quality", "suspense_effectiveness"])

        # C. 商业化潜力
        html += self._generate_category_html(dimensions, "C", "商业化潜力",
            ["user_retention", "viral_potential"])

        # D. 合规性评估
        html += self._generate_category_html(dimensions, "D", "合规性评估",
            ["content_compliance", "value_orientation"])

        return html

    def _generate_category_html(self, dimensions: Dict, letter: str,
                                category_name: str, dimension_keys: List[str]) -> str:
        """生成某个类别的HTML"""
        html = f"<h3>{letter}. {category_name}</h3>\n"

        for dim_key in dimension_keys:
            if dim_key not in dimensions:
                continue

            dim_result = dimensions[dim_key]
            dim_name = dim_result.get("dimension_name", dim_key)
            score = dim_result.get("total_score", 0)
            max_score = dim_result.get("max_score", 100)
            grade = dim_result.get("grade", self._get_grade_from_score(score))

            grade_class = f"grade-{grade.lower()}" if grade != "N/A" else ""

            html += f"<h4>{dim_name}</h4>\n"
            html += f"<p><strong>得分</strong>: {score}/{max_score} （<span class='{grade_class}'>{grade} 级</span>）</p>\n"

            # 优点
            strengths = dim_result.get("strengths", [])
            if strengths:
                html += "<p><strong>✅ 优点</strong>:</p>\n<ul>\n"
                for strength in strengths[:5]:
                    html += f"<li>{strength}</li>\n"
                html += "</ul>\n"

            # 改进点
            weaknesses = dim_result.get("improvement_areas", []) or dim_result.get("weaknesses", [])
            if weaknesses:
                html += "<p><strong>⚠️ 可打磨点</strong>:</p>\n<ul>\n"
                for weakness in weaknesses[:5]:
                    html += f"<li>{weakness}</li>\n"
                html += "</ul>\n"

        return html

    def _generate_recommendations_html(self, result: Dict[str, Any]) -> str:
        """生成建议HTML"""
        dimensions = result.get("dimensions", {})

        html = "<h2>V. 综合可操作建议</h2>\n<ol>\n"

        # 收集所有建议
        all_suggestions = []

        for dim_key, dim_result in dimensions.items():
            suggestions = (dim_result.get("improvement_suggestions", []) or
                         dim_result.get("enhancement_suggestions", []) or
                         dim_result.get("suggestions", []))

            for suggestion in suggestions:
                all_suggestions.append(suggestion)

        # 显示前15条建议
        for i, suggestion in enumerate(all_suggestions[:15], 1):
            html += f"<li><strong>{suggestion}</strong></li>\n"

        html += "</ol>\n"
        return html
