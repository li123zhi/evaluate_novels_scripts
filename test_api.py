#!/usr/bin/env python3
"""测试 API 连接"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.api_client import DoubaoAPIClient

def test_api():
    """测试 API 调用"""
    print("测试豆包 API 连接...")

    try:
        client = DoubaoAPIClient()
        print(f"✓ API 客户端初始化成功")
        print(f"  - API URL: {client.api_url}")
        print(f"  - 模型: {client.model_endpoint}")
        print(f"  - 超时: {client.timeout}秒")
        print(f"  - 最大 tokens: {client.max_tokens}")

        # 测试简单请求
        print("\n发送测试请求...")
        response = client.chat("请用一句话介绍你自己", json_mode=False)
        print(f"✓ API 响应成功")
        print(f"  响应内容: {response[:100]}...")

        return True

    except Exception as e:
        print(f"✗ API 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
