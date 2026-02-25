"""
豆包 API 客户端
封装与豆包 seed-1.8 模型的交互
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DoubaoAPIClient:
    """豆包 API 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model_name: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        timeout: int = 300,  # 5分钟超时
        max_retries: int = 3
    ):
        """
        初始化 API 客户端

        Args:
            api_key: API 密钥
            api_url: API 端点 URL
            model_name: 模型名称/endpoint
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key or os.getenv("ARK_API_KEY")
        base_url = api_url or os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model_endpoint = model_name or os.getenv("MODEL_ENDPOINT", "ep-20260112180849-626fn")
        self.api_url = f"{base_url}/chat/completions"
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

        # 从环境变量读取配置
        self.timeout = int(os.getenv("API_TIMEOUT", str(timeout)))
        self.max_tokens = int(os.getenv("MAX_TOKENS", str(max_tokens)))

        if not self.api_key:
            raise ValueError("API 密钥未设置，请在 .env 文件中配置 ARK_API_KEY")

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发起 API 请求

        Args:
            messages: 消息列表
            response_format: 响应格式（如 {"type": "json_object"}）

        Returns:
            API 响应数据
        """
        import logging
        logger = logging.getLogger(__name__)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 计算输入 token 大小（粗略估计）
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        logger.info(f"发起 API 请求，输入字符数: {total_chars}, 超时设置: {self.timeout}秒")

        payload = {
            "model": self.model_endpoint,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        # 如果指定了响应格式，添加到 payload
        if response_format:
            payload["response_format"] = response_format

        for attempt in range(self.max_retries):
            try:
                logger.info(f"API 请求尝试 {attempt + 1}/{self.max_retries}")
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"API 请求成功，状态码: {response.status_code}")
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"API 请求超时（第 {attempt + 1} 次尝试）")
                if attempt == self.max_retries - 1:
                    raise TimeoutError(f"API 请求超时（{self.timeout}秒）")
                time.sleep(2 ** attempt)  # 指数退避

            except requests.exceptions.HTTPError as e:
                logger.warning(f"API HTTP 错误: {e}")
                if attempt == self.max_retries - 1:
                    error_detail = response.text if 'response' in locals() else str(e)
                    raise RuntimeError(f"API 请求失败: {error_detail}")
                time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                logger.warning(f"API 网络错误: {e}")
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"网络请求错误: {str(e)}")
                time.sleep(2 ** attempt)

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """
        发送聊天请求

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            json_mode: 是否启用 JSON 模式

        Returns:
            模型响应文本
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None

        response_data = self._make_request(messages, response_format)

        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"解析 API 响应失败: {str(e)}")

    def chat_with_json_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求并解析 JSON 响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            解析后的 JSON 数据
        """
        response_text = self.chat(prompt, system_prompt, json_mode=True)

        # 记录响应用于调试
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"API 响应内容 (前500字符): {response_text[:500]}")

        # 清理响应文本 - 移除可能存在的 markdown 代码块标记
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        try:
            parsed = json.loads(cleaned_response)
            # 处理 API 返回 list 的情况（提取第一个元素）
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[0]
            # 处理 API 返回其他类型的情况
            if not isinstance(parsed, dict):
                return {"error": f"API 返回非字典类型: {type(parsed).__name__}", "raw_value": parsed}
            return parsed
        except json.JSONDecodeError as e:
            # 如果 JSON 解析失败，检查是否是单个值（如数字）
            try:
                # 尝试直接解析为数字
                cleaned_response_stripped = cleaned_response.strip()
                if cleaned_response_stripped.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '').isdigit():
                    return {"error": "API 返回了单个数值而非 JSON 对象", "raw_value": float(cleaned_response_stripped)}
            except:
                pass
            raise RuntimeError(f"解析模型 JSON 响应失败: {str(e)}\n原始响应: {response_text}\n清理后响应: {cleaned_response}")


# 便捷函数
def get_client() -> DoubaoAPIClient:
    """获取配置好的 API 客户端实例"""
    return DoubaoAPIClient()
