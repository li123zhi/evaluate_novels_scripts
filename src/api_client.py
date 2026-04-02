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
        max_retries: int = 3,
        thinking_mode: Optional[str] = None,  # 思考模式: enabled/disabled/auto
        reasoning_effort: Optional[str] = None  # 思考深度: minimal/low/medium/high
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
            thinking_mode: 思考模式 (enabled/disabled/auto)
            reasoning_effort: 思考深度 (minimal/low/medium/high)
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

        # 读取思考模式配置
        thinking_mode_env = os.getenv("THINKING_MODE")
        if thinking_mode_env and thinking_mode_env in ["enabled", "disabled", "auto"]:
            self.thinking_mode = thinking_mode_env
        else:
            self.thinking_mode = thinking_mode or "disabled"  # 默认关闭思考模式

        # 读取思考深度配置
        reasoning_effort_env = os.getenv("REASONING_EFFORT")
        if reasoning_effort_env and reasoning_effort_env in ["minimal", "low", "medium", "high"]:
            self.reasoning_effort = reasoning_effort_env
        else:
            self.reasoning_effort = reasoning_effort or None  # 默认不设置

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

        # 添加思考模式参数
        if self.thinking_mode and self.thinking_mode != "disabled":
            thinking_config = {"type": self.thinking_mode}

            # 如果设置了 reasoning_effort，添加到 thinking 配置中
            if self.reasoning_effort:
                thinking_config["reasoning_effort"] = self.reasoning_effort

            payload["thinking"] = thinking_config

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
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"📤 准备发送 API 请求 (JSON模式: {json_mode})")
        logger.info(f"📝 Prompt 长度: {len(prompt)} 字符")

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response_format = {"type": "json_object"} if json_mode else None

        logger.info("⏳ 等待豆包 API 响应...")
        response_data = self._make_request(messages, response_format)
        logger.info("✅ 收到 API 响应")

        try:
            content = response_data["choices"][0]["message"]["content"]
            logger.info(f"📥 响应内容长度: {len(content)} 字符")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"❌ 解析 API 响应失败: {str(e)}")
            raise RuntimeError(f"解析 API 响应失败: {str(e)}")

    def chat_with_json_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_parse_retries: int = 2
    ) -> Dict[str, Any]:
        """
        发送聊天请求并解析 JSON 响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_parse_retries: 解析失败时的最大重试次数

        Returns:
            解析后的 JSON 数据
        """
        import logging
        logger = logging.getLogger(__name__)

        # 添加更强的 JSON 格式要求到系统提示词
        enhanced_system_prompt = """你必须严格按照 JSON 格式返回结果，不要添加任何其他文本或解释。
返回的内容必须是一个完整的 JSON 对象，以 { 开始，以 } 结束。
不要只返回数字、字符串或其他单一值，必须返回完整的 JSON 对象结构。"""

        if system_prompt:
            enhanced_system_prompt = system_prompt + "\n\n" + enhanced_system_prompt

        for retry in range(max_parse_retries):
            try:
                response_text = self.chat(prompt, enhanced_system_prompt, json_mode=True)

                # 记录响应用于调试
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

                # 尝试解析 JSON
                try:
                    parsed = json.loads(cleaned_response)
                except json.JSONDecodeError as e:
                    # 如果 JSON 解析失败，检查是否是单个值（如数字）
                    cleaned_response_stripped = cleaned_response.strip()

                    # 检查是否是单个数字（整数或浮点数）
                    # 先尝试直接转换为数字
                    try:
                        num_value = float(cleaned_response_stripped)
                        # 如果转换成功，说明是单个数字
                        logger.warning(f"⚠️ API 返回了单个数值而非 JSON 对象: {cleaned_response_stripped}")
                        if retry < max_parse_retries - 1:
                            logger.info(f"🔄 重试第 {retry + 1} 次...")
                            time.sleep(1)
                            continue
                        # 返回默认结构
                        return {
                            "dimension": "unknown",
                            "dimension_name": "未知维度",
                            "total_score": num_value,
                            "max_score": 100,
                            "error": "API 返回了单个数值而非 JSON 对象",
                            "raw_value": num_value
                        }
                    except ValueError:
                        # 不是数字，继续其他检查
                        pass

                    # 检查是否是单个字符串
                    if not cleaned_response_stripped.startswith('{') and not cleaned_response_stripped.startswith('['):
                        logger.warning(f"⚠️ API 返回了非 JSON 内容: {cleaned_response_stripped[:100]}")
                        if retry < max_parse_retries - 1:
                            logger.info(f"🔄 重试第 {retry + 1} 次...")
                            time.sleep(1)
                            continue
                        return {
                            "dimension": "unknown",
                            "dimension_name": "未知维度",
                            "total_score": 0,
                            "max_score": 100,
                            "error": f"API 返回了非 JSON 格式内容",
                            "raw_value": cleaned_response_stripped
                        }

                    # 真正的 JSON 解析错误
                    raise RuntimeError(f"解析模型 JSON 响应失败: {str(e)}\n原始响应: {response_text}\n清理后响应: {cleaned_response}")

                # 处理 API 返回 list 的情况（提取第一个元素）
                if isinstance(parsed, list):
                    if len(parsed) > 0:
                        if isinstance(parsed[0], dict):
                            return parsed[0]
                        else:
                            logger.warning(f"⚠️ API 返回了列表，但第一个元素不是字典: {type(parsed[0])}")
                            if retry < max_parse_retries - 1:
                                logger.info(f"🔄 重试第 {retry + 1} 次...")
                                time.sleep(1)
                                continue
                            return {"error": f"API 返回列表，但元素不是字典类型", "raw_value": parsed}
                    else:
                        logger.warning("⚠️ API 返回了空列表")
                        if retry < max_parse_retries - 1:
                            logger.info(f"🔄 重试第 {retry + 1} 次...")
                            time.sleep(1)
                            continue
                        return {"error": "API 返回了空列表", "raw_value": parsed}

                # 处理 API 返回其他类型的情况
                if not isinstance(parsed, dict):
                    logger.warning(f"⚠️ API 返回了非字典类型: {type(parsed).__name__}, 值: {parsed}")
                    if retry < max_parse_retries - 1:
                        logger.info(f"🔄 重试第 {retry + 1} 次...")
                        time.sleep(1)
                        continue
                    return {"error": f"API 返回非字典类型: {type(parsed).__name__}", "raw_value": parsed}

                # 成功返回字典
                return parsed

            except Exception as e:
                if retry == max_parse_retries - 1:
                    raise
                logger.warning(f"⚠️ 处理响应时出错 (第 {retry + 1} 次尝试): {str(e)}")
                time.sleep(1)

        # 理论上不会到达这里
        return {"error": "达到最大重试次数", "raw_value": None}


# 便捷函数
def get_client() -> DoubaoAPIClient:
    """获取配置好的 API 客户端实例"""
    return DoubaoAPIClient()
