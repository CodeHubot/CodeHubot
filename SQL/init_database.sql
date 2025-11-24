-- ============================================================================
-- CodeHubot AI-IoT 智能教学平台 - 数据库初始化SQL脚本
-- 版本: 1.2.0
-- 日期: 2025-11-24
-- 
-- 表命名规范:
--   - 所有表名统一使用 aiot_ 前缀，便于区分不同业务模块的表
--   - 核心表使用 aiot_core_ 前缀，标识为最小系统必需的表
--   - 扩展表使用 aiot_ 前缀 + 模块标识，标识为可选功能表
--   - 使用下划线分隔单词，表名使用复数形式（如 bases, workflows, agents）
--   - 相关表使用模块前缀，便于识别和管理
-- 
-- 核心表 vs 扩展表:
--   - 核心表（aiot_core_*）: 系统运行必需的基础表，最小系统必须包含
--   - 扩展表（aiot_*）: 可选功能表，可根据业务需求选择性部署
-- 
-- 各业务模块表命名示例:
-- 
-- 1. 核心业务表（最小系统必需，使用 aiot_core_ 前缀）:
--    - aiot_core_users              # 用户表（必需：认证和授权）
--    - aiot_core_products           # 产品表（必需：设备需要关联产品）
--    - aiot_core_devices            # 设备表（必需：核心业务实体）
--    - aiot_core_firmware_versions  # 固件版本表（必需：设备需要固件信息）
-- 
--    最小系统表清单（4张核心表）:
--    ✓ aiot_core_users              - 用户认证和授权
--    ✓ aiot_core_products           - 产品定义和管理
--    ✓ aiot_core_devices            - 设备注册和管理
--    ✓ aiot_core_firmware_versions  - 固件版本管理
-- 
-- 2. 扩展业务表（可选功能，使用 aiot_ 前缀）:
--    - aiot_device_binding_history  # 设备绑定历史表（可选：用于审计）
--    - aiot_interaction_logs         # 交互日志表（可选：用于日志记录）
--    - aiot_interaction_stats_hourly # 交互统计表-每小时（可选：用于统计分析）
--    - aiot_interaction_stats_daily  # 交互统计表-每日（可选：用于统计分析）
--    - aiot_device_product_history   # 设备产品切换历史表（可选：用于审计）
-- 
-- 3. 智能体（Agent）相关表（扩展功能，使用 aiot_agent_* 前缀）:
--    - aiot_agents                   # 智能体表
--    - aiot_agent_configs            # 智能体配置表
--    - aiot_agent_conversations      # 智能体对话表
--    - aiot_agent_messages           # 智能体消息表
--    - aiot_agent_tools              # 智能体工具表
--    - aiot_agent_tool_executions    # 智能体工具执行记录表
-- 
-- 4. 知识库（Knowledge Base）相关表（扩展功能，使用 aiot_knowledge_* 前缀）:
--    - aiot_knowledge_bases          # 知识库表
--    - aiot_knowledge_documents      # 知识库文档表
--    - aiot_knowledge_chunks         # 知识库文档分块表
--    - aiot_knowledge_embeddings     # 知识库向量嵌入表
--    - aiot_knowledge_tags           # 知识库标签表
--    - aiot_knowledge_categories     # 知识库分类表
--    - aiot_knowledge_metadata       # 知识库元数据表
--    - aiot_knowledge_sources        # 知识库来源表（如文件、URL等）
-- 
-- 5. 工作流（Workflow）相关表（扩展功能，使用 aiot_workflow_* 前缀）:
--    - aiot_workflows                # 工作流定义表
--    - aiot_workflow_nodes           # 工作流节点表
--    - aiot_workflow_edges           # 工作流边（连接）表
--    - aiot_workflow_executions      # 工作流执行记录表
--    - aiot_workflow_execution_logs  # 工作流执行日志表
--    - aiot_workflow_templates       # 工作流模板表
--    - aiot_workflow_triggers        # 工作流触发器表
--    - aiot_workflow_variables       # 工作流变量表
-- 
-- 6. 大模型配置（LLM）相关表（扩展功能，使用 aiot_llm_* 前缀）:
--    - aiot_llm_providers            # 大模型提供商表（如 OpenAI、Claude、通义千问等）
--    - aiot_llm_models               # 大模型配置表（模型名称、参数配置等）
--    - aiot_llm_api_keys             # 大模型 API 密钥表（加密存储）
--    - aiot_llm_usage_logs           # 大模型使用日志表（记录调用次数、费用等）
--    - aiot_llm_prompts              # 提示词模板表
--    - aiot_llm_prompt_templates     # 提示词模板库表
--    - aiot_llm_configs              # 大模型全局配置表（默认模型、温度等参数）
-- 
-- 7. 插件（Plugin）相关表（扩展功能，使用 aiot_plugin_* 前缀）:
--    - aiot_plugins                  # 插件表（插件基本信息）
--    - aiot_plugin_configs           # 插件配置表（插件参数配置）
--    - aiot_plugin_versions          # 插件版本表（版本管理）
--    - aiot_plugin_installations     # 插件安装记录表（安装状态、安装时间等）
--    - aiot_plugin_executions        # 插件执行记录表（执行日志、结果等）
--    - aiot_plugin_permissions       # 插件权限表（插件所需权限配置）
--    - aiot_plugin_dependencies      # 插件依赖表（插件之间的依赖关系）
--    - aiot_plugin_events            # 插件事件表（插件触发的事件配置）
-- 
-- 8. 团队管理（Team/Organization）相关表（扩展功能，使用 aiot_team_* 前缀）:
--    - aiot_teams                    # 团队表（团队基本信息）
--    - aiot_team_members             # 团队成员表（成员关系、角色等）
--    - aiot_team_roles               # 团队角色表（角色定义、权限等）
--    - aiot_team_permissions         # 团队权限表（权限配置）
--    - aiot_team_invitations         # 团队邀请表（邀请记录、状态等）
--    - aiot_team_devices             # 团队设备关联表（设备归属、共享等）
--    - aiot_team_projects            # 团队项目表（项目信息）
--    - aiot_team_resources           # 团队资源表（资源配额、使用情况等）
--    - aiot_organizations            # 组织表（多级组织架构）
--    - aiot_organization_members     # 组织成员表
-- 
-- 9. 其他扩展业务模块（使用 aiot_* 前缀）:
--    - aiot_notifications            # 通知表
--    - aiot_notification_templates   # 通知模板表
--    - aiot_alerts                   # 告警表
--    - aiot_alert_rules              # 告警规则表
--    - aiot_dashboards               # 仪表盘表
--    - aiot_dashboard_widgets        # 仪表盘组件表
--    - aiot_reports                  # 报表表
--    - aiot_report_templates         # 报表模板表
-- 
-- 命名原则:
--   1. 核心表使用 aiot_core_ 前缀，扩展表使用 aiot_ 前缀
--   2. 使用下划线分隔单词（snake_case）
--   3. 表名使用复数形式（如 bases, workflows, agents）
--   4. 相关表使用模块前缀（如 aiot_knowledge_*, aiot_workflow_*, aiot_agent_*）
--   5. 表名应清晰表达其用途，避免缩写（除非是通用缩写）
--   6. 历史记录表使用 _history 后缀（如 aiot_device_binding_history）
--   7. 统计表使用 _stats 前缀或后缀（如 aiot_interaction_stats_hourly）
--   8. 日志表使用 _logs 后缀（如 aiot_interaction_logs）
-- 
-- 核心表识别标准:
--   - 系统启动和基本功能运行必需的表
--   - 其他表的外键依赖的基础表
--   - 核心业务流程中不可缺失的表
--   - 例如：用户、产品、设备、固件版本等基础实体表
-- 
-- 扩展表识别标准:
--   - 用于审计、日志、统计等辅助功能的表
--   - 历史记录、分析报表等非核心业务表
--   - 可选功能模块相关的表（如智能体、知识库、工作流、大模型配置、插件、团队管理等）
-- 
-- MySQL 版本要求:
--   - 最低版本: MySQL 5.7.8+ (需要支持 JSON 数据类型)
--   - 推荐版本: MySQL 8.0+
--   - 兼容性: 本脚本兼容 MySQL 5.7.8+ 和 8.0+
-- ============================================================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. 创建用户表
-- ============================================================================

