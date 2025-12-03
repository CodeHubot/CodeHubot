-- ==========================================
-- CodeHubot 数据库初始化脚本
-- ==========================================
--
-- 说明：
--   本脚本用于初始化 CodeHubot 系统的数据库结构
--   包含所有核心表和扩展表的定义、索引、外键约束等
--
-- 使用方式：
--   1. 确保 MySQL 服务已启动
--   2. 创建数据库：CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   3. 选择数据库：USE aiot_admin;
--   4. 执行本脚本：source /path/to/init_database.sql;
--   5. 或使用命令行：mysql -u username -p aiot_admin < init_database.sql
--
-- 注意事项：
--   - 本脚本仅包含表结构定义，不包含示例数据
--   - 所有 AUTO_INCREMENT 从 1 开始
--   - 支持 MySQL 5.7-8.0 版本
--   - 字符集：utf8mb4，排序规则：utf8mb4_unicode_ci
--
-- 表结构说明：
--   - 核心表（aiot_core_*）：系统运行必需的基础表
--   - 扩展表（aiot_*）：可选功能表，可根据业务需求选择性部署
--
-- ==========================================



-- --------------------------------------------------------

--
-- 表的结构 `aiot_agents`
--

CREATE TABLE `aiot_agents` (
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
-- 表的结构 `aiot_agent_knowledge_bases`
--

CREATE TABLE `aiot_agent_knowledge_bases` (
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

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_classes`
--

CREATE TABLE `aiot_classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '班级ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `school_id` int(11) NOT NULL COMMENT '所属学校ID',
  `class_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '班级名称',
  `grade` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '年级',
  `class_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '班号',
  `teacher_id` int(11) DEFAULT NULL COMMENT '班主任ID',
  `teacher_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '班主任姓名',
  `academic_year` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学年',
  `semester` enum('spring','fall') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学期',
  `student_count` int(11) DEFAULT NULL COMMENT '学生人数',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '班级描述',
  `is_active` tinyint(1) DEFAULT NULL COMMENT '是否激活',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;

-- --------------------------------------------------------

--
-- 表的结构 `aiot_class_teachers`
--

CREATE TABLE `aiot_class_teachers` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
  `class_id` int(11) NOT NULL COMMENT '班级ID',
  `teacher_id` int(11) NOT NULL COMMENT '教师ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;

-- --------------------------------------------------------

--
-- 表的结构 `aiot_core_devices`
--

CREATE TABLE `aiot_core_devices` (
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
-- 表的结构 `aiot_core_firmware_versions`
--

CREATE TABLE `aiot_core_firmware_versions` (
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

-- --------------------------------------------------------

--
-- 表的结构 `aiot_core_products`
--

CREATE TABLE `aiot_core_products` (
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
-- 表的结构 `aiot_core_users`
--

CREATE TABLE `aiot_core_users` (
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
-- 表的结构 `aiot_courses`
--

CREATE TABLE `aiot_courses` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '班级ID',
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `school_id` int(11) NOT NULL COMMENT '所属学校ID',
  `course_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '课程名称',
  `grade` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '年级（如：三年级）',
  `course_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '课程编号',
  `teacher_id` int(11) DEFAULT NULL COMMENT '教师ID（已废弃，使用 aiot_class_teachers 表）',
  `teacher_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '教师姓名（已废弃，使用 aiot_class_teachers 表）',
  `academic_year` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学年（可选）',
  `semester` enum('spring','fall') COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学期：spring-春季, fall-秋季',
  `student_count` int(11) DEFAULT '0' COMMENT '选课学生人数',
  `max_students` int(11) DEFAULT '100' COMMENT '最大学生人数',
  `teacher_count` int(11) DEFAULT '0' COMMENT '授课教师人数',
  `credits` decimal(3,1) DEFAULT '0.0' COMMENT '学分',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '课程描述',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间（软删除）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='课程表';

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_course_device_authorizations`
--

CREATE TABLE `aiot_course_device_authorizations` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '授权ID',
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `device_group_id` int(11) NOT NULL COMMENT '设备组ID',
  `authorized_by` int(11) NOT NULL COMMENT '授权人ID（学校管理员）',
  `authorized_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `notes` text COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='课程设备授权表';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_course_groups`
--

CREATE TABLE `aiot_course_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '小组ID',
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `course_id` int(11) NOT NULL COMMENT '所属课程ID',
  `school_id` int(11) NOT NULL COMMENT '所属学校ID（冗余，便于查询）',
  `group_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '小组名称（如：小组A）',
  `group_number` int(11) DEFAULT NULL COMMENT '小组编号（班级内序号）',
  `leader_id` int(11) DEFAULT NULL COMMENT '组长ID',
  `leader_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '组长姓名（冗余字段）',
  `member_count` int(11) DEFAULT '0' COMMENT '成员人数（冗余字段）',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '小组描述',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间（软删除）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='课程分组表';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_course_students`
--

CREATE TABLE `aiot_course_students` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `student_id` int(11) NOT NULL COMMENT '学生ID',
  `enrolled_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
  `status` enum('enrolled','completed','dropped') COLLATE utf8mb4_unicode_ci DEFAULT 'enrolled' COMMENT '状态：enrolled-在读, completed-已完成, dropped-已退课',
  `score` decimal(5,2) DEFAULT NULL COMMENT '成绩',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间（软删除）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='学生-课程关联表（选课记录）';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_course_teachers`
--

CREATE TABLE `aiot_course_teachers` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `teacher_id` int(11) NOT NULL COMMENT '教师ID',
  `subject` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '教师在该班级教授的科目',
  `is_primary` tinyint(1) DEFAULT NULL COMMENT '是否为班主任',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='教师-课程关联表（多对多）';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_device_binding_history`
--

CREATE TABLE `aiot_device_binding_history` (
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
-- 表的结构 `aiot_device_groups`
--

CREATE TABLE `aiot_device_groups` (
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
-- 表的结构 `aiot_device_group_members`
--

CREATE TABLE `aiot_device_group_members` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
  `group_id` int(11) NOT NULL COMMENT '设备组ID',
  `device_id` int(11) NOT NULL COMMENT '设备ID',
  `joined_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  `left_at` datetime DEFAULT NULL COMMENT '离开时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='设备分组成员表 - 一个设备同一时间只能属于一个设备组（通过触发器约束）';

--
--
-- 触发器 `aiot_device_group_members`
--
DELIMITER $$
CREATE TRIGGER `before_insert_device_group_member_check` BEFORE INSERT ON `aiot_device_group_members` FOR EACH ROW BEGIN
    DECLARE existing_count INT;
    
    -- 检查该设备是否已经在其他活跃的设备组中
    SELECT COUNT(*) INTO existing_count
    FROM aiot_device_group_members
    WHERE device_id = NEW.device_id
      AND left_at IS NULL
      AND group_id != NEW.group_id;
    
    IF existing_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '该设备已在其他设备组中，一个设备只能属于一个设备组';
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `before_update_device_group_member_check` BEFORE UPDATE ON `aiot_device_group_members` FOR EACH ROW BEGIN
    DECLARE existing_count INT;
    
    -- 只在left_at从非NULL变为NULL时检查（设备重新加入）
    IF OLD.left_at IS NOT NULL AND NEW.left_at IS NULL THEN
        SELECT COUNT(*) INTO existing_count
        FROM aiot_device_group_members
        WHERE device_id = NEW.device_id
          AND left_at IS NULL
          AND group_id != NEW.group_id;
        
        IF existing_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = '该设备已在其他设备组中，一个设备只能属于一个设备组';
        END IF;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- 表的结构 `aiot_documents`
--

CREATE TABLE `aiot_documents` (
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
-- 表的结构 `aiot_document_chunks`
--

CREATE TABLE `aiot_document_chunks` (
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
-- 表的结构 `aiot_groups`
--

CREATE TABLE `aiot_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '小组ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `class_id` int(11) NOT NULL COMMENT '所属班级ID',
  `school_id` int(11) NOT NULL COMMENT '所属学校ID',
  `group_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '小组名称',
  `group_number` int(11) DEFAULT NULL COMMENT '小组编号',
  `leader_id` int(11) DEFAULT NULL COMMENT '组长ID',
  `leader_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '组长姓名',
  `member_count` int(11) DEFAULT NULL COMMENT '成员人数',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '小组描述',
  `is_active` tinyint(1) DEFAULT NULL COMMENT '是否激活',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  `deleted_at` datetime DEFAULT NULL COMMENT '删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;

-- --------------------------------------------------------

--
-- 表的结构 `aiot_group_members`
--

CREATE TABLE `aiot_group_members` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
  `group_id` int(11) NOT NULL COMMENT '小组ID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `school_id` int(11) NOT NULL COMMENT '学校ID（冗余，便于查询）',
  `student_id` int(11) NOT NULL COMMENT '学生ID',
  `student_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学生姓名（冗余字段）',
  `student_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学号（冗余字段）',
  `is_leader` tinyint(1) DEFAULT '0' COMMENT '是否为组长',
  `joined_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
  `left_at` datetime DEFAULT NULL COMMENT '离开时间（软删除/转组）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='小组成员表';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_kb_analytics`
--

CREATE TABLE `aiot_kb_analytics` (
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

-- --------------------------------------------------------

--
-- 表的结构 `aiot_kb_permissions`
--

CREATE TABLE `aiot_kb_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `user_id` int(11) DEFAULT NULL COMMENT '用户ID',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '角色（platform_admin/school_admin/teacher/student）',
  `permission_type` enum('read','write','manage','admin') COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限类型',
  `granted_by` int(11) NOT NULL COMMENT '授权人ID',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间（NULL表示永久）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库权限表';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_kb_retrieval_logs`
--

CREATE TABLE `aiot_kb_retrieval_logs` (
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

-- --------------------------------------------------------

--
-- 表的结构 `aiot_kb_sharing`
--

CREATE TABLE `aiot_kb_sharing` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '共享ID',
  `knowledge_base_id` int(11) NOT NULL COMMENT '知识库ID',
  `school_id` int(11) DEFAULT NULL COMMENT '共享给学校ID',
  `course_id` int(11) DEFAULT NULL COMMENT '共享给课程ID',
  `user_id` int(11) DEFAULT NULL COMMENT '共享给用户ID',
  `share_type` enum('read_only','editable','reference') COLLATE utf8mb4_unicode_ci DEFAULT 'read_only' COMMENT '共享类型',
  `shared_by` int(11) NOT NULL COMMENT '共享人ID',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='知识库共享表';

-- --------------------------------------------------------

--
-- 表的结构 `aiot_knowledge_bases`
--

CREATE TABLE `aiot_knowledge_bases` (
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
-- 表的结构 `aiot_llm_models`
--

CREATE TABLE `aiot_llm_models` (
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
-- 表的结构 `aiot_llm_providers`
--

CREATE TABLE `aiot_llm_providers` (
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
-- 表的结构 `aiot_plugins`
--

CREATE TABLE `aiot_plugins` (
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

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_prompt_templates`
--

CREATE TABLE `aiot_prompt_templates` (
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

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_workflows`
--

CREATE TABLE `aiot_workflows` (
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
  CONSTRAINT `fk_workflow_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='工作流表';

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_workflow_executions`
--

CREATE TABLE `aiot_workflow_executions` (
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
  CONSTRAINT `fk_execution_workflow` FOREIGN KEY (`workflow_id`) REFERENCES `aiot_workflows` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1 COMMENT='工作流执行记录表';

--
-- --------------------------------------------------------

--
-- 表的结构 `aiot_schools`
--

CREATE TABLE `aiot_schools` (
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
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci AUTO_INCREMENT=1;



--
-- 表的索引 `aiot_agents`
--
ALTER TABLE `aiot_agents`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_llm_model_id` (`llm_model_id`);

--
-- 表的索引 `aiot_agent_knowledge_bases`
--
ALTER TABLE `aiot_agent_knowledge_bases`
  ADD UNIQUE KEY `uk_agent_kb` (`agent_id`,`knowledge_base_id`),
  ADD KEY `idx_agent` (`agent_id`),
  ADD KEY `idx_kb` (`knowledge_base_id`);

--
-- 表的索引 `aiot_classes`
--
ALTER TABLE `aiot_classes`
  ADD UNIQUE KEY `ix_aiot_classes_uuid` (`uuid`),
  ADD KEY `ix_aiot_classes_teacher_id` (`teacher_id`),
  ADD KEY `ix_aiot_classes_academic_year` (`academic_year`),
  ADD KEY `ix_aiot_classes_is_active` (`is_active`),
  ADD KEY `ix_aiot_classes_school_id` (`school_id`);

--
-- 表的索引 `aiot_class_teachers`
--
ALTER TABLE `aiot_class_teachers`
  ADD KEY `ix_aiot_class_teachers_teacher_id` (`teacher_id`),
  ADD KEY `ix_aiot_class_teachers_class_id` (`class_id`);

--
-- 表的索引 `aiot_core_devices`
--
ALTER TABLE `aiot_core_devices`
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD UNIQUE KEY `device_id` (`device_id`),
  ADD KEY `idx_product_id` (`product_id`),
  ADD KEY `idx_user_id` (`user_id`),
  ADD KEY `idx_device_status` (`device_status`),
  ADD KEY `idx_is_online` (`is_online`),
  ADD KEY `idx_mac_address` (`mac_address`),
  ADD KEY `idx_school_id` (`school_id`);

--
-- 表的索引 `aiot_core_firmware_versions`
--
ALTER TABLE `aiot_core_firmware_versions`
  ADD UNIQUE KEY `version` (`version`),
  ADD KEY `idx_product_code` (`product_code`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- 表的索引 `aiot_core_products`
--
ALTER TABLE `aiot_core_products`
  ADD UNIQUE KEY `product_code` (`product_code`),
  ADD UNIQUE KEY `idx_product_code` (`product_code`),
  ADD KEY `idx_name` (`name`),
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_creator_id` (`creator_id`);

--
-- 表的索引 `aiot_core_users`
--
ALTER TABLE `aiot_core_users`
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
-- 表的索引 `aiot_courses`
--
ALTER TABLE `aiot_courses`
  ADD UNIQUE KEY `idx_uuid` (`uuid`),
  ADD UNIQUE KEY `uk_school_class` (`school_id`,`course_name`,`deleted_at`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_teacher_id` (`teacher_id`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_academic_year` (`academic_year`);

--
-- 表的索引 `aiot_course_device_authorizations`
--
ALTER TABLE `aiot_course_device_authorizations`
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD UNIQUE KEY `uk_course_group` (`course_id`,`device_group_id`,`expires_at`),
  ADD KEY `idx_course_id` (`course_id`),
  ADD KEY `idx_device_group_id` (`device_group_id`),
  ADD KEY `idx_uuid` (`uuid`),
  ADD KEY `idx_authorized_by` (`authorized_by`),
  ADD KEY `idx_expires_at` (`expires_at`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- 表的索引 `aiot_course_groups`
--
ALTER TABLE `aiot_course_groups`
  ADD UNIQUE KEY `idx_uuid` (`uuid`),
  ADD UNIQUE KEY `uk_class_group` (`course_id`,`group_name`,`deleted_at`),
  ADD KEY `idx_class_id` (`course_id`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_leader_id` (`leader_id`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- 表的索引 `aiot_course_students`
--
ALTER TABLE `aiot_course_students`
  ADD UNIQUE KEY `uk_course_student` (`course_id`,`student_id`),
  ADD KEY `idx_course_id` (`course_id`),
  ADD KEY `idx_student_id` (`student_id`),
  ADD KEY `idx_status` (`status`);

--
-- 表的索引 `aiot_course_teachers`
--
ALTER TABLE `aiot_course_teachers`
  ADD UNIQUE KEY `uk_class_teacher` (`course_id`,`teacher_id`),
  ADD KEY `ix_aiot_class_teachers_class_id` (`course_id`),
  ADD KEY `ix_aiot_class_teachers_teacher_id` (`teacher_id`),
  ADD KEY `ix_aiot_class_teachers_is_primary` (`is_primary`);

--
-- 表的索引 `aiot_device_binding_history`
--
ALTER TABLE `aiot_device_binding_history`
  ADD KEY `product_id` (`product_id`),
  ADD KEY `ix_device_binding_history_device_uuid` (`device_uuid`),
  ADD KEY `ix_device_binding_history_action_time` (`action_time`),
  ADD KEY `ix_device_binding_history_mac_address` (`mac_address`),
  ADD KEY `ix_device_binding_history_user_id` (`user_id`);

--
-- 表的索引 `aiot_device_groups`
--
ALTER TABLE `aiot_device_groups`
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_uuid` (`uuid`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_deleted_at` (`deleted_at`),
  ADD KEY `created_by` (`created_by`);

--
-- 表的索引 `aiot_device_group_members`
--
ALTER TABLE `aiot_device_group_members`
  ADD UNIQUE KEY `uk_group_device` (`group_id`,`device_id`,`left_at`),
  ADD KEY `idx_group_id` (`group_id`),
  ADD KEY `idx_device_id` (`device_id`),
  ADD KEY `idx_left_at` (`left_at`);

--
-- 表的索引 `aiot_documents`
--
ALTER TABLE `aiot_documents`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_status` (`embedding_status`),
  ADD KEY `idx_hash` (`file_hash`),
  ADD KEY `idx_uploader` (`uploader_id`),
  ADD KEY `idx_type` (`file_type`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `aiot_document_chunks`
--
ALTER TABLE `aiot_document_chunks`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_document` (`document_id`,`chunk_index`),
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `aiot_groups`
--
ALTER TABLE `aiot_groups`
  ADD UNIQUE KEY `ix_aiot_groups_uuid` (`uuid`),
  ADD KEY `ix_aiot_groups_is_active` (`is_active`),
  ADD KEY `ix_aiot_groups_leader_id` (`leader_id`),
  ADD KEY `ix_aiot_groups_class_id` (`class_id`),
  ADD KEY `ix_aiot_groups_school_id` (`school_id`);

--
-- 表的索引 `aiot_group_members`
--
ALTER TABLE `aiot_group_members`
  ADD UNIQUE KEY `uk_group_student` (`group_id`,`student_id`,`left_at`),
  ADD KEY `idx_group_id` (`group_id`),
  ADD KEY `idx_class_id` (`course_id`),
  ADD KEY `idx_school_id` (`school_id`),
  ADD KEY `idx_student_id` (`student_id`),
  ADD KEY `idx_is_leader` (`is_leader`);

--
-- 表的索引 `aiot_kb_analytics`
--
ALTER TABLE `aiot_kb_analytics`
  ADD UNIQUE KEY `uk_kb_date` (`knowledge_base_id`,`date`),
  ADD KEY `idx_date` (`date`);

--
-- 表的索引 `aiot_kb_permissions`
--
ALTER TABLE `aiot_kb_permissions`
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_role` (`role`),
  ADD KEY `idx_expires` (`expires_at`),
  ADD KEY `fk_kbp_granter` (`granted_by`);

--
-- 表的索引 `aiot_kb_retrieval_logs`
--
ALTER TABLE `aiot_kb_retrieval_logs`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_agent` (`agent_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `aiot_kb_sharing`
--
ALTER TABLE `aiot_kb_sharing`
  ADD KEY `idx_kb` (`knowledge_base_id`),
  ADD KEY `idx_school` (`school_id`),
  ADD KEY `idx_course` (`course_id`),
  ADD KEY `idx_user` (`user_id`),
  ADD KEY `fk_kbs_sharer` (`shared_by`);

--
-- 表的索引 `aiot_knowledge_bases`
--
ALTER TABLE `aiot_knowledge_bases`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `idx_scope` (`scope_type`,`scope_id`),
  ADD KEY `idx_owner` (`owner_id`),
  ADD KEY `idx_parent` (`parent_kb_id`),
  ADD KEY `idx_active` (`is_active`,`deleted_at`),
  ADD KEY `idx_created` (`created_at`);

--
-- 表的索引 `aiot_llm_models`
--
ALTER TABLE `aiot_llm_models`
  ADD UNIQUE KEY `uk_uuid` (`uuid`);

--
-- 表的索引 `aiot_llm_providers`
--
ALTER TABLE `aiot_llm_providers`
  ADD UNIQUE KEY `code` (`code`),
  ADD UNIQUE KEY `uk_uuid` (`uuid`);

--
-- 表的索引 `aiot_plugins`
--
ALTER TABLE `aiot_plugins`
  ADD UNIQUE KEY `uk_uuid` (`uuid`),
  ADD KEY `user_id` (`user_id`);

--
-- 表的索引 `aiot_prompt_templates`
--
ALTER TABLE `aiot_prompt_templates`
  ADD KEY `idx_category` (`category`),
  ADD KEY `idx_is_active` (`is_active`),
  ADD KEY `idx_sort_order` (`sort_order`);

--
-- 表的索引 `aiot_workflows`
-- 注意：所有索引已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

--
-- 表的索引 `aiot_workflow_executions`
-- 注意：所有索引已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

--
-- 表的索引 `aiot_schools`
--
ALTER TABLE `aiot_schools`
  ADD UNIQUE KEY `ix_aiot_schools_school_code` (`school_code`),
  ADD UNIQUE KEY `idx_uuid` (`uuid`);


--
-- 表 `aiot_agents` 的外键约束
--
ALTER TABLE `aiot_agents`
  ADD CONSTRAINT `aiot_agents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_agent_knowledge_bases` 的外键约束
--
ALTER TABLE `aiot_agent_knowledge_bases`
  ADD CONSTRAINT `fk_akb_agent` FOREIGN KEY (`agent_id`) REFERENCES `aiot_agents` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_akb_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_classes` 的外键约束
--
ALTER TABLE `aiot_classes`
  ADD CONSTRAINT `aiot_classes_ibfk_1` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`),
  ADD CONSTRAINT `aiot_classes_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_class_teachers` 的外键约束
--
ALTER TABLE `aiot_class_teachers`
  ADD CONSTRAINT `aiot_class_teachers_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `aiot_classes` (`id`),
  ADD CONSTRAINT `aiot_class_teachers_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_core_devices` 的外键约束
--
ALTER TABLE `aiot_core_devices`
  ADD CONSTRAINT `aiot_core_devices_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `aiot_core_devices_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `fk_device_school` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_core_products` 的外键约束
--
ALTER TABLE `aiot_core_products`
  ADD CONSTRAINT `aiot_core_products_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_core_users` 的外键约束
--
ALTER TABLE `aiot_core_users`
  ADD CONSTRAINT `fk_users_school` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_courses` 的外键约束
--
ALTER TABLE `aiot_courses`
  ADD CONSTRAINT `aiot_courses_ibfk_1` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_courses_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_course_device_authorizations` 的外键约束
--
ALTER TABLE `aiot_course_device_authorizations`
  ADD CONSTRAINT `aiot_course_device_authorizations_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_course_device_authorizations_ibfk_2` FOREIGN KEY (`device_group_id`) REFERENCES `aiot_device_groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_course_device_authorizations_ibfk_3` FOREIGN KEY (`authorized_by`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_course_groups` 的外键约束
--
ALTER TABLE `aiot_course_groups`
  ADD CONSTRAINT `fk_cg_course` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_course_groups_ibfk_2` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_course_groups_ibfk_3` FOREIGN KEY (`leader_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_course_students` 的外键约束
--
ALTER TABLE `aiot_course_students`
  ADD CONSTRAINT `fk_cs_course` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_cs_student` FOREIGN KEY (`student_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_course_teachers` 的外键约束
--
ALTER TABLE `aiot_course_teachers`
  ADD CONSTRAINT `aiot_course_teachers_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`),
  ADD CONSTRAINT `aiot_course_teachers_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `aiot_core_users` (`id`),
  ADD CONSTRAINT `fk_ct_course` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_ct_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_device_binding_history` 的外键约束
--
ALTER TABLE `aiot_device_binding_history`
  ADD CONSTRAINT `device_binding_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`),
  ADD CONSTRAINT `device_binding_history_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `aiot_core_products` (`id`);

--
-- 表 `aiot_device_groups` 的外键约束
--
ALTER TABLE `aiot_device_groups`
  ADD CONSTRAINT `aiot_device_groups_ibfk_1` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_device_groups_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `aiot_core_users` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_device_group_members` 的外键约束
--
ALTER TABLE `aiot_device_group_members`
  ADD CONSTRAINT `aiot_device_group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `aiot_device_groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_device_group_members_ibfk_2` FOREIGN KEY (`device_id`) REFERENCES `aiot_core_devices` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_documents` 的外键约束
--
ALTER TABLE `aiot_documents`
  ADD CONSTRAINT `fk_doc_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_doc_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_document_chunks` 的外键约束
--
ALTER TABLE `aiot_document_chunks`
  ADD CONSTRAINT `fk_chunk_document` FOREIGN KEY (`document_id`) REFERENCES `aiot_documents` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_chunk_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_groups` 的外键约束
--
ALTER TABLE `aiot_groups`
  ADD CONSTRAINT `aiot_groups_ibfk_1` FOREIGN KEY (`class_id`) REFERENCES `aiot_classes` (`id`),
  ADD CONSTRAINT `aiot_groups_ibfk_2` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`),
  ADD CONSTRAINT `aiot_groups_ibfk_3` FOREIGN KEY (`leader_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_group_members` 的外键约束
--
ALTER TABLE `aiot_group_members`
  ADD CONSTRAINT `aiot_group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `aiot_course_groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_gm_course` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_group_members_ibfk_3` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `aiot_group_members_ibfk_4` FOREIGN KEY (`student_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_kb_analytics` 的外键约束
--
ALTER TABLE `aiot_kb_analytics`
  ADD CONSTRAINT `fk_kba_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_kb_permissions` 的外键约束
--
ALTER TABLE `aiot_kb_permissions`
  ADD CONSTRAINT `fk_kbp_granter` FOREIGN KEY (`granted_by`) REFERENCES `aiot_core_users` (`id`),
  ADD CONSTRAINT `fk_kbp_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbp_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_kb_sharing` 的外键约束
--
ALTER TABLE `aiot_kb_sharing`
  ADD CONSTRAINT `fk_kbs_course` FOREIGN KEY (`course_id`) REFERENCES `aiot_courses` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbs_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbs_school` FOREIGN KEY (`school_id`) REFERENCES `aiot_schools` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_kbs_sharer` FOREIGN KEY (`shared_by`) REFERENCES `aiot_core_users` (`id`),
  ADD CONSTRAINT `fk_kbs_user` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE;

--
-- 表 `aiot_knowledge_bases` 的外键约束
--
ALTER TABLE `aiot_knowledge_bases`
  ADD CONSTRAINT `fk_kb_owner` FOREIGN KEY (`owner_id`) REFERENCES `aiot_core_users` (`id`),
  ADD CONSTRAINT `fk_kb_parent` FOREIGN KEY (`parent_kb_id`) REFERENCES `aiot_knowledge_bases` (`id`) ON DELETE SET NULL;

--
-- 表 `aiot_plugins` 的外键约束
--
ALTER TABLE `aiot_plugins`
  ADD CONSTRAINT `aiot_plugins_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`);

--
-- 表 `aiot_workflows` 的外键约束
-- 注意：外键约束已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

--
-- 表 `aiot_workflow_executions` 的外键约束
-- 注意：外键约束已在 CREATE TABLE 中定义，无需额外的 ALTER TABLE
--

COMMIT;

