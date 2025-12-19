"""
预设指令序列执行服务
支持多指令配合执行，如LED打开后延迟5秒再关闭
"""
import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional
import paho.mqtt.client as mqtt
from app.core.config import settings

logger = logging.getLogger(__name__)


class PresetSequenceService:
    """预设指令序列执行服务"""
    
    @staticmethod
    async def execute_sequence(
        device_uuid: str,
        steps: List[Dict[str, Any]],
        db_session=None
    ) -> Dict[str, Any]:
        """
        执行预设指令序列
        
        Args:
            device_uuid: 设备UUID
            steps: 指令步骤列表，每个步骤包含：
                - command: 控制命令字典
                - delay: 延迟时间（秒），可选，默认0
            db_session: 数据库会话（可选）
            
        Returns:
            执行结果字典
            
        Example:
            steps = [
                {"command": {"cmd": "led", "device_id": 1, "value": 1}, "delay": 0},
                {"command": {"cmd": "led", "device_id": 1, "value": 0}, "delay": 5}
            ]
        """
        if not steps:
            raise ValueError("指令序列不能为空")
        
        if not mqtt_service.client or not mqtt_service.is_connected:
            raise RuntimeError("MQTT服务未连接")
        
        control_topic = f"devices/{device_uuid}/control"
        executed_steps = []
        errors = []
        
        try:
            for index, step in enumerate(steps, 1):
                # 获取控制命令
                command = step.get("command")
                if not command:
                    error_msg = f"步骤 {index} 缺少 command 字段"
                    logger.error(error_msg)
                    errors.append({"step": index, "error": error_msg})
                    continue
                
                # 转换命令格式为固件期望的格式
                # 固件期望：LED/继电器使用 action 字段（"on"/"off"），而不是 value 字段（1/0）
                converted_command = command.copy()
                cmd_type = converted_command.get("cmd")
                
                if cmd_type in ["led", "relay"]:
                    # 如果有 value 字段，转换为 action 字段
                    if "value" in converted_command:
                        value = converted_command.pop("value")
                        if value == 1 or value == True:
                            converted_command["action"] = "on"
                        elif value == 0 or value == False:
                            converted_command["action"] = "off"
                        else:
                            # 其他值也转换为 on
                            converted_command["action"] = "on"
                    # 如果已经有 action 字段，保持不变
                    # 移除 device_type 字段（固件不需要）
                    converted_command.pop("device_type", None)
                elif cmd_type == "servo":
                    # 舵机命令：保持 angle 字段，移除 device_type
                    converted_command.pop("device_type", None)
                elif cmd_type == "pwm":
                    # PWM命令：固件期望 'channel' 而不是 'device_id'
                    if "device_id" in converted_command:
                        converted_command["channel"] = converted_command.pop("device_id")
                    # 固件期望 'duty_cycle' 而不是 'duty'
                    if "duty" in converted_command:
                        converted_command["duty_cycle"] = converted_command.pop("duty")
                    # 移除 device_type
                    converted_command.pop("device_type", None)
                
                # 发送MQTT消息
                try:
                    message = json.dumps(converted_command)
                    result = mqtt_service.client.publish(control_topic, message, qos=1)
                    
                    if result.rc == 0:
                        logger.info(
                            f"✅ 步骤 {index}/{len(steps)} 执行成功 - "
                            f"设备: {device_uuid}, 命令: {converted_command}"
                        )
                        
                        # 获取延迟时间（秒）- 执行完当前步骤后等待的时间
                        delay = step.get("delay", 0)
                        
                        executed_steps.append({
                            "step": index,
                            "command": converted_command,
                            "delay": delay,
                            "status": "success"
                        })
                        
                        # 如果不是最后一步，执行延迟（执行完当前步骤后等待）
                        if index < len(steps) and delay > 0:
                            logger.info(f"⏳ 步骤 {index} 执行完成，等待 {delay} 秒后执行下一步...")
                            await asyncio.sleep(delay)
                    else:
                        error_msg = f"步骤 {index} MQTT消息发送失败"
                        logger.error(error_msg)
                        errors.append({"step": index, "error": error_msg})
                        executed_steps.append({
                            "step": index,
                            "command": converted_command,
                            "delay": step.get("delay", 0),
                            "status": "failed",
                            "error": error_msg
                        })
                        
                except Exception as e:
                    error_msg = f"步骤 {index} 执行失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append({"step": index, "error": error_msg})
                    executed_steps.append({
                        "step": index,
                        "command": converted_command,
                        "delay": step.get("delay", 0),
                        "status": "failed",
                        "error": error_msg
                    })
            
            # 返回执行结果
            success_count = sum(1 for s in executed_steps if s.get("status") == "success")
            failed_count = len(executed_steps) - success_count
            
            return {
                "success": failed_count == 0,
                "message": f"序列执行完成: {success_count} 成功, {failed_count} 失败",
                "device_uuid": device_uuid,
                "total_steps": len(steps),
                "executed_steps": executed_steps,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"执行预设指令序列失败: {e}", exc_info=True)
            raise RuntimeError(f"执行预设指令序列失败: {str(e)}")
    
    @staticmethod
    def parse_sequence_preset(preset_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析序列类型的预设指令
        
        Args:
            preset_data: 预设指令数据，包含 steps 字段
            
        Returns:
            步骤列表
            
        Example preset_data:
            {
                "type": "sequence",
                "steps": [
                    {"command": {"cmd": "led", "device_id": 1, "value": 1}, "delay": 0},
                    {"command": {"cmd": "led", "device_id": 1, "value": 0}, "delay": 5}
                ]
            }
        """
        if preset_data.get("type") != "sequence":
            raise ValueError("预设指令类型必须是 'sequence'")
        
        steps = preset_data.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("steps 必须是非空列表")
        
        # 验证每个步骤
        parsed_steps = []
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                raise ValueError(f"步骤 {index} 必须是字典类型")
            
            if "command" not in step:
                raise ValueError(f"步骤 {index} 缺少 command 字段")
            
            delay = step.get("delay", 0)
            if not isinstance(delay, (int, float)) or delay < 0:
                raise ValueError(f"步骤 {index} 的 delay 必须是非负数")
            
            parsed_steps.append({
                "command": step["command"],
                "delay": float(delay)
            })
        
        return parsed_steps


# 创建单例
preset_sequence_service = PresetSequenceService()

