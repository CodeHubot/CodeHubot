-- ==========================================================================================================
-- CodeHubot 系统数据库初始化脚本
-- ==========================================================================================================
-- 
-- 脚本名称: init_database.sql
-- 脚本版本: 2.0.0
-- 数据库版本: 2.0
-- 创建日期: 2025-01-01
-- 最后更新: 2025-12-09
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于初始化 CodeHubot 系统的核心数据库结构，包含以下模块：
--    - 核心模块 (Core): 用户管理、学校管理
--    - 设备模块 (Device): 设备管理、产品管理、固件管理、设备分组
--    - 智能体模块 (Agent): AI智能体及知识库关联
--    - 知识库模块 (KB): 知识库、文档、文本块、权限、共享、检索日志、统计分析
--    - LLM模块 (LLM): 大语言模型配置、提供商管理、提示词模板
--    - 插件模块 (Plugin): 插件管理与OpenAPI规范
--    - 工作流模块 (Workflow): 工作流定义与执行记录
--
-- 2. 执行前提条件:
--    - MySQL Server 5.7.x 或 8.0.x 已安装并正常运行
--    - 执行用户拥有 CREATE, ALTER, INDEX, REFERENCES 等权限
--    - 目标数据库已创建并指定正确的字符集
--
-- 3. 执行方式:
--    方式一 (推荐): 
--      mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < init_database.sql
--    
--    方式二:
--      mysql> USE aiot_admin;
--      mysql> SOURCE /path/to/init_database.sql;
--    
--    方式三 (检查模式):
--      mysql -u username -p aiot_admin < init_database.sql > init_output.log 2>&1
--
-- 4. 执行后验证:
--    - 检查输出日志中是否有错误信息
--    - 验证表数量: SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'aiot_admin';
--    - 验证外键约束: SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = 'aiot_admin' AND constraint_type = 'FOREIGN KEY';
--
-- 5. 回滚说明:
--    本脚本不包含自动回滚机制。如需回滚，请执行:
--    - 删除所有表: DROP DATABASE aiot_admin; CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--    - 或使用数据库备份恢复
--
-- 6. 注意事项:
--    - 本脚本仅包含数据库结构定义(DDL)，不包含初始数据(DML)
--    - 所有表的 AUTO_INCREMENT 初始值为 1
--    - 建议在生产环境执行前先在测试环境验证
--    - 执行过程中请勿中断，否则可能导致数据库结构不完整
--    - PBL模块相关表定义在 pbl_schema.sql 中，需单独执行
--
-- 7. 表命名规范:
--    - core_*       : 核心模块表（用户、学校等基础数据）
--    - device_*     : 设备模块表（设备、产品、固件、分组等）
--    - agent_*      : 智能体模块表（AI智能体配置与管理）
--    - kb_*         : 知识库模块表（知识库、文档、检索等）
--    - llm_*        : LLM模块表（大语言模型配置）
--    - plugin_*     : 插件模块表（插件管理）
--    - workflow_*   : 工作流模块表（工作流定义与执行）
--    - pbl_*        : PBL模块表（项目制学习，见 pbl_schema.sql）
--
-- 8. 技术规范:
--    - 存储引擎: InnoDB (支持事务和外键)
--    - 字符集: utf8mb4 (支持完整的 Unicode 字符，包括 Emoji)
--    - 排序规则: utf8mb4_unicode_ci (不区分大小写)
--    - 时间戳: 使用 TIMESTAMP 类型，自动维护创建和更新时间
--    - 软删除: 部分表使用 deleted_at 字段实现软删除
--    - 外键约束: 使用 ON DELETE CASCADE 或 ON DELETE SET NULL 保证数据完整性
--
-- ==========================================================================================================
-- 执行环境检查
-- ==========================================================================================================

-- 检查 MySQL 版本
SELECT 
    VERSION() AS mysql_version,
    @@character_set_database AS db_charset,
    @@collation_database AS db_collation,
    NOW() AS execution_start_time;

-- 显示当前数据库信息
SELECT DATABASE() AS current_database;

-- 设置 SQL 模式（兼容 MySQL 5.7 和 8.0）
SET SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 禁用外键检查（创建表时提升性能，所有表创建完成后会重新启用）
SET FOREIGN_KEY_CHECKS = 0;

-- 禁用唯一性检查（提升导入性能）
SET UNIQUE_CHECKS = 0;

-- 开始事务（确保原子性）
START TRANSACTION;



-- ========================================== 
-- 核心模块（Core）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `core_users`
--

