"""
大模型调用服务
支持多种国产和国际大模型
"""

import json
import requests
import logging
from typing import List, Dict, Any, Optional
from app.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class LLMService:
    """大模型调用服务基类"""
    
    def __init__(self, model: LLMModel):
        self.model = model
        self.api_base = model.api_base
        self.api_key = model.api_key
        self.model_name = model.name
        self.temperature = float(model.temperature) if model.temperature else 0.7
        self.max_tokens = model.max_tokens or 4096
        self.top_p = float(model.top_p) if model.top_p else 0.9
    
    def _log_request_details(self, provider: str, url: str, payload: Dict, functions: Optional[List[Dict]] = None):
        """统一的请求日志输出"""
        logger.info("=" * 80)
        logger.info(f"🤖 调用大模型 API - {provider}")
        logger.info("=" * 80)
        logger.info(f"📍 URL: {url}")
        logger.info(f"🏷️  Provider: {provider}")
        logger.info(f"🎯 Model: {self.model_name}")
        
        # API Key (脱敏显示)
        masked_key = f"{self.api_key[:10]}...{self.api_key[-4:]}" if self.api_key and len(self.api_key) > 14 else "***"
        logger.info(f"🔑 API Key: {masked_key}")
        
        # 参数配置
        logger.info(f"⚙️  Temperature: {payload.get('temperature', self.temperature)}")
        logger.info(f"⚙️  Max Tokens: {payload.get('max_tokens', self.max_tokens)}")
        logger.info(f"⚙️  Top P: {payload.get('top_p', self.top_p)}")
        
        # 消息内容
        messages = payload.get('messages', [])
        logger.info(f"💬 Messages Count: {len(messages)}")
        logger.info("📝 Messages Detail:")
        for i, msg in enumerate(messages, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '') or ''  # 确保不为 None
            # 安全处理 content
            if content:
                content_preview = content[:200] + '...' if len(content) > 200 else content
            else:
                content_preview = '[空内容]'
            logger.info(f"   [{i}] Role: {role}")
            logger.info(f"       Content: {content_preview}")
        
        # Functions (工具)
        if functions:
            logger.info(f"🔧 Functions/Tools: {len(functions)} 个")
            logger.info("📋 Functions Detail:")
            for i, func in enumerate(functions, 1):
                func_name = func.get('name', 'unknown') or 'unknown'
                func_desc = func.get('description', 'N/A') or 'N/A'
                logger.info(f"   [{i}] {func_name}: {func_desc}")
                
                # 打印参数定义
                if 'parameters' in func:
                    params = func['parameters']
                    if 'properties' in params:
                        logger.info(f"       参数:")
                        for param_name, param_def in params['properties'].items():
                            param_type = param_def.get('type', 'unknown') or 'unknown'
                            param_desc = param_def.get('description', 'N/A') or 'N/A'
                            required = '必填' if param_name in params.get('required', []) else '可选'
                            logger.info(f"         - {param_name} ({param_type}, {required}): {param_desc}")
            
            # Tool choice
            if 'tool_choice' in payload:
                logger.info(f"🎯 Tool Choice: {payload['tool_choice']}")
            elif 'function_call' in payload:
                logger.info(f"🎯 Function Call: {payload['function_call']}")
        else:
            logger.info("🔧 Functions/Tools: 无")
        
        # 完整 Payload (JSON 格式)
        logger.info("📦 完整请求 Payload:")
        try:
            payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
            logger.info(payload_json)
        except Exception as e:
            logger.error(f"   无法序列化 payload: {e}")
        
        logger.info("=" * 80)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求到大模型
        
        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            functions: 可用的函数列表（用于 Function Calling）
            function_call: 是否强制调用函数 ("auto", "none", {"name": "function_name"})
        
        Returns:
            {"response": "回复内容", "function_call": {...}}
        """
        provider = self.model.provider.lower()
        
        if provider == 'openai':
            return self._call_openai_api(messages, functions, function_call)
        elif provider == 'qwen':
            return self._call_qwen_api(messages, functions, function_call)
        elif provider == 'wenxin':
            return self._call_wenxin_api(messages, functions, function_call)
        elif provider == 'spark':
            return self._call_spark_api(messages, functions, function_call)
        elif provider == 'zhipu':
            return self._call_zhipu_api(messages, functions, function_call)
        elif provider == 'moonshot':
            return self._call_moonshot_api(messages, functions, function_call)
        elif provider == 'deepseek':
            return self._call_deepseek_api(messages, functions, function_call)
        elif provider == 'doubao':
            return self._call_doubao_api(messages, functions, function_call)
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def _call_openai_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用 OpenAI API"""
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(self.temperature) if self.temperature else 0.7,
            "max_tokens": int(self.max_tokens) if self.max_tokens else 2000,
            "top_p": float(self.top_p) if self.top_p else 0.9
        }
        
        if functions:
            payload["functions"] = functions
            payload["function_call"] = function_call or "auto"
        
        # 打印详细请求日志
        self._log_request_details("OpenAI", url, payload, functions)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # 打印响应状态
        logger.info(f"📡 响应状态码: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"❌ API 调用失败: {response.text}")
        
        response.raise_for_status()
        
        result = response.json()
        choice = result["choices"][0]
        message = choice["message"]
        
        output = {}
        if message.get("content"):
            output["response"] = message["content"]
            logger.info(f"✅ 响应内容: {message['content'][:200]}...")
        if message.get("function_call"):
            output["function_call"] = {
                "name": message["function_call"]["name"],
                "arguments": json.loads(message["function_call"]["arguments"])
            }
            logger.info(f"🔧 Function Call: {message['function_call']['name']}")
            logger.info(f"📝 Arguments: {json.dumps(output['function_call']['arguments'], ensure_ascii=False)}")
        
        return output
    
    def _call_qwen_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用阿里通义千问 API（兼容 OpenAI 格式）"""
        # 通义千问使用 DashScope SDK，这里使用 OpenAI 兼容接口
        # 自动修正旧的 API Base URL
        api_base = self.api_base or 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        if 'dashscope.aliyuncs.com/api/' in api_base:
            # 自动替换为兼容模式
            api_base = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        url = f"{api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(self.temperature) if self.temperature else 0.7,
            "max_tokens": int(self.max_tokens) if self.max_tokens else 2000,
            "top_p": float(self.top_p) if self.top_p else 0.9
        }
        
        if functions:
            # 通义千问支持 Function Calling
            payload["tools"] = [{"type": "function", "function": func} for func in functions]
            if function_call and function_call != "none":
                payload["tool_choice"] = "auto"
        
        # 打印详细请求日志
        self._log_request_details("Qwen (通义千问)", url, payload, functions)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # 打印响应状态
        logger.info(f"📡 响应状态码: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"❌ API 调用失败: {response.text}")
        
        response.raise_for_status()
        
        result = response.json()
        choice = result["choices"][0]
        message = choice["message"]
        
        output = {}
        if message.get("content"):
            output["response"] = message["content"]
            logger.info(f"✅ 响应内容: {message['content'][:200]}...")
        
        # 添加 token 使用量信息
        if "usage" in result:
            output["usage"] = result["usage"]
            logger.info(f"📊 Token使用: {json.dumps(result['usage'], ensure_ascii=False)}")
        
        if message.get("tool_calls"):
            # 转换为标准格式
            tool_call = message["tool_calls"][0]
            output["function_call"] = {
                "name": tool_call["function"]["name"],
                "arguments": json.loads(tool_call["function"]["arguments"])
            }
            logger.info(f"🔧 Tool Call: {tool_call['function']['name']}")
            logger.info(f"📝 Arguments: {json.dumps(output['function_call']['arguments'], ensure_ascii=False)}")
        
        return output
    
    def _call_wenxin_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用百度文心一言 API"""
        # 文心一言需要先获取 access_token
        # 简化实现：假设 api_key 是 access_token
        url = f"{self.api_base or 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat'}/{self.model_name}"
        
        payload = {
            "messages": messages,
            "temperature": float(self.temperature) if self.temperature else 0.7,
            "top_p": float(self.top_p) if self.top_p else 0.9
        }
        
        if functions:
            payload["functions"] = functions
        
        params = {"access_token": self.api_key}
        
        response = requests.post(url, json=payload, params=params, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        output = {"response": result.get("result", "")}
        
        if result.get("function_call"):
            output["function_call"] = {
                "name": result["function_call"]["name"],
                "arguments": json.loads(result["function_call"]["arguments"])
            }
        
        return output
    
    def _call_spark_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用讯飞星火 API"""
        # 星火认知大模型需要 WebSocket 连接，这里简化实现
        # 实际使用应该使用官方 SDK
        raise NotImplementedError("讯飞星火 API 需要使用 WebSocket，请使用官方 SDK")
    
    def _call_zhipu_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用智谱 GLM API（兼容 OpenAI 格式）"""
        url = f"{self.api_base or 'https://open.bigmodel.cn/api/paas/v4'}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": float(self.temperature) if self.temperature else 0.7,
            "max_tokens": int(self.max_tokens) if self.max_tokens else 2000,
            "top_p": float(self.top_p) if self.top_p else 0.9
        }
        
        if functions:
            payload["tools"] = [{"type": "function", "function": func} for func in functions]
            if function_call and function_call != "none":
                payload["tool_choice"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        choice = result["choices"][0]
        message = choice["message"]
        
        output = {}
        if message.get("content"):
            output["response"] = message["content"]
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            output["function_call"] = {
                "name": tool_call["function"]["name"],
                "arguments": json.loads(tool_call["function"]["arguments"])
            }
        
        return output
    
    def _call_moonshot_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用月之暗面 Kimi API（兼容 OpenAI 格式）"""
        return self._call_openai_api(messages, functions, function_call)
    
    def _call_deepseek_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用 DeepSeek API（兼容 OpenAI 格式）"""
        return self._call_openai_api(messages, functions, function_call)
    
    def _call_doubao_api(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用火山引擎豆包 API（OpenAI 兼容接口）"""
        # 火山引擎方舟平台使用 OpenAI 兼容的 API
        # API Base: https://ark.cn-beijing.volces.com/api/v3
        # 完整路径: https://ark.cn-beijing.volces.com/api/v3/chat/completions
        
        api_base = self.model.api_base or 'https://ark.cn-beijing.volces.com/api/v3'
        
        # 统一处理 API Base，确保没有尾部斜杠
        api_base = api_base.rstrip('/')
        
        # 构建完整 URL
        url = f"{api_base}/chat/completions"
        
        payload = {
            "model": self.model.name,
            "messages": messages,
            "temperature": float(self.model.temperature) if self.model.temperature else 0.7,
            "max_tokens": int(self.model.max_tokens) if self.model.max_tokens else 2000,
            "top_p": float(self.model.top_p) if self.model.top_p else 0.9
        }
        
        if functions:
            # 豆包支持 Function Calling，使用 tools 格式（OpenAI 新格式）
            payload["tools"] = [{"type": "function", "function": func} for func in functions]
            if function_call and function_call != "none":
                payload["tool_choice"] = "auto"
        
        # 打印详细请求日志
        self._log_request_details("Doubao (豆包)", url, payload, functions)
        
        headers = {
            "Authorization": f"Bearer {self.model.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            # 打印响应状态
            logger.info(f"📡 响应状态码: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"❌ API 调用失败:")
                logger.error(f"  Status Code: {response.status_code}")
                logger.error(f"  Response Headers: {dict(response.headers)}")
                logger.error(f"  Response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            choice = result["choices"][0]
            message = choice["message"]
            
            output = {}
            if message.get("content"):
                output["response"] = message["content"]
                logger.info(f"✅ 响应内容: {message['content'][:200]}...")
            
            # 添加 token 使用量信息
            if "usage" in result:
                output["usage"] = result["usage"]
                logger.info(f"📊 Token使用: {json.dumps(result['usage'], ensure_ascii=False)}")
            
            if message.get("tool_calls"):
                # 转换为标准格式
                tool_call = message["tool_calls"][0]
                output["function_call"] = {
                    "name": tool_call["function"]["name"],
                    "arguments": json.loads(tool_call["function"]["arguments"])
                }
                logger.info(f"🔧 Tool Call: {tool_call['function']['name']}")
                logger.info(f"📝 Arguments: {json.dumps(output['function_call']['arguments'], ensure_ascii=False)}")
            
            return output
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 请求异常:")
            logger.error(f"  Error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"  Response Text: {e.response.text}")
            raise


def create_llm_service(model: LLMModel) -> LLMService:
    """创建 LLM 服务实例"""
    return LLMService(model)

