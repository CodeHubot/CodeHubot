-- ============================================================================
-- CodeHubot - AIOT管理系统数据库初始化脚本
-- ============================================================================
-- 版本: 2.1
-- 生成日期: 2025-11-26
-- 说明: 本脚本用于初始化 AIOT 管理系统数据库
-- 
-- 使用前请修改:
-- 1. 用户密码 (password_hash)
-- 2. API 密钥 (api_key)
-- 3. 设备密钥 (device_secret)
-- 
-- 规范说明:
-- - 字符集统一使用: utf8mb4_unicode_ci
-- - 布尔值统一使用: tinyint(1)
-- - 时间戳统一使用: CURRENT_TIMESTAMP
-- - UUID统一使用: UUID() 函数生成
-- ============================================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- ============================================================================
-- 1. 核心用户表
-- ============================================================================

CREATE TABLE `aiot_core_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '姓名',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT '用户角色：admin/user',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_username` (`username`),
  KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 插入默认管理员用户 (密码: Admin123$)
INSERT INTO `aiot_core_users` (`id`, `email`, `username`, `name`, `password_hash`, `role`, `is_active`, `last_login`, `created_at`, `updated_at`) VALUES
(1, 'admin@example.com', 'admin', '系统管理员', '$pbkdf2-sha256$29000$BqCUEgIAYIwxRugdAyCEcA$saYHM8J66d.FK1ZMx7sFZf7byo3qnqEnCjy2FP98ilQ', 'admin', 1, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 2. 产品表
-- ============================================================================

CREATE TABLE `aiot_core_products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品代码',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '产品描述',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品分类',
  `sensor_types` json DEFAULT NULL COMMENT '传感器类型配置',
  `control_ports` json DEFAULT NULL COMMENT '控制端口配置',
  `device_capabilities` json DEFAULT NULL COMMENT '设备能力配置',
  `default_device_config` json DEFAULT NULL COMMENT '默认设备配置',
  `communication_protocols` json DEFAULT NULL COMMENT '通信协议',
  `power_requirements` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '电源要求',
  `firmware_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `manufacturer` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商',
  `manufacturer_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商代码',
  `total_devices` int NOT NULL DEFAULT '0' COMMENT '设备总数',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置产品',
  `creator_id` int DEFAULT NULL COMMENT '创建者ID',
  `is_shared` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否共享',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_code` (`product_code`),
  UNIQUE KEY `idx_product_code` (`product_code`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_creator_id` (`creator_id`),
  CONSTRAINT `aiot_core_products_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品表';

-- 插入示例产品
INSERT INTO `aiot_core_products` (`id`, `product_code`, `name`, `description`, `category`, `sensor_types`, `control_ports`, `device_capabilities`, `communication_protocols`, `power_requirements`, `firmware_version`, `hardware_version`, `is_active`, `version`, `manufacturer`, `manufacturer_code`, `total_devices`, `is_system`, `creator_id`, `is_shared`, `created_at`, `updated_at`) VALUES
(1, 'ESP32-S3-Dev-01', 'ESP32-S3开发板', 'ESP32-S3 DevKit开发板，支持DHT11和DS18B20传感器，4个LED，2个继电器，1个舵机，1个PWM输出', 'IoT开发板', 
'{"DHT11_humidity": {"key": "DHT11_humidity", "name": "DHT11湿度传感器", "type": "DHT11", "unit": "%", "range": {"max": 100, "min": 0}, "enabled": true}, "DHT11_temperature": {"key": "DHT11_temperature", "name": "DHT11温度传感器", "type": "DHT11", "unit": "°C", "range": {"max": 80, "min": -40}, "enabled": true}, "DS18B20_temperature": {"key": "DS18B20_temperature", "name": "DS18B20防水温度传感器", "type": "DS18B20", "unit": "°C", "range": {"max": 125, "min": -55}, "enabled": true}}',
'{"led_1": {"key": "led_1", "pin": 42, "name": "LED1", "type": "LED", "enabled": true, "device_id": 1}, "led_2": {"key": "led_2", "pin": 41, "name": "LED2", "type": "LED", "enabled": true, "device_id": 2}, "relay_1": {"key": "relay_1", "pin": 1, "name": "继电器1", "type": "RELAY", "enabled": true, "device_id": 1}, "servo_m1": {"key": "servo_m1", "pin": 48, "name": "舵机M1", "type": "SERVO", "enabled": true, "device_id": 1}}',
'{"ota": true, "mqtt": true, "wifi": true, "sensors": ["DHT11", "DS18B20"], "controls": ["LED", "RELAY", "SERVO", "PWM"]}',
'["WiFi", "MQTT", "HTTP"]', '{"power": "0.5W", "current": "160mA", "voltage": "3.3V"}', '1.0.0', 'ESP32-V2', 1, '1.0', 'ESP', 'ESP', 0, 1, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 3. 设备表
-- ============================================================================

CREATE TABLE `aiot_core_devices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备UUID',
  `device_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `product_id` int DEFAULT NULL COMMENT '产品ID',
  `user_id` int DEFAULT NULL COMMENT '用户ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '设备描述',
  `device_secret` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备密钥',
  `firmware_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `device_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '设备状态: pending/bound/active/offline/error',
  `is_online` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否在线',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `last_seen` datetime DEFAULT NULL COMMENT '最后在线时间',
  `product_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品代码',
  `product_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `last_product_report` datetime DEFAULT NULL COMMENT '最后产品上报时间',
  `product_switch_count` int NOT NULL DEFAULT '0' COMMENT '产品切换次数',
  `auto_created_product` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自动创建产品',
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `mac_address` varchar(17) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MAC地址',
  `location` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置',
  `group_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分组',
  `room` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '房间',
  `floor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '楼层',
  `device_sensor_config` json DEFAULT NULL COMMENT '设备传感器配置',
  `device_control_config` json DEFAULT NULL COMMENT '设备控制配置',
  `device_settings` json DEFAULT NULL COMMENT '设备设置',
  `production_date` date DEFAULT NULL COMMENT '生产日期',
  `serial_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '序列号',
  `quality_grade` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '质量等级',
  `last_heartbeat` datetime DEFAULT NULL COMMENT '最后心跳时间',
  `error_count` int NOT NULL DEFAULT '0' COMMENT '错误次数',
  `last_error` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '最后错误信息',
  `uptime` bigint DEFAULT NULL COMMENT '运行时间(秒)',
  `installation_date` date DEFAULT NULL COMMENT '安装日期',
  `warranty_expiry` date DEFAULT NULL COMMENT '保修到期日',
  `last_maintenance` date DEFAULT NULL COMMENT '最后维护日期',
  `next_maintenance` date DEFAULT NULL COMMENT '下次维护日期',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `device_id` (`device_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_status` (`device_status`),
  KEY `idx_is_online` (`is_online`),
  KEY `idx_mac_address` (`mac_address`),
  CONSTRAINT `aiot_core_devices_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`) ON DELETE SET NULL,
  CONSTRAINT `aiot_core_devices_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备表';

-- 插入测试设备（用于功能测试）
INSERT INTO `aiot_core_devices` (`uuid`, `device_id`, `product_id`, `user_id`, `name`, `description`, `device_secret`, `device_status`, `is_online`, `is_active`, `mac_address`, `created_at`, `updated_at`) VALUES
('test', 'TEST-DEVICE-001', 1, 1, '测试设备', '用于功能测试的虚拟设备，支持所有控制命令', 'REPLACE_WITH_DEVICE_SECRET', 'active', 0, 1, '00:00:00:00:00:00', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 4. LLM提供商表
-- ============================================================================

CREATE TABLE `aiot_llm_providers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商代码',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商名称',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '完整标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '提供商描述',
  `apply_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API申请地址',
  `doc_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文档地址',
  `default_api_base` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '默认API地址',
  `has_free_quota` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否提供免费额度',
  `icon` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图标URL或图标名称',
  `tag_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标签类型',
  `country` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '国家',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序顺序',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  KEY `ix_aiot_llm_providers_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM提供商表';

-- 插入LLM提供商
INSERT INTO `aiot_llm_providers` (`uuid`, `code`, `name`, `title`, `description`, `apply_url`, `doc_url`, `default_api_base`, `has_free_quota`, `tag_type`, `country`, `sort_order`, `is_active`, `created_at`, `updated_at`) VALUES
(UUID(), 'qwen', '通义千问', '阿里云通义千问（模型服务平台百炼）', '阿里云自研的大语言模型，支持中文对话、代码生成、Function Calling 等功能。提供 Turbo、Plus、Max 等多个版本，性能强劲，响应快速。', 'https://dashscope.console.aliyun.com/', 'https://help.aliyun.com/zh/model-studio/qwen-api-reference', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 1, 'primary', 'cn', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(UUID(), 'doubao', '豆包', '火山引擎豆包（字节跳动）', '字节跳动自研的大语言模型，推理能力强，响应快速。支持多种场景应用，包括对话、文本生成、Kimi长文本等。火山引擎方舟平台提供稳定的API服务。', 'https://console.volcengine.com/ark', 'https://www.volcengine.com/docs/82379/1330310', 'https://ark.cn-beijing.volces.com/api/v3', 1, 'success', 'cn', 10, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 5. LLM模型表
-- ============================================================================

CREATE TABLE `aiot_llm_models` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `display_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名称',
  `provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商',
  `model_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '模型类型',
  `api_base` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API基础URL',
  `api_key` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API密钥',
  `api_version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API版本',
  `max_tokens` int DEFAULT NULL COMMENT '最大token数',
  `temperature` decimal(3,2) DEFAULT NULL COMMENT '温度参数',
  `top_p` decimal(3,2) DEFAULT NULL COMMENT 'top_p参数',
  `enable_deep_thinking` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否启用深度思考',
  `frequency_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '频率惩罚参数',
  `presence_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '存在惩罚参数',
  `config` json DEFAULT NULL COMMENT '其他配置参数',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '模型描述',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否默认模型',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序顺序',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  KEY `ix_aiot_llm_models_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM模型表';

-- 插入LLM模型（API密钥需要自行配置）
INSERT INTO `aiot_llm_models` (`uuid`, `name`, `display_name`, `provider`, `model_type`, `api_base`, `api_key`, `max_tokens`, `temperature`, `top_p`, `enable_deep_thinking`, `frequency_penalty`, `presence_penalty`, `config`, `description`, `is_active`, `is_default`, `is_system`, `sort_order`, `created_at`, `updated_at`) VALUES
(UUID(), 'qwen-turbo', '通义千问-Turbo', 'qwen', 'chat', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'YOUR_API_KEY_HERE', 8192, 0.70, 0.90, 0, 0.00, 0.00, NULL, '阿里云通义千问大语言模型，性能强劲，响应快速，适合对话场景', 1, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(UUID(), 'qwen-plus', '通义千问-Plus', 'qwen', 'chat', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'YOUR_API_KEY_HERE', 32768, 0.70, 0.90, 0, 0.00, 0.00, NULL, '阿里云通义千问Plus版本，更强大的理解和生成能力', 1, 0, 1, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 6. 插件表
-- ============================================================================

CREATE TABLE `aiot_plugins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '插件名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '插件描述',
  `openapi_spec` json NOT NULL COMMENT 'OpenAPI 3.0.0 规范（JSON）',
  `user_id` int NOT NULL COMMENT '创建用户 ID',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  KEY `user_id` (`user_id`),
  KEY `ix_aiot_plugins_id` (`id`),
  CONSTRAINT `aiot_plugins_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='插件表';

-- 插入IoT设备控制插件
INSERT INTO `aiot_plugins` (`uuid`, `name`, `description`, `openapi_spec`, `user_id`, `is_active`, `is_system`, `created_at`, `updated_at`) VALUES
(UUID(), 'IoT设备控制', '传感器查询、设备控制（LED/继电器/舵机/PWM）、预设指令', 
'{"openapi": "3.0.0", "info": {"title": "IoT设备控制", "version": "1.2.0", "description": "传感器查询、设备控制（LED/继电器/舵机/PWM）、预设指令"}, "servers": [{"url": "https://plugin.aiot.hello1023.com", "description": "生产服务器"}], "paths": {"/plugin/sensor-data": {"get": {"summary": "查询传感器", "operationId": "getSensorData", "parameters": [{"name": "uuid", "in": "query", "required": true, "description": "UUID", "schema": {"type": "string"}}, {"name": "sensor", "in": "query", "required": true, "description": "传感器类型", "schema": {"type": "string", "enum": ["温度", "湿度", "DS18B20"]}}]}}, "/plugin/control": {"post": {"summary": "控制设备", "operationId": "controlDevice", "requestBody": {"required": true, "content": {"application/json": {"schema": {"type": "object", "required": ["device_uuid", "port_type", "port_id", "action"], "properties": {"device_uuid": {"type": "string"}, "port_type": {"type": "string", "enum": ["led", "relay", "servo", "pwm"]}, "port_id": {"type": "integer"}, "action": {"type": "string", "enum": ["on", "off", "set"]}, "value": {"type": "integer"}}}}}}}}, "/plugin/preset": {"post": {"summary": "执行预设", "operationId": "executePreset", "requestBody": {"required": true, "content": {"application/json": {"schema": {"type": "object", "required": ["device_uuid", "preset_name"], "properties": {"device_uuid": {"type": "string"}, "preset_name": {"type": "string"}, "parameters": {"type": "object"}}}}}}}}}}',
1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 7. 智能体表
-- ============================================================================

CREATE TABLE `aiot_agents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '智能体名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '智能体描述',
  `system_prompt` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '系统提示词',
  `plugin_ids` json DEFAULT NULL COMMENT '关联的插件 ID 列表',
  `llm_model_id` int DEFAULT NULL COMMENT '关联的大模型ID',
  `user_id` int NOT NULL COMMENT '创建用户 ID',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_uuid` (`uuid`),
  KEY `user_id` (`user_id`),
  KEY `ix_aiot_agents_id` (`id`),
  KEY `idx_llm_model_id` (`llm_model_id`),
  CONSTRAINT `aiot_agents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能体表';

-- 插入示例智能体
INSERT INTO `aiot_agents` (`uuid`, `name`, `description`, `system_prompt`, `plugin_ids`, `llm_model_id`, `user_id`, `is_active`, `is_system`, `created_at`, `updated_at`) VALUES
(UUID(), 'IoT助手', 'IoT设备管理助手', '你是一个专业的物联网助手，擅长帮助用户管理和控制智能设备。\n\n你的主要职责包括：\n1. 解答用户关于设备使用的问题\n2. 帮助用户控制智能设备（如开关灯、调节温度等）\n3. 分析传感器数据并提供建议\n4. 设置自动化场景\n\n请用友好、专业的语气与用户交流，并在必要时主动询问以获取更多信息。', '[1]', 1, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- ============================================================================
-- 8. 其他辅助表
-- ============================================================================

-- 访问日志表
CREATE TABLE `aiot_access_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `endpoint` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '访问端点',
  `mac_address` varchar(17) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MAC地址',
  `success` tinyint(1) DEFAULT NULL COMMENT '是否成功',
  `timestamp` datetime DEFAULT NULL COMMENT '时间戳',
  `user_agent` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理',
  PRIMARY KEY (`id`),
  KEY `ix_aiot_access_logs_ip_address` (`ip_address`),
  KEY `ix_aiot_access_logs_timestamp` (`timestamp`),
  KEY `ix_aiot_access_logs_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问日志表';

-- 设备绑定历史表
CREATE TABLE `aiot_device_binding_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mac_address` varchar(17) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备MAC地址',
  `device_uuid` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备UUID',
  `device_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备ID',
  `device_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备名称',
  `user_id` int NOT NULL COMMENT '绑定用户ID',
  `user_email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户邮箱',
  `user_username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户名',
  `product_id` int DEFAULT NULL COMMENT '产品ID',
  `product_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品编码',
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品名称',
  `action` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型：bind/unbind',
  `action_time` datetime NOT NULL COMMENT '操作时间',
  `notes` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '备注信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `ix_device_binding_history_device_uuid` (`device_uuid`),
  KEY `ix_device_binding_history_action_time` (`action_time`),
  KEY `ix_device_binding_history_mac_address` (`mac_address`),
  KEY `ix_device_binding_history_user_id` (`user_id`),
  CONSTRAINT `device_binding_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`),
  CONSTRAINT `device_binding_history_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备绑定历史表';

-- 固件版本表
CREATE TABLE `aiot_core_firmware_versions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品编码',
  `version` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `firmware_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '固件下载地址',
  `file_size` int NOT NULL COMMENT '文件大小(字节)',
  `file_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件哈希值',
  `description` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '描述',
  `release_notes` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布说明',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_latest` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否最新版本',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`),
  KEY `idx_product_code` (`product_code`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='固件版本表';

-- 交互日志表
CREATE TABLE `aiot_interaction_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  `device_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `interaction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交互类型',
  `direction` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据方向：inbound/outbound',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态：success/failed/timeout/pending',
  `data_size` bigint NOT NULL DEFAULT '0' COMMENT '数据大小（字节）',
  `response_time` int DEFAULT NULL COMMENT '响应时间（毫秒）',
  `error_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误代码',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `request_data` json DEFAULT NULL COMMENT '请求数据',
  `response_data` json DEFAULT NULL COMMENT '响应数据',
  `client_ip` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端IP地址',
  `user_agent` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理（User-Agent）',
  `session_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '会话ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_interaction_type` (`interaction_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互日志表';

-- 交互统计表（每日）
CREATE TABLE `aiot_interaction_stats_daily` (
  `date` datetime NOT NULL COMMENT '统计日期',
  `device_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `total_interactions` int NOT NULL DEFAULT '0' COMMENT '总交互次数',
  `successful_interactions` int NOT NULL DEFAULT '0' COMMENT '成功交互次数',
  `failed_interactions` int NOT NULL DEFAULT '0' COMMENT '失败交互次数',
  `avg_response_time` int DEFAULT NULL COMMENT '平均响应时间（毫秒）',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`date`,`device_id`),
  KEY `idx_date` (`date`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互统计表（每日）';

-- 交互统计表（每小时）
CREATE TABLE `aiot_interaction_stats_hourly` (
  `timestamp` datetime NOT NULL COMMENT '统计小时',
  `device_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `interaction_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交互类型',
  `total_count` int NOT NULL DEFAULT '0' COMMENT '总次数',
  `success_count` int NOT NULL DEFAULT '0' COMMENT '成功次数',
  `failed_count` int NOT NULL DEFAULT '0' COMMENT '失败次数',
  `avg_response_time` int DEFAULT NULL COMMENT '平均响应时间（毫秒）',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`timestamp`,`device_id`,`interaction_type`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互统计表（每小时）';

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

-- ============================================================================
-- 初始化完成
-- ============================================================================
-- 说明：
-- 1. 默认管理员用户名: admin, 密码: Admin123$
-- 2. 默认测试设备 UUID: test
-- 3. LLM模型的 API Key 需要在前端管理界面配置
-- 4. 设备密钥 (device_secret) 需要替换为实际值
-- 
-- 数据规范：
-- - 所有表统一使用 utf8mb4_unicode_ci 字符集
-- - 所有布尔值统一使用 tinyint(1) 类型
-- - 所有时间戳统一使用 CURRENT_TIMESTAMP
-- - 所有 UUID 统一使用 UUID() 函数生成
-- - 所有 NOT NULL 字段都有明确的 DEFAULT 值
-- ============================================================================