CREATE TABLE `core_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱（学生非必填）',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '电话（学生非必填）',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `nickname` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户昵称（可选，优先显示）',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '姓名',
  `real_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '真实姓名（学生必填）',
  `gender` enum('male','female','other') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性别：male-男, female-女, other-其他',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'individual' COMMENT '用户角色：individual/platform_admin/school_admin/teacher/student',
  `school_id` int(11) DEFAULT NULL COMMENT '所属学校ID（独立用户为NULL）',
  `class_id` int(11) DEFAULT NULL COMMENT '所属班级ID（学生必填）',
  `group_id` int(11) DEFAULT NULL COMMENT '所属小组ID（学生）',
  `school_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学校名称（冗余字段，便于查询）',
  `teacher_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '教师工号（仅教师/学校管理员有）',
  `student_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学号（学生必填）',
  `subject` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '教师学科',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `need_change_password` tinyint(1) DEFAULT '0' COMMENT '首次登录需修改密码',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最后登录IP',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='用户表';

--
-- --------------------------------------------------------

--
-- 表的结构 `core_schools`
--

CREATE TABLE `core_schools` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `school_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学校代码（如 BJ-YCZX）',
  `school_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '学校名称',
  `province` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '省份',
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '城市',
  `district` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '区/县',
  `address` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '详细地址',
  `contact_person` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系人',
  `contact_phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系电话',
  `contact_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系邮箱',
  `is_active` tinyint(1) DEFAULT NULL COMMENT '是否激活',
  `license_expire_at` date DEFAULT NULL COMMENT '授权到期时间',
  `max_teachers` int(11) DEFAULT NULL COMMENT '最大教师数',
  `max_students` int(11) DEFAULT NULL COMMENT '最大学生数',
  `max_devices` int(11) DEFAULT NULL COMMENT '最大设备数',
  `admin_user_id` int(11) DEFAULT NULL COMMENT '学校管理员用户ID',
  `admin_username` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学校管理员用户名',
  `video_student_view_limit` int(11) DEFAULT NULL COMMENT '学生视频观看次数限制（NULL表示不限制）',
  `video_teacher_view_limit` int(11) DEFAULT NULL COMMENT '教师视频观看次数限制（NULL表示不限制）',
  `current_teachers` int(11) DEFAULT 0 COMMENT '当前教师数',
  `current_students` int(11) DEFAULT 0 COMMENT '当前学生数',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '学校描述',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;


-- ========================================== 
-- 设备模块（Device）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `device_main`
--

CREATE TABLE `device_main` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备UUID',
  `device_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `product_id` int(11) DEFAULT NULL COMMENT '产品ID',
  `user_id` int(11) DEFAULT NULL COMMENT '用户ID',
  `school_id` int(11) DEFAULT NULL COMMENT '所属学校ID（用于教学场景）',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '设备描述',
  `device_secret` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备密钥',
  `firmware_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `device_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '设备状态: pending/bound/active/offline/error',
  `is_online` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否在线',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `last_seen` datetime DEFAULT NULL COMMENT '最后在线时间',
  `last_report_data` json DEFAULT NULL COMMENT '最后上报数据（JSON格式，包含设备所有传感器和状态数据）',
  `product_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品代码',
  `product_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `last_product_report` datetime DEFAULT NULL COMMENT '最后产品上报时间',
  `product_switch_count` int(11) NOT NULL DEFAULT '0' COMMENT '产品切换次数',
  `auto_created_product` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自动创建产品',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `mac_address` varchar(17) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'MAC地址',
  `location` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置',
  `group_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分组',
  `room` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '房间',
  `floor` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '楼层',
  `device_sensor_config` json DEFAULT NULL COMMENT '设备传感器配置',
  `device_control_config` json DEFAULT NULL COMMENT '设备控制配置',
  `device_settings` json DEFAULT NULL COMMENT '设备设置',
  `production_date` date DEFAULT NULL COMMENT '生产日期',
  `serial_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '序列号',
  `quality_grade` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '质量等级',
  `last_heartbeat` datetime DEFAULT NULL COMMENT '最后心跳时间',
  `error_count` int(11) NOT NULL DEFAULT '0' COMMENT '错误次数',
  `last_error` text COLLATE utf8mb4_unicode_ci COMMENT '最后错误信息',
  `uptime` bigint(20) DEFAULT NULL COMMENT '运行时间(秒)',
  `installation_date` date DEFAULT NULL COMMENT '安装日期',
  `warranty_expiry` date DEFAULT NULL COMMENT '保修到期日',
  `last_maintenance` date DEFAULT NULL COMMENT '最后维护日期',
  `next_maintenance` date DEFAULT NULL COMMENT '下次维护日期',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='设备表';

--
-- --------------------------------------------------------

--
-- 表的结构 `device_products`
--

