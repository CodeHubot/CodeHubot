-- ==========================================
-- 工作流系统数据库表创建脚本
-- ==========================================
-- 
-- 说明：
--   本脚本用于创建工作流系统相关的数据库表
--   包括工作流表和工作流执行记录表
-- 
-- 使用方式：
--   1. 确保 MySQL 服务已启动
--   2. 选择数据库：USE aiot_admin;
--   3. 执行本脚本：source /path/to/01_create_workflow_tables.sql;
--   4. 或使用命令行：mysql -u username -p aiot_admin < 01_create_workflow_tables.sql
-- 
-- 注意事项：
--   - 支持 MySQL 5.7-8.0 版本
--   - 字符集：utf8mb4，排序规则：utf8mb4_unicode_ci
--   - 所有表使用 aiot_ 前缀
-- 
-- ==========================================

-- --------------------------------------------------------
-- 表的结构 `aiot_workflows` - 工作流表
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS `aiot_workflows` (
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

-- --------------------------------------------------------
-- 表的结构 `aiot_workflow_executions` - 工作流执行记录表
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS `aiot_workflow_executions` (
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

