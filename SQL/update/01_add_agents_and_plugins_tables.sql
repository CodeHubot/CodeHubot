-- ============================================================================
-- CodeHubot AI-IoT 智能教学平台 - 数据库更新脚本
-- 版本: 1.0.0
-- 日期: 2025-11-24
-- 说明: 添加智能体和插件管理表
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. 创建插件表（AI 扩展功能）
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
  FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI插件表（扩展功能）';

-- ============================================================================
-- 2. 创建智能体表（AI 扩展功能）
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
  FOREIGN KEY (`user_id`) REFERENCES `aiot_core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体表（扩展功能）';

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 脚本执行完成
-- ============================================================================