CREATE TABLE `device_products` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品代码',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '产品描述',
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品分类',
  `sensor_types` json NOT NULL COMMENT '传感器类型配置',
  `control_ports` json NOT NULL COMMENT '控制端口配置',
  `device_capabilities` json DEFAULT NULL COMMENT '设备能力配置',
  `default_device_config` json DEFAULT NULL COMMENT '默认设备配置',
  `communication_protocols` json DEFAULT NULL COMMENT '通信协议',
  `power_requirements` json DEFAULT NULL COMMENT '电源要求',
  `firmware_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '固件版本',
  `hardware_version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '硬件版本',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `version` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品版本',
  `manufacturer` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商',
  `manufacturer_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制造商代码',
  `total_devices` int(11) NOT NULL DEFAULT '0' COMMENT '设备总数',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置产品',
  `creator_id` int(11) DEFAULT NULL COMMENT '创建者ID',
  `is_shared` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否共享',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='产品表';

--
-- --------------------------------------------------------

--
-- 表的结构 `device_firmware_versions`
--

CREATE TABLE `device_firmware_versions` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `product_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品编码',
  `version` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '版本号',
  `firmware_url` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '固件下载地址',
  `file_size` int(11) NOT NULL COMMENT '文件大小(字节)',
  `file_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件哈希值',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `release_notes` text COLLATE utf8mb4_unicode_ci COMMENT '发布说明',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_latest` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否最新版本',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='固件版本表';

--
-- --------------------------------------------------------

--
-- 表的结构 `device_binding_history`
--

CREATE TABLE `device_binding_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `mac_address` varchar(17) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备MAC地址',
  `device_uuid` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备UUID',
  `device_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备ID',
  `device_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备名称',
  `user_id` int(11) NOT NULL COMMENT '绑定用户ID',
  `user_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户邮箱',
  `user_username` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户名',
  `product_id` int(11) DEFAULT NULL COMMENT '产品ID',
  `product_code` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品编码',
  `product_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '产品名称',
  `action` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型：bind/unbind',
  `action_time` datetime NOT NULL COMMENT '操作时间',
  `notes` text COLLATE utf8mb4_unicode_ci COMMENT '备注信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='设备绑定历史表';

--
-- --------------------------------------------------------

--
-- 表的结构 `device_groups`
--

CREATE TABLE `device_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '分组ID',
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `school_id` int(11) NOT NULL COMMENT '所属学校ID',
  `group_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备组名称',
  `group_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '设备组编号',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '描述',
  `device_count` int(11) DEFAULT '0' COMMENT '设备数量',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `created_by` int(11) DEFAULT NULL COMMENT '创建人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='设备分组表';

--
-- --------------------------------------------------------

--
-- 表的结构 `device_group_members`
--

CREATE TABLE `device_group_members` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
  `group_id` int(11) NOT NULL COMMENT '设备组ID',
  `device_id` int(11) NOT NULL COMMENT '设备ID',
  `joined_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  `left_at` datetime DEFAULT NULL COMMENT '离开时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='设备分组成员表 - 一个设备同一时间只能属于一个设备组（需在应用层实现约束）';

--
-- 注意：设备分组成员约束（一个设备只能属于一个设备组）需要在应用层实现
-- 原因：系统不使用触发器和存储过程，所有业务逻辑在应用层控制
--


-- ========================================== 
-- 智能体模块（Agent）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `agent_main`
--

CREATE TABLE `agent_main` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '智能体名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '智能体描述',
  `system_prompt` text COLLATE utf8mb4_unicode_ci COMMENT '系统提示词',
  `plugin_ids` json DEFAULT NULL COMMENT '关联的插件 ID 列表',
  `llm_model_id` int(11) DEFAULT NULL COMMENT '关联的大模型ID',
  `user_id` int(11) NOT NULL COMMENT '创建用户 ID',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='智能体表';

--
-- --------------------------------------------------------

--
-- 表的结构 `agent_knowledge_bases`
--

CREATE TABLE `agent_knowledge_bases` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
  `agent_id` int(11) NOT NULL COMMENT '智能体ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `priority` int(11) DEFAULT '0' COMMENT '优先级（数字越大优先级越高）',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `top_k` int(11) DEFAULT '5' COMMENT '检索返回的文档数量',
  `similarity_threshold` decimal(3,2) DEFAULT '0.70' COMMENT '相似度阈值',
  `retrieval_mode` enum('vector','keyword','hybrid') COLLATE utf8mb4_unicode_ci DEFAULT 'hybrid' COMMENT '检索模式',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='智能体知识库关联表';


-- ========================================== 
-- 知识库模块（KB）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `kb_main`
--

CREATE TABLE `kb_main` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '知识库ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '知识库名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '知识库描述',
  `icon` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '知识库图标URL',
  `scope_type` enum('system','school','course','agent','personal') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作用域类型',
  `scope_id` int(11) DEFAULT NULL COMMENT '作用域ID（school_id/course_id/agent_id）',
  `parent_kb_id` int(11) DEFAULT NULL COMMENT '父知识库ID（支持继承）',
  `owner_id` int(11) NOT NULL COMMENT '创建者用户ID',
  `access_level` enum('public','protected','private') COLLATE utf8mb4_unicode_ci DEFAULT 'protected' COMMENT '访问级别',
  `document_count` int(11) DEFAULT '0' COMMENT '文档数量',
  `chunk_count` int(11) DEFAULT '0' COMMENT '文本块数量',
  `total_size` bigint(20) DEFAULT '0' COMMENT '总大小（字节）',
  `last_updated_at` datetime DEFAULT NULL COMMENT '最后更新时间',
  `chunk_size` int(11) DEFAULT '500' COMMENT '文本块大小（字符数）',
  `chunk_overlap` int(11) DEFAULT '50' COMMENT '文本块重叠大小',
  `embedding_model_id` int(11) DEFAULT NULL COMMENT 'Embedding模型ID',
  `retrieval_config` json DEFAULT NULL COMMENT '检索配置（相似度阈值、返回数量等）',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `is_system` tinyint(1) DEFAULT '0' COMMENT '是否系统内置',
  `tags` json DEFAULT NULL COMMENT '标签（便于分类）',
  `meta_data` json DEFAULT NULL COMMENT '扩展元数据',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间（软删除）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库表';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_documents`
