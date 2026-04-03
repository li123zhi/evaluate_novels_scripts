#!/usr/bin/env python3
"""
重新生成失败的评测报告
"""
import sys
import os
import json
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.new_report_generator import NewReportGenerator

def find_latest_evaluation():
    """查找最近的评测结果"""
    # 查找最近的JSON文件
    import glob
    json_files = glob.glob("/Users/ruite_ios/Desktop/aiShortVideo/evaluate_novels_scripts/outputs/*_20260402_*.json")

    if not json_files:
        print("未找到评测JSON文件")
        return None, None

    # 找到最新的JSON文件
    latest_json = max(json_files, key=os.path.getmtime)
    latest_md = latest_json.replace('.json', '.md')

    print(f"找到评测JSON文件: {latest_json}")

    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data, latest_md

def regenerate_report():
    """重新生成报告"""
    evaluation_data, md_file = find_latest_evaluation()

    if evaluation_data is None:
        print("无法找到评测数据，无法重新生成报告")
        return

    print("\n开始重新生成报告...")
    print(f"剧本名称: {evaluation_data.get('script_name', 'Unknown')}")
    print(f"总分: {evaluation_data.get('overall', {}).get('total_score', 'N/A')}")

    # 使用新的报告生成器
    report_generator = NewReportGenerator(output_dir="/Users/ruite_ios/Desktop/aiShortVideo/evaluate_novels_scripts/outputs")

    try:
        # 生成报告
        generated_files = report_generator.generate(evaluation_data, formats=['markdown'])

        print(f"\n✅ 报告重新生成成功！")
        print(f"生成的文件:")
        for file in generated_files:
            print(f"  - {file}")

    except Exception as e:
        print(f"\n❌ 报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_report()