CREATE TABLE `aiot_core_users` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `username` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '姓名',
  `password_hash` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `role` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user' COMMENT '用户角色：admin/user',
  `is_active` TINYINT(1) DEFAULT '1' COMMENT '是否激活',
  `last_login` DATETIME DEFAULT NULL COMMENT '最后登录时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_username` (`username`),
  KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================================
-- 2. 创建产品表
-- ============================================================================

CREATE TABLE `aiot_core_products` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `product_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品代码',
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称',
  `description` TEXT COLLATE utf8mb4_unicode_ci COMMENT '产品描述',
  `category` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品分类',
  `sensor_types` JSON DEFAULT NULL COMMENT '传感器类型配置',
  `control_ports` JSON DEFAULT NULL COMMENT '控制端口配置',
  `device_capabilities` JSON DEFAULT NULL COMMENT '设备能力配置',
  `default_device_config` JSON DEFAULT NULL COMMENT '默认设备配置',
  `communication_protocols` JSON DEFAULT NULL COMMENT '通信协议',
  `power_requirements` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '电源要求',
  `firmware_version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `is_active` TINYINT(1) DEFAULT '1' COMMENT '是否激活',
  `version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `manufacturer` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商',
  `manufacturer_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商代码',
  `total_devices` INT(11) DEFAULT '0' COMMENT '设备总数',
  `is_system` TINYINT(1) DEFAULT '0' COMMENT '是否系统内置产品',
  `creator_id` INT(11) DEFAULT NULL COMMENT '创建者ID',
  `is_shared` TINYINT(1) DEFAULT '0' COMMENT '是否共享',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_code` (`product_code`),
  UNIQUE KEY `idx_product_code` (`product_code`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_creator_id` (`creator_id`),
  FOREIGN KEY (`creator_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品表';

-- ============================================================================
-- 3. 创建设备表
-- ============================================================================

CREATE TABLE `aiot_core_devices` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `uuid` VARCHAR(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备UUID',
  `device_id` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `product_id` INT(11) DEFAULT NULL COMMENT '产品ID',
  `user_id` INT(11) DEFAULT NULL COMMENT '用户ID',
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` TEXT COLLATE utf8mb4_unicode_ci COMMENT '设备描述',
  `device_secret` VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备密钥',
  `firmware_version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `device_status` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '设备状态: pending/bound/active/offline/error',
  `is_online` TINYINT(1) DEFAULT '0' COMMENT '是否在线',
  `is_active` TINYINT(1) DEFAULT '1' COMMENT '是否激活',
  `last_seen` DATETIME DEFAULT NULL COMMENT '最后在线时间',
  `product_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品代码',
  `product_version` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `last_product_report` DATETIME DEFAULT NULL COMMENT '最后产品上报时间',
  `product_switch_count` INT(11) DEFAULT '0' COMMENT '产品切换次数',
  `auto_created_product` TINYINT(1) DEFAULT '0' COMMENT '是否自动创建产品',
  `ip_address` VARCHAR(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `mac_address` VARCHAR(17) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MAC地址',
  `location` VARCHAR(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置',
  `group_name` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分组',
  `room` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '房间',
  `floor` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '楼层',
  `device_sensor_config` JSON DEFAULT NULL COMMENT '设备传感器配置',
  `device_control_config` JSON DEFAULT NULL COMMENT '设备控制配置',
  `device_settings` JSON DEFAULT NULL COMMENT '设备设置',
  `production_date` DATE DEFAULT NULL COMMENT '生产日期',
  `serial_number` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '序列号',
  `quality_grade` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '质量等级',
  `last_heartbeat` DATETIME DEFAULT NULL COMMENT '最后心跳时间',
  `error_count` INT(11) DEFAULT '0' COMMENT '错误次数',
  `last_error` TEXT COLLATE utf8mb4_unicode_ci COMMENT '最后错误信息',
  `uptime` BIGINT(20) DEFAULT NULL COMMENT '运行时间(秒)',
  `installation_date` DATE DEFAULT NULL COMMENT '安装日期',
  `warranty_expiry` DATE DEFAULT NULL COMMENT '保修到期日',
  `last_maintenance` DATE DEFAULT NULL COMMENT '最后维护日期',
  `next_maintenance` DATE DEFAULT NULL COMMENT '下次维护日期',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uuid` (`uuid`),
  UNIQUE KEY `device_id` (`device_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_device_status` (`device_status`),
  KEY `idx_is_online` (`is_online`),
  KEY `idx_mac_address` (`mac_address`),
  FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`) ON DELETE SET NULL,
  FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备表';

-- ============================================================================
-- 4. 创建固件版本表
-- ============================================================================

CREATE TABLE `aiot_core_firmware_versions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `product_code` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品编码',
  `version` VARCHAR(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `firmware_url` VARCHAR(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '固件下载地址',
  `file_size` INT(11) NOT NULL COMMENT '文件大小(字节)',
  `file_hash` VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件哈希值',
  `description` VARCHAR(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '描述',
  `release_notes` VARCHAR(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布说明',
  `is_active` TINYINT(1) DEFAULT '1' COMMENT '是否激活',
  `is_latest` TINYINT(1) DEFAULT '0' COMMENT '是否最新版本',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`),
  KEY `idx_product_code` (`product_code`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='固件版本表';

-- ============================================================================
-- 5. 创建设备绑定历史表
-- ============================================================================

CREATE TABLE `aiot_device_binding_history` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `mac_address` VARCHAR(17) NOT NULL COMMENT '设备MAC地址',
  `device_uuid` VARCHAR(36) DEFAULT NULL COMMENT '设备UUID（解绑后可能为空）',
  `device_id` VARCHAR(100) DEFAULT NULL COMMENT '设备ID',
  `device_name` VARCHAR(100) DEFAULT NULL COMMENT '设备名称',
  `user_id` INT(11) NOT NULL COMMENT '绑定用户ID',
  `user_email` VARCHAR(255) DEFAULT NULL COMMENT '用户邮箱（冗余字段，便于查询）',
  `user_username` VARCHAR(50) DEFAULT NULL COMMENT '用户名（冗余字段，便于查询）',
  `product_id` INT(11) DEFAULT NULL COMMENT '产品ID',
  `product_code` VARCHAR(100) DEFAULT NULL COMMENT '产品编码',
  `product_name` VARCHAR(200) DEFAULT NULL COMMENT '产品名称（冗余字段，便于查询）',
  `action` VARCHAR(20) NOT NULL COMMENT '操作类型：bind/unbind',
  `action_time` DATETIME NOT NULL COMMENT '操作时间',
  `notes` TEXT COMMENT '备注信息（如解绑原因等）',
  `created_at` DATETIME DEFAULT NULL COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `ix_device_binding_history_device_uuid` (`device_uuid`),
  KEY `ix_device_binding_history_action_time` (`action_time`),
  KEY `ix_device_binding_history_mac_address` (`mac_address`),
  KEY `ix_device_binding_history_id` (`id`),
  KEY `ix_device_binding_history_user_id` (`user_id`),
  KEY `idx_mac_action_time` (`mac_address`,`action_time`),
  CONSTRAINT `device_binding_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`),
  CONSTRAINT `device_binding_history_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备绑定历史表';

-- ============================================================================
-- 6. 创建交互日志表（根据backend/models/interaction_log.py定义）
-- ============================================================================

CREATE TABLE `aiot_interaction_logs` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  `device_id` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `interaction_type` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交互类型：data_upload/data_download/command/heartbeat/config_update/firmware_update',
  `direction` VARCHAR(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据方向：inbound/outbound',
  `status` VARCHAR(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态：success/failed/timeout/pending',
  `data_size` BIGINT(20) DEFAULT '0' COMMENT '数据大小（字节）',
  `response_time` INT(11) DEFAULT NULL COMMENT '响应时间（毫秒）',
  `error_code` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误代码',
  `error_message` TEXT COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `request_data` JSON DEFAULT NULL COMMENT '请求数据',
  `response_data` JSON DEFAULT NULL COMMENT '响应数据',
  `client_ip` VARCHAR(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '客户端IP地址',
  `user_agent` TEXT COLLATE utf8mb4_unicode_ci COMMENT '用户代理',
  `session_id` VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '会话ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_interaction_type` (`interaction_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互日志表';

-- ============================================================================
-- 7. 创建交互统计表（每小时，根据backend/models/interaction_log.py定义）
-- ============================================================================

CREATE TABLE `aiot_interaction_stats_hourly` (
  `timestamp` DATETIME NOT NULL COMMENT '统计小时',
  `device_id` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `interaction_type` VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交互类型',
  `total_count` INT(11) DEFAULT '0' COMMENT '总次数',
  `success_count` INT(11) DEFAULT '0' COMMENT '成功次数',
  `failed_count` INT(11) DEFAULT '0' COMMENT '失败次数',
  `timeout_count` INT(11) DEFAULT '0' COMMENT '超时次数',
  `avg_response_time` INT(11) DEFAULT NULL COMMENT '平均响应时间（毫秒）',
  `max_response_time` INT(11) DEFAULT NULL COMMENT '最大响应时间（毫秒）',
  `min_response_time` INT(11) DEFAULT NULL COMMENT '最小响应时间（毫秒）',
  `total_data_size` BIGINT(20) DEFAULT '0' COMMENT '总数据量（字节）',
  `avg_data_size` BIGINT(20) DEFAULT '0' COMMENT '平均数据量（字节）',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`timestamp`, `device_id`, `interaction_type`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互统计表（每小时）';

-- ============================================================================
-- 8. 创建交互统计表（每日，根据backend/models/interaction_log.py定义）
-- ============================================================================

CREATE TABLE `aiot_interaction_stats_daily` (
  `date` DATETIME NOT NULL COMMENT '统计日期',
  `device_id` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `total_interactions` INT(11) DEFAULT '0' COMMENT '总交互次数',
  `successful_interactions` INT(11) DEFAULT '0' COMMENT '成功交互次数',
  `failed_interactions` INT(11) DEFAULT '0' COMMENT '失败交互次数',
  `data_upload_count` INT(11) DEFAULT '0' COMMENT '数据上传次数',
  `data_download_count` INT(11) DEFAULT '0' COMMENT '数据下载次数',
  `command_count` INT(11) DEFAULT '0' COMMENT '命令次数',
  `heartbeat_count` INT(11) DEFAULT '0' COMMENT '心跳次数',
  `avg_response_time` INT(11) DEFAULT NULL COMMENT '平均响应时间（毫秒）',
  `total_data_transferred` BIGINT(20) DEFAULT '0' COMMENT '总传输数据量（字节）',
  `online_duration` INT(11) DEFAULT '0' COMMENT '在线时长（分钟）',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`date`, `device_id`),
  KEY `idx_date` (`date`),
  KEY `idx_device_id` (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交互统计表（每日）';

-- ============================================================================
-- 9. 插入初始数据
-- ============================================================================

-- 9.1 插入管理员用户
-- 密码: admin123 (使用 pbkdf2-sha256 加密)
INSERT INTO `aiot_core_users` (`id`, `email`, `username`, `name`, `password_hash`, `role`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'admin@aiot.com', 'admin', '系统管理员', '$pbkdf2-sha256$29000$dK6Vcm4tReg9B0DImTMmRA$sxi6IZom9C17tDagKrVkE/4PBVBLClSBZDdSGVmystM', 'admin', 1, NOW(), NOW());

-- 9.2 插入产品信息（ESP32-S3开发板）
INSERT INTO `aiot_core_products` (
  `id`,
  `product_code`,
  `name`,
  `description`,
  `category`,
  `sensor_types`,
  `control_ports`,
  `device_capabilities`,
  `default_device_config`,
  `communication_protocols`,
  `power_requirements`,
  `firmware_version`,
  `hardware_version`,
  `is_active`,
  `version`,
  `manufacturer`,
  `manufacturer_code`,
  `total_devices`,
  `is_system`,
  `creator_id`,
  `is_shared`,
  `created_at`,
  `updated_at`
) VALUES (
  1,
  'ESP32-S3-Dev-01',
  'ESP32-S3开发板',
  'ESP32-S3 DevKit开发板，支持DHT11和DS18B20传感器，4个LED，2个继电器，1个舵机，1个PWM输出',
  'IoT开发板',
  '{"DHT11_humidity": {"key": "DHT11_humidity", "name": "DHT11湿度传感器", "type": "DHT11", "unit": "%", "range": {"max": 100, "min": 0}, "enabled": true, "accuracy": 1, "data_field": "humidity"}, "DHT11_temperature": {"key": "DHT11_temperature", "name": "DHT11温度传感器", "type": "DHT11", "unit": "°C", "range": {"max": 80, "min": -40}, "enabled": true, "accuracy": 0.1, "data_field": "temperature"}, "DS18B20_temperature": {"key": "DS18B20_temperature", "name": "DS18B20防水温度传感器", "type": "DS18B20", "unit": "°C", "range": {"max": 125, "min": -55}, "enabled": true, "accuracy": 0.1, "data_field": "temperature"}}',
  '{"led_1": {"key": "led_1", "pin": 42, "name": "LED1", "type": "LED", "enabled": true, "device_id": 1, "description": "板载LED1"}, "led_2": {"key": "led_2", "pin": 41, "name": "LED2", "type": "LED", "enabled": true, "device_id": 2, "description": "板载LED2"}, "led_3": {"key": "led_3", "pin": 37, "name": "LED3", "type": "LED", "enabled": true, "device_id": 3, "description": "板载LED3"}, "led_4": {"key": "led_4", "pin": 36, "name": "LED4", "type": "LED", "enabled": true, "device_id": 4, "description": "板载LED4"}, "pwm_m2": {"key": "pwm_m2", "pin": 40, "name": "PWM输出M2", "type": "PWM", "enabled": true, "device_id": 2, "description": "PWM输出端口2", "frequency_range": {"max": 5000, "min": 100}, "duty_cycle_range": {"max": 100, "min": 0}}, "relay_1": {"key": "relay_1", "pin": 1, "name": "继电器1", "type": "RELAY", "enabled": true, "device_id": 1, "description": "继电器通道1"}, "relay_2": {"key": "relay_2", "pin": 2, "name": "继电器2", "type": "RELAY", "enabled": true, "device_id": 2, "description": "继电器通道2"}, "servo_m1": {"key": "servo_m1", "pin": 48, "name": "舵机M1", "type": "SERVO", "enabled": true, "device_id": 1, "angle_range": {"max": 180, "min": 0}, "description": "舵机电机1"}}',
  '{"ota": true, "mqtt": true, "wifi": true, "sensors": ["DHT11", "DS18B20"], "controls": ["LED", "RELAY", "SERVO", "PWM"]}',
  NULL,
  '["WiFi", "MQTT", "HTTP"]',
  '{"power": "0.5W", "current": "160mA", "voltage": "3.3V"}',
  '1.0.0',
  'ESP32-V2',
  1,
  '1.0',
  'ESP',
  'ESP',
  0,
  1,
  1,
  0,
  NOW(),
  NOW()
);

-- ============================================================================
-- 7. 创建插件表（AI 扩展功能）
-- ============================================================================

CREATE TABLE IF NOT EXISTS `aiot_plugins` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '插件名称',
  `description` TEXT COLLATE utf8mb4_unicode_ci COMMENT '插件描述',
  `openapi_spec` JSON NOT NULL COMMENT 'OpenAPI 3.0.0 规范（JSON）',
  `user_id` INT(11) NOT NULL COMMENT '创建用户 ID',
  `is_active` INT(11) DEFAULT '1' COMMENT '是否激活（1=激活，0=禁用）',
  `is_system` INT(11) DEFAULT '0' COMMENT '是否系统内置（1=是，0=否）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_is_system` (`is_system`),
  CONSTRAINT `fk_plugin_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI插件表（扩展功能）';

-- ============================================================================
-- 8. 创建智能体表（AI 扩展功能）
-- ============================================================================

CREATE TABLE IF NOT EXISTS `aiot_agents` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '智能体名称',
  `description` TEXT COLLATE utf8mb4_unicode_ci COMMENT '智能体描述',
  `system_prompt` TEXT COLLATE utf8mb4_unicode_ci COMMENT '系统提示词',
  `plugin_ids` JSON DEFAULT NULL COMMENT '关联的插件 ID 列表',
  `user_id` INT(11) NOT NULL COMMENT '创建用户 ID',
  `is_active` INT(11) DEFAULT '1' COMMENT '是否激活（1=激活，0=禁用）',
  `is_system` INT(11) DEFAULT '0' COMMENT '是否系统内置（1=是，0=否）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_is_system` (`is_system`),
  CONSTRAINT `fk_agent_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体表（扩展功能）';

-- ============================================================================
-- 10. 恢复外键检查
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 初始化完成
-- ============================================================================

-- 默认管理员账号：
--   邮箱: admin@aiot.com
--   用户名: admin
--   密码: admin123

-- 默认产品：
--   产品编码: ESP32-S3-Dev-01
--   产品名称: ESP32-S3开发板
--   包含传感器: DHT11温湿度传感器、DS18B20防水温度传感器
--   包含控制: 4个LED、2个继电器、1个舵机、1个PWM输出

-- 使用说明：
--   1. 请先创建数据库：CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   2. 使用数据库：USE aiot_admin;
--   3. 执行此脚本：mysql -u root -p aiot_admin < init_database.sql
--   4. 字符集：utf8mb4