--

CREATE TABLE `kb_documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '所属知识库ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文档标题',
  `content` longtext COLLATE utf8mb4_unicode_ci COMMENT '文档内容（纯文本）',
  `file_type` enum('txt','md') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件类型（txt-纯文本, md-Markdown）',
  `file_size` bigint(20) DEFAULT NULL COMMENT '文件大小（字节）',
  `file_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文件存储路径（相对路径）',
  `file_hash` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文件MD5哈希（去重）',
  `embedding_status` enum('pending','processing','completed','failed') COLLATE utf8mb4_unicode_ci DEFAULT 'pending' COMMENT '向量化状态',
  `chunk_count` int(11) DEFAULT '0' COMMENT '切分的文本块数量',
  `embedding_error` text COLLATE utf8mb4_unicode_ci COMMENT '向量化失败原因',
  `embedded_at` datetime DEFAULT NULL COMMENT '向量化完成时间',
  `author` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作者',
  `source` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源',
  `language` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'zh' COMMENT '语言',
  `tags` json DEFAULT NULL COMMENT '标签',
  `meta_data` json DEFAULT NULL COMMENT '扩展元数据',
  `uploader_id` int(11) NOT NULL COMMENT '上传者用户ID',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `view_count` int(11) DEFAULT '0' COMMENT '查看次数',
  `reference_count` int(11) DEFAULT '0' COMMENT '被引用次数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间（软删除）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='文档表';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_document_chunks`
--

CREATE TABLE `kb_document_chunks` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '文本块ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `document_id` int(11) NOT NULL COMMENT '所属文档ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '所属知识库ID（冗余，便于查询）',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文本块内容',
  `chunk_index` int(11) NOT NULL COMMENT '在文档中的顺序',
  `char_count` int(11) DEFAULT NULL COMMENT '字符数',
  `token_count` int(11) DEFAULT NULL COMMENT 'Token数（估算）',
  `embedding_vector` json DEFAULT NULL COMMENT '向量表示（JSON数组，用于MySQL存储）',
  `previous_chunk_id` int(11) DEFAULT NULL COMMENT '上一个文本块ID',
  `next_chunk_id` int(11) DEFAULT NULL COMMENT '下一个文本块ID',
  `meta_data` json DEFAULT NULL COMMENT '扩展元数据（如段落位置、标题层级等）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='文本块表（用于向量检索）';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_permissions`
--

CREATE TABLE `kb_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `user_id` int(11) DEFAULT NULL COMMENT '用户ID',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '角色（platform_admin/school_admin/teacher/student）',
  `permission_type` enum('read','write','manage','admin') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限类型',
  `granted_by` int(11) NOT NULL COMMENT '授权人ID',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间（NULL表示永久）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库权限表';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_sharing`
--

CREATE TABLE `kb_sharing` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '共享ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `school_id` int(11) DEFAULT NULL COMMENT '共享给学校ID',
  `course_id` bigint(20) DEFAULT NULL COMMENT '共享给课程ID',
  `user_id` int(11) DEFAULT NULL COMMENT '共享给用户ID',
  `share_type` enum('read_only','editable','reference') COLLATE utf8mb4_unicode_ci DEFAULT 'read_only' COMMENT '共享类型',
  `shared_by` int(11) NOT NULL COMMENT '共享人ID',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库共享表';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_retrieval_logs`
--

