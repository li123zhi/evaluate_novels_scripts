#!/usr/bin/env python3
"""
剧本评测系统 - 主程序入口
使用豆包 seed-1.8 模型进行短剧剧本质量评测
"""

import sys
import os
import click
import glob
from pathlib import Path
from typing import List

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.evaluator import ScriptEvaluator
from src.report_generator import ReportGenerator


@click.group()
def cli():
    """AI 剧本评测系统 - 使用豆包 seed-1.8 模型评测短剧剧本质量"""
    pass


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--dimensions', '-d', multiple=True, help='指定评测维度 (可多选)')
@click.option('--format', '-f', multiple=True, default=['markdown'], type=click.Choice(['markdown', 'json']),
              help='输出格式')
@click.option('--output', '-o', type=click.Path(), help='输出目录')
def evaluate(script_path: str, dimensions: tuple, format: tuple, output: str):
    """
    评测单个剧本文件

    SCRIPT_PATH: 剧本文件路径
    """
    click.echo(f"🎬 开始评测剧本: {script_path}")

    # 转换 dimensions
    dim_list = list(dimensions) if dimensions else None

    # 转换 format
    format_list = list(format)

    try:
        # 初始化评测器
        evaluator = ScriptEvaluator()

        # 执行评测
        result = evaluator.evaluate(script_path, dimensions=dim_list)

        # 显示结果摘要
        overall = result.get("overall", {})
        score = overall.get("total_score", 0)
        grade = overall.get("grade", "N/A")

        click.echo(f"\n✅ 评测完成!")
        click.echo(f"📊 综合评分: {score}/100  (等级: {grade})")

        # 生成报告
        report_generator = ReportGenerator(output_dir=output) if output else ReportGenerator()
        output_files = report_generator.generate(result, formats=format_list)

        click.echo(f"\n📄 报告已生成:")
        for file in output_files:
            click.echo(f"   - {file}")

    except Exception as e:
        click.echo(f"❌ 评测失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('scripts_dir', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.txt', help='剧本文件匹配模式 (默认: *.txt)')
@click.option('--dimensions', '-d', multiple=True, help='指定评测维度 (可多选)')
@click.option('--format', '-f', multiple=True, default=['markdown'], type=click.Choice(['markdown', 'json']),
              help='输出格式')
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--summary', '-s', is_flag=True, help='生成汇总报告')
def batch(scripts_dir: str, pattern: str, dimensions: tuple, format: tuple, output: str, summary: bool):
    """
    批量评测目录下的剧本文件

    SCRIPTS_DIR: 剧本文件所在目录
    """
    # 查找剧本文件
    search_pattern = os.path.join(scripts_dir, pattern)
    script_files = glob.glob(search_pattern)

    if not script_files:
        click.echo(f"❌ 在目录 {scripts_dir} 中未找到匹配 {pattern} 的文件", err=True)
        sys.exit(1)

    click.echo(f"🎬 找到 {len(script_files)} 个剧本文件")
    click.echo(f"📂 开始批量评测...\n")

    # 转换参数
    dim_list = list(dimensions) if dimensions else None
    format_list = list(format)

    try:
        # 初始化评测器和报告生成器
        evaluator = ScriptEvaluator()
        report_generator = ReportGenerator(output_dir=output) if output else ReportGenerator()

        results = []

        # 逐个评测
        with click.progressbar(script_files, label='评测进度') as bar:
            for script_file in bar:
                try:
                    result = evaluator.evaluate(script_file, dimensions=dim_list, show_progress=False)
                    results.append(result)

                    # 生成单独报告
                    report_generator.generate(result, formats=format_list)

                except Exception as e:
                    click.echo(f"\n⚠️  评测 {script_file} 失败: {str(e)}", err=True)
                    continue

        # 显示结果
        click.echo(f"\n✅ 批量评测完成! 共评测 {len(results)} 个剧本")

        # 生成汇总报告
        if summary and len(results) > 1:
            summary_file = report_generator.generate_batch_summary(results)
            click.echo(f"\n📊 汇总报告已生成: {summary_file}")

            # 显示排行榜
            sorted_results = sorted(
                results,
                key=lambda x: x.get("overall", {}).get("total_score", 0),
                reverse=True
            )
            click.echo("\n🏆 评测排行榜:")
            click.echo("{:<5} {:<20} {:<10} {:<5}".format("排名", "剧本名称", "得分", "等级"))
            click.echo("-" * 45)
            for i, result in enumerate(sorted_results[:10], 1):
                name = result.get("script_name", "Unknown")[:20]
                score = result.get("overall", {}).get("total_score", 0)
                grade = result.get("overall", {}).get("grade", "N/A")
                click.echo("{:<5} {:<20} {:<10} {:<5}".format(i, name, score, grade))

    except Exception as e:
        click.echo(f"❌ 批量评测失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def list_dimensions():
    """列出所有可用的评测维度"""
    try:
        evaluator = ScriptEvaluator()
        dimensions = evaluator.config.get('evaluation_dimensions', {})

        click.echo("📋 可用的评测维度:\n")

        for key, config in dimensions.items():
            name = config.get('name', key)
            weight = config.get('weight', 0)
            description = config.get('description', '')

            click.echo(f"• {key}")
            click.echo(f"  名称: {name}")
            click.echo(f"  权重: {weight*100:.0f}%")
            click.echo(f"  说明: {description}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ 获取维度列表失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def check_config():
    """检查配置是否正确"""
    click.echo("🔍 检查配置...\n")

    # 检查环境变量
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL")
    model_endpoint = os.getenv("MODEL_ENDPOINT")

    checks = []

    # API Key 检查
    if api_key and api_key != "your_api_key_here":
        checks.append(("API 密钥", "✅ 已配置", True))
    else:
        checks.append(("API 密钥", "❌ 未配置，请在 .env 文件中设置 ARK_API_KEY", False))

    # Base URL 检查
    if base_url:
        checks.append(("API 基础地址", f"✅ {base_url}", True))
    else:
        checks.append(("API 基础地址", "⚠️  未配置，将使用默认值", True))

    # 模型 Endpoint 检查
    if model_endpoint:
        checks.append(("模型 Endpoint", f"✅ {model_endpoint}", True))
    else:
        checks.append(("模型 Endpoint", "⚠️  未配置，将使用默认值", True))

    # 配置文件检查
    config_path = os.path.join(os.path.dirname(__file__), "config.yml")
    if os.path.exists(config_path):
        checks.append(("配置文件", "✅ config.yml 存在", True))
    else:
        checks.append(("配置文件", "❌ config.yml 不存在", False))

    # 提示词文件检查
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    if os.path.exists(prompts_dir):
        prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.txt')]
        checks.append(("提示词模板", f"✅ 找到 {len(prompt_files)} 个模板", True))
    else:
        checks.append(("提示词模板", "❌ prompts 目录不存在", False))

    # 输出结果
    all_ok = True
    for name, status, ok in checks:
        click.echo(f"{status} - {name}")
        if not ok:
            all_ok = False

    click.echo()
    if all_ok:
        click.echo("✅ 配置检查通过，可以开始使用!")
    else:
        click.echo("⚠️  配置存在问题，请根据上述提示进行修复")

    return 0 if all_ok else 1


if __name__ == '__main__':
    cli()
