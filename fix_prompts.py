#!/usr/bin/env python3
"""
批量更新所有提示词模板，添加 JSON 格式强制要求
"""

import os
import glob

# JSON 格式强制要求的声明
JSON_REQUIREMENT = """⚠️ 重要：你必须严格按照 JSON 格式返回评测结果，不要添加任何其他文本或解释。
返回的内容必须是一个完整的 JSON 对象，以 { 开始，以 } 结束。
不要只返回数字、字符串或其他单一值，必须返回完整的 JSON 对象结构。

"""

def process_prompt_file(file_path):
    """处理单个提示词文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已经包含 JSON 要求
        if '⚠️ 重要：你必须严格按照 JSON 格式返回评测结果' in content:
            print(f"✅ 跳过（已有JSON要求）: {os.path.basename(file_path)}")
            return False

        # 找到第一行（角色定义）
        lines = content.split('\n')
        if not lines:
            return False

        first_line = lines[0]

        # 如果第一行是角色定义，在它之后插入JSON要求
        if '是一位' in first_line or '你是' in first_line or '你是一位' in first_line:
            new_content = first_line + '\n\n' + JSON_REQUIREMENT + '\n'.join(lines[1:])
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ 已更新: {os.path.basename(file_path)}")
            return True

        return False

    except Exception as e:
        print(f"❌ 错误 {os.path.basename(file_path)}: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("批量更新提示词模板，添加 JSON 格式强制要求")
    print("=" * 60)

    # 查找所有 .txt 提示词文件（排除 novel 子目录）
    prompt_files = []
    for file_path in glob.glob('prompts/*.txt'):
        if 'novel' not in file_path:
            prompt_files.append(file_path)

    print(f"\n找到 {len(prompt_files)} 个提示词文件\n")

    updated_count = 0
    for file_path in sorted(prompt_files):
        if process_prompt_file(file_path):
            updated_count += 1

    print("\n" + "=" * 60)
    print(f"完成！共更新了 {updated_count}/{len(prompt_files)} 个文件")
    print("=" * 60)

if __name__ == '__main__':
    main()