CREATE TABLE `kb_retrieval_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `query` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '查询文本',
  `agent_id` int(11) DEFAULT NULL COMMENT '智能体ID',
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `kb_ids` json DEFAULT NULL COMMENT '检索的知识库ID列表',
  `scope_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '检索范围类型',
  `retrieved_chunks` json DEFAULT NULL COMMENT '检索到的文本块ID及分数',
  `chunk_count` int(11) DEFAULT NULL COMMENT '返回的文本块数量',
  `avg_similarity_score` decimal(4,3) DEFAULT NULL COMMENT '平均相似度分数',
  `retrieval_time_ms` int(11) DEFAULT NULL COMMENT '检索耗时（毫秒）',
  `user_feedback` enum('helpful','not_helpful','irrelevant') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户反馈',
  `feedback_at` datetime DEFAULT NULL COMMENT '反馈时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库检索日志表';

--
-- --------------------------------------------------------

--
-- 表的结构 `kb_analytics`
--

CREATE TABLE `kb_analytics` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '统计ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `date` date NOT NULL COMMENT '统计日期',
  `query_count` int(11) DEFAULT '0' COMMENT '查询次数',
  `unique_users` int(11) DEFAULT '0' COMMENT '独立用户数',
  `hit_rate` decimal(4,3) DEFAULT NULL COMMENT '命中率',
  `avg_similarity` decimal(4,3) DEFAULT NULL COMMENT '平均相似度',
  `positive_feedback_count` int(11) DEFAULT '0' COMMENT '正面反馈数',
  `negative_feedback_count` int(11) DEFAULT '0' COMMENT '负面反馈数',
  `document_added` int(11) DEFAULT '0' COMMENT '新增文档数',
  `document_updated` int(11) DEFAULT '0' COMMENT '更新文档数',
  `document_deleted` int(11) DEFAULT '0' COMMENT '删除文档数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库统计表';


-- ========================================== 
-- LLM模块（LLM）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `llm_models`
--

CREATE TABLE `llm_models` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模型名称',
  `display_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '显示名称',
  `provider` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商',
  `model_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '模型类型',
  `api_base` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API基础URL',
  `api_key` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API密钥',
  `api_version` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API版本',
  `max_tokens` int(11) DEFAULT NULL COMMENT '最大token数',
  `temperature` decimal(3,2) DEFAULT NULL COMMENT '温度参数',
  `top_p` decimal(3,2) DEFAULT NULL COMMENT 'top_p参数',
  `enable_deep_thinking` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否启用深度思考',
  `frequency_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '频率惩罚参数',
  `presence_penalty` decimal(3,2) NOT NULL DEFAULT '0.00' COMMENT '存在惩罚参数',
  `config` json DEFAULT NULL COMMENT '其他配置参数',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '模型描述',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_default` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否默认模型',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序顺序',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='LLM模型表';

--
-- --------------------------------------------------------

--
-- 表的结构 `llm_providers`
--

CREATE TABLE `llm_providers` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商代码',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提供商名称',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '完整标题',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '提供商描述',
  `apply_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API申请地址',
  `doc_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文档地址',
  `default_api_base` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '默认API地址',
  `has_free_quota` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否提供免费额度',
  `icon` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图标URL或图标名称',
  `tag_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '标签类型',
  `country` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '国家',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT '排序顺序',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='LLM提供商表';

--
-- --------------------------------------------------------

--
-- 表的结构 `llm_prompt_templates`
--

CREATE TABLE `llm_prompt_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '模板名称',
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '模板描述',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提示词内容',
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分类标签',
  `tags` json DEFAULT NULL COMMENT '标签（数组）',
  `difficulty` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '难度等级：easy/medium/hard',
  `suitable_for` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '适用场景',
  `requires_plugin` tinyint(1) DEFAULT '0' COMMENT '是否需要插件',
  `recommended_temperature` decimal(3,2) DEFAULT '0.70' COMMENT '推荐的Temperature参数',
  `sort_order` int(11) DEFAULT '0' COMMENT '排序顺序',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='提示词模板表';


-- ========================================== 
-- 插件模块（Plugin）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `plugin_main`
--

CREATE TABLE `plugin_main` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '插件名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '插件描述',
  `openapi_spec` json NOT NULL COMMENT 'OpenAPI 3.0.0 规范（JSON）',
  `user_id` int(11) NOT NULL COMMENT '创建用户 ID',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `is_system` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否系统内置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='插件表';


-- ========================================== 
-- 工作流模块（Workflow）
-- ==========================================

-- --------------------------------------------------------

--
-- 表的结构 `workflow_main`
--

CREATE TABLE `workflow_main` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '工作流ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '唯一标识UUID',
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工作流名称',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '工作流描述',
  `user_id` int(11) NOT NULL COMMENT '创建用户ID',
  `nodes` json NOT NULL COMMENT '节点列表（JSON数组）',
  `edges` json NOT NULL COMMENT '边列表（JSON数组）',
  `config` json DEFAULT NULL COMMENT '工作流配置（超时、重试等）',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活（1=激活，0=禁用）',
  `is_public` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否公开（1=公开，0=私有）',
  `execution_count` int(11) NOT NULL DEFAULT '0' COMMENT '执行次数',
  `success_count` int(11) NOT NULL DEFAULT '0' COMMENT '成功次数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_uuid` (`uuid`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_workflow_user` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='工作流表';

