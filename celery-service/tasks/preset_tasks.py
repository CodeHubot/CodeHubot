"""
预设指令序列 Celery 任务
异步执行预设序列，不阻塞HTTP请求
"""
import sys
from pathlib import Path
import time
import json
import logging

# 确保可以导入backend模块
backend_dir = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name='execute_preset_sequence',
    bind=True,
    max_retries=3,
    default_retry_delay=5
)
def execute_preset_sequence_task(self, device_uuid: str, steps: list):
    """
    执行预设指令序列 - Celery异步任务
    
    Args:
        device_uuid: 设备UUID
        steps: 指令步骤列表，每个步骤包含：
            - command: 控制命令字典
            - delay: 延迟时间（秒）
    
    Returns:
        dict: 执行结果
    
    Example:
        steps = [
            {"command": {"cmd": "led", "device_id": 1, "action": "on"}, "delay": 0},
            {"command": {"cmd": "led", "device_id": 1, "action": "off"}, "delay": 5}
        ]
    """
    logger.info(f"开始执行预设序列任务: device={device_uuid}, task_id={self.request.id}, steps={len(steps)}")
    
    # 导入MQTT服务（延迟导入，确保环境加载）
    try:
        from app.services.mqtt_service import mqtt_service
    except ImportError as e:
        logger.error(f"无法导入mqtt_service: {e}")
        # 尝试创建本地MQTT客户端
        mqtt_service = None
    
    if not mqtt_service:
        error_msg = "MQTT服务未初始化"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "device_uuid": device_uuid
        }
    
    # 检查MQTT连接
    if not mqtt_service.client or not mqtt_service.is_connected:
        # 尝试连接
        try:
            mqtt_service.start()
            time.sleep(2)  # 等待连接
        except Exception as e:
            logger.error(f"MQTT连接失败: {e}")
    
    if not mqtt_service.client or not mqtt_service.is_connected:
        error_msg = "MQTT服务未连接"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "device_uuid": device_uuid
        }
    
    control_topic = f"devices/{device_uuid}/control"
    executed_steps = []
    errors = []
    
    try:
        for index, step in enumerate(steps, 1):
            # 更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': index,
                    'total': len(steps),
                    'status': f'执行步骤 {index}/{len(steps)}'
                }
            )
            
            # 获取控制命令
            command = step.get("command")
            if not command:
                error_msg = f"步骤 {index} 缺少 command 字段"
                logger.error(error_msg)
                errors.append({"step": index, "error": error_msg})
                executed_steps.append({
                    "step": index,
                    "status": "failed",
                    "error": error_msg
                })
                continue
            
            # 转换命令格式（与preset_sequence_service保持一致）
            converted_command = command.copy()
            cmd_type = converted_command.get("cmd")
            
            if cmd_type in ["led", "relay"]:
                # 转换 value 为 action
                if "value" in converted_command:
                    value = converted_command.pop("value")
                    if value == 1 or value == True:
                        converted_command["action"] = "on"
                    elif value == 0 or value == False:
                        converted_command["action"] = "off"
                    else:
                        converted_command["action"] = "on"
                converted_command.pop("device_type", None)
                
            elif cmd_type == "servo":
                converted_command.pop("device_type", None)
                
            elif cmd_type == "pwm":
                if "device_id" in converted_command:
                    converted_command["channel"] = converted_command.pop("device_id")
                if "duty" in converted_command:
                    converted_command["duty_cycle"] = converted_command.pop("duty")
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
                    
                    # 获取延迟时间
                    delay = step.get("delay", 0)
                    
                    executed_steps.append({
                        "step": index,
                        "command": converted_command,
                        "delay": delay,
                        "status": "success"
                    })
                    
                    # 如果不是最后一步，执行延迟
                    if index < len(steps) and delay > 0:
                        logger.info(f"⏳ 步骤 {index} 执行完成，等待 {delay} 秒...")
                        time.sleep(delay)  # 在Celery Worker中可以安全使用time.sleep
                else:
                    error_msg = f"MQTT消息发送失败，rc={result.rc}"
                    logger.error(f"❌ 步骤 {index} {error_msg}")
                    errors.append({"step": index, "error": error_msg})
                    executed_steps.append({
                        "step": index,
                        "command": converted_command,
                        "delay": step.get("delay", 0),
                        "status": "failed",
                        "error": error_msg
                    })
                    
            except Exception as e:
                error_msg = f"执行失败: {str(e)}"
                logger.error(f"❌ 步骤 {index} {error_msg}", exc_info=True)
                errors.append({"step": index, "error": error_msg})
                executed_steps.append({
                    "step": index,
                    "command": converted_command,
                    "delay": step.get("delay", 0),
                    "status": "failed",
                    "error": error_msg
                })
        
        # 统计结果
        success_count = sum(1 for s in executed_steps if s.get("status") == "success")
        failed_count = len(executed_steps) - success_count
        
        result = {
            "success": failed_count == 0,
            "message": f"序列执行完成: {success_count} 成功, {failed_count} 失败",
            "device_uuid": device_uuid,
            "total_steps": len(steps),
            "executed_steps": executed_steps,
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors if errors else None
        }
        
        logger.info(f"预设序列任务完成: {result['message']}")
        return result
        
    except Exception as e:
        error_msg = f"执行预设指令序列失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 返回失败结果
        return {
            "success": False,
            "error": error_msg,
            "device_uuid": device_uuid,
            "executed_steps": executed_steps
        }