--
-- --------------------------------------------------------

--
-- 表的结构 `workflow_executions`
--

CREATE TABLE `workflow_executions` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '执行记录ID',
  `execution_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '执行唯一标识UUID',
  `workflow_id` int(11) NOT NULL COMMENT '工作流ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '执行状态（pending/running/completed/failed）',
  `input` json DEFAULT NULL COMMENT '工作流输入参数（JSON对象）',
  `output` json DEFAULT NULL COMMENT '工作流输出结果（JSON对象）',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息（执行失败时）',
  `node_executions` json DEFAULT NULL COMMENT '节点执行记录（JSON数组）',
  `started_at` datetime DEFAULT NULL COMMENT '开始执行时间',
  `completed_at` datetime DEFAULT NULL COMMENT '完成执行时间',
  `execution_time` int(11) DEFAULT NULL COMMENT '执行时间（毫秒）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_execution_id` (`execution_id`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_execution_workflow` FOREIGN KEY (`workflow_id`) REFERENCES `workflow_main` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='工作流执行记录表';


-- ==========================================
-- 索引定义
-- ==========================================

--
-- 表的索引 `core_users`
--
ALTER TABLE `core_users`
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `uk_school_teacher_number` (`school_id`,`teacher_number`),
  ADD UNIQUE KEY `uk_school_student_number` (`school_id`,`student_number`),
  ADD KEY `idx_email` (`email`),
  ADD KEY `idx_username` (`username`),
  ADD KEY `idx_role` (`role`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_teacher_number` (`teacher_number`),
  ADD KEY `idx_student_number` (`student_number`),
  ADD KEY `idx_real_name` (`real_name`),
  ADD KEY `idx_deleted_at` (`deleted_at`),
  ADD KEY `idx_class_id` (`class_id`),
  ADD KEY `idx_group_id` (`group_id`);

--
-- 表的索引 `core_schools`
--
ALTER TABLE `core_schools`
  ADD UNIQUE KEY `ix_schools_school_code` (`school_code`),
  ADD UNIQUE KEY `idx_uuid` (`uuid`);

--
-- 表的索引 `device_main`
--
ALTER TABLE `device_main`
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD UNIQUE KEY `device_id` (`device_id`),
  ADD KEY `idx_product_id` (`product_id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_device_status` (`device_status`),
  ADD KEY `idx_is_online` (`is_online`),
  ADD KEY `idx_mac_address` (`mac_address`),
  ADD KEY `idx_school_id` (`school_id`);

--
-- 表的索引 `device_products`
--
ALTER TABLE `device_products`
  ADD UNIQUE KEY `product_code` (`product_code`),
  ADD UNIQUE KEY `idx_product_code` (`product_code`),
  ADD KEY `idx_name` (`name`),
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_creator_id` (`creator_id`);

--
-- 表的索引 `device_firmware_versions`
--
ALTER TABLE `device_firmware_versions`
  ADD UNIQUE KEY `version` (`version`),
  ADD KEY `idx_product_code` (`product_code`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- 表的索引 `device_binding_history`
--
ALTER TABLE `device_binding_history`
  ADD KEY `product_id` (`product_id`),
  ADD KEY `ix_device_binding_history_device_uuid` (`device_uuid`),
  ADD KEY `ix_device_binding_history_action_time` (`action_time`),
  ADD KEY `ix_device_binding_history_mac_address` (`mac_address`),
  ADD KEY `ix_device_binding_history_user_id` (`user_id`);

--
-- 表的索引 `device_groups`
--
ALTER TABLE `device_groups`
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_uuid` (`uuid`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_deleted_at` (`deleted_at`),
  ADD KEY `created_by` (`created_by`);

--
-- 表的索引 `device_group_members`
--
ALTER TABLE `device_group_members`
  ADD UNIQUE KEY `uk_group_device` (`group_id`,`device_id`,`left_at`),
  ADD KEY `idx_group_id` (`group_id`),
  ADD KEY `idx_device_id` (`device_id`),
  ADD KEY `idx_left_at` (`left_at`);

--
-- 表的索引 `agent_main`
--
ALTER TABLE `agent_main`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_llm_model_id` (`llm_model_id`);

--
-- 表的索引 `agent_knowledge_bases`
--
ALTER TABLE `agent_knowledge_bases`
  ADD UNIQUE KEY `uk_agent_kb` (`agent_id`,`knowledge_base_id`),
  ADD KEY `idx_agent` (`agent_id`),
  ADD KEY `idx_kb` (`knowledge_base_id`);

--
-- 表的索引 `kb_main`
--
ALTER TABLE `kb_main`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_scope` (`scope_type`,`scope_id`),
  ADD KEY `idx_owner` (`owner_id`),
  ADD KEY `idx_parent` (`parent_kb_id`),
  ADD KEY `idx_active` (`is_active`,`deleted_at`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `kb_documents`
--
ALTER TABLE `kb_documents`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_status` (`embedding_status`),
  ADD KEY `idx_hash` (`file_hash`),
  ADD KEY `idx_uploader` (`uploader_id`),
  ADD KEY `idx_type` (`file_type`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `kb_document_chunks`
--
ALTER TABLE `kb_document_chunks`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_document` (`document_id`,`chunk_index`),
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `kb_permissions`
--
ALTER TABLE `kb_permissions`
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_role` (`role`),
  ADD KEY `idx_expires` (`expires_at`),
  ADD KEY `fk_kbp_granter` (`granted_by`);

--
-- 表的索引 `kb_sharing`
--
ALTER TABLE `kb_sharing`
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_school` (`school_id`),
  ADD KEY `idx_course` (`course_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `fk_kbs_sharer` (`shared_by`);

--
-- 表的索引 `kb_retrieval_logs`
--
ALTER TABLE `kb_retrieval_logs`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_agent` (`agent_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `kb_analytics`
--
ALTER TABLE `kb_analytics`
  ADD UNIQUE KEY `uk_kb_date` (`knowledge_base_id`,`date`),
  ADD KEY `idx_date` (`date`);

--
-- 表的索引 `llm_models`
--
ALTER TABLE `llm_models`
  ADD UNIQUE KEY `uk_uuid` (`uuid`);

--
-- 表的索引 `llm_providers`
--
ALTER TABLE `llm_providers`
  ADD UNIQUE KEY `code` (`code`),
  ADD UNIQUE KEY `uk_uuid` (`uuid`);

--
-- 表的索引 `llm_prompt_templates`
--
ALTER TABLE `llm_prompt_templates`
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_sort_order` (`sort_order`);

--
-- 表的索引 `plugin_main`
--
ALTER TABLE `plugin_main`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `user_id` (`user_id`);

--
-- 表的索引 `workflow_main`
-- 注意：所有索引已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

--
-- 表的索引 `workflow_executions`
-- 注意：所有索引已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--


-- ==========================================
-- 外键约束
-- ==========================================

--
-- 表 `core_users` 的外键约束
--
ALTER TABLE `core_users`
  ADD CONSTRAINT `fk_users_school` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE SET NULL;

--
-- 表 `device_main` 的外键约束
--
ALTER TABLE `device_main`
  ADD CONSTRAINT `device_main_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `device_products` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `device_main_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_device_school` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE SET NULL;

--
-- 表 `device_products` 的外键约束
--
ALTER TABLE `device_products`
  ADD CONSTRAINT `device_products_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `device_binding_history` 的外键约束
--
ALTER TABLE `device_binding_history`
  ADD CONSTRAINT `device_binding_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`),
  ADD CONSTRAINT `device_binding_history_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `device_products` (`id`);

--
-- 表 `device_groups` 的外键约束
--
ALTER TABLE `device_groups`
  ADD CONSTRAINT `device_groups_ibfk_1` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `device_groups_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `device_group_members` 的外键约束
--
ALTER TABLE `device_group_members`
  ADD CONSTRAINT `device_group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `device_groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `device_group_members_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `device_main` (`id`) ON DELETE CASCADE;

--
-- 表 `agent_main` 的外键约束
--
ALTER TABLE `agent_main`
  ADD CONSTRAINT `agent_main_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`);

--
-- 表 `agent_knowledge_bases` 的外键约束
--
ALTER TABLE `agent_knowledge_bases`
  ADD CONSTRAINT `fk_akb_agent` FOREIGN KEY (`agent_id`) REFERENCES `agent_main` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_akb_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE;

--
-- 表 `kb_main` 的外键约束
--
ALTER TABLE `kb_main`
  ADD CONSTRAINT `fk_kb_owner` FOREIGN KEY (`owner_id`) REFERENCES `core_users` (`id`),
  ADD CONSTRAINT `fk_kb_parent` FOREIGN KEY (`parent_kb_id`) REFERENCES `kb_main` (`id`) ON DELETE SET NULL;

--
-- 表 `kb_documents` 的外键约束
--
ALTER TABLE `kb_documents`
  ADD CONSTRAINT `fk_doc_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_doc_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `core_users` (`id`);

--
-- 表 `kb_document_chunks` 的外键约束
--
ALTER TABLE `kb_document_chunks`
  ADD CONSTRAINT `fk_chunk_document` FOREIGN KEY (`document_id`) REFERENCES `kb_documents` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_chunk_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE;

--
-- 表 `kb_permissions` 的外键约束
--
ALTER TABLE `kb_permissions`
  ADD CONSTRAINT `fk_kbp_granter` FOREIGN KEY (`granted_by`) REFERENCES `core_users` (`id`),
  ADD CONSTRAINT `fk_kbp_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbp_user` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `kb_sharing` 的外键约束
--
-- 注意：course_id 引用的是 pbl_courses 表，该外键约束在 pbl_schema.sql 中定义
ALTER TABLE `kb_sharing`
  ADD CONSTRAINT `fk_kbs_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbs_school` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbs_sharer` FOREIGN KEY (`shared_by`) REFERENCES `core_users` (`id`),
  ADD CONSTRAINT `fk_kbs_user` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `kb_analytics` 的外键约束
--
ALTER TABLE `kb_analytics`
  ADD CONSTRAINT `fk_kba_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `kb_main` (`id`) ON DELETE CASCADE;

--
-- 表 `plugin_main` 的外键约束
--
ALTER TABLE `plugin_main`
  ADD CONSTRAINT `plugin_main_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`);

--
-- 表 `workflow_main` 的外键约束
-- 注意：外键约束已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

--
-- 表 `workflow_executions` 的外键约束
-- 注意：外键约束已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--


-- ==========================================================================================================
-- 执行后清理与验证
-- ==========================================================================================================

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 重新启用唯一性检查
SET UNIQUE_CHECKS = 1;

-- 提交事务
COMMIT;

-- ==========================================================================================================
-- 数据库结构验证
-- ==========================================================================================================

-- 验证表数量
SELECT 
    'Database Tables Summary' AS info_type,
    COUNT(*) AS total_tables
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
  AND table_type = 'BASE TABLE';

-- 验证外键约束数量
SELECT 
    'Foreign Key Constraints Summary' AS info_type,
    COUNT(*) AS total_foreign_keys
FROM information_schema.table_constraints 
WHERE constraint_schema = DATABASE() 
  AND constraint_type = 'FOREIGN KEY';

-- 验证索引数量
SELECT 
    'Index Summary' AS info_type,
    COUNT(DISTINCT index_name) AS total_indexes
FROM information_schema.statistics 
WHERE table_schema = DATABASE();

-- 验证触发器数量（系统不使用触发器）
SELECT 
    'Trigger Summary' AS info_type,
    COUNT(*) AS total_triggers,
    'Note: System does not use triggers, all business logic in application layer' AS note
FROM information_schema.triggers 
WHERE trigger_schema = DATABASE();

-- 按模块统计表数量
SELECT 
    'Tables by Module' AS info_type,
    CASE 
        WHEN table_name LIKE 'core_%' THEN 'Core Module'
        WHEN table_name LIKE 'device_%' THEN 'Device Module'
        WHEN table_name LIKE 'agent_%' THEN 'Agent Module'
        WHEN table_name LIKE 'kb_%' THEN 'Knowledge Base Module'
        WHEN table_name LIKE 'llm_%' THEN 'LLM Module'
        WHEN table_name LIKE 'plugin_%' THEN 'Plugin Module'
        WHEN table_name LIKE 'workflow_%' THEN 'Workflow Module'
        ELSE 'Other'
    END AS module_name,
    COUNT(*) AS table_count
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
  AND table_type = 'BASE TABLE'
GROUP BY module_name
ORDER BY table_count DESC;

-- 列出所有创建的表
SELECT 
    table_name AS 'Created Tables',
    ROUND(((data_length + index_length) / 1024), 2) AS 'Size (KB)',
    table_rows AS 'Rows',
    engine AS 'Engine',
    table_collation AS 'Collation'
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ==========================================================================================================
-- 执行完成信息
-- ==========================================================================================================

SELECT 
    '==========================================================================================================' AS ' ';

SELECT 
    'CodeHubot Database Initialization Completed Successfully!' AS 'Status',
    VERSION() AS 'MySQL Version',
    DATABASE() AS 'Database Name',
    NOW() AS 'Completion Time';

SELECT 
    '==========================================================================================================' AS ' ';

SELECT 
    'Next Steps:' AS 'Information';

SELECT 
    '1. Execute pbl_schema.sql to create PBL module tables' AS 'Step 1';

SELECT 
    '2. Verify all tables were created correctly' AS 'Step 2';

SELECT 
    '3. Run application migrations if needed' AS 'Step 3';

SELECT 
    '4. Initialize system data (admin user, default settings, etc.)' AS 'Step 4';

SELECT 
    '5. Backup the clean database structure for future use' AS 'Step 5';

SELECT 
    '==========================================================================================================' AS ' ';

-- ==========================================================================================================
-- 脚本结束
-- ==========================================================================================================
