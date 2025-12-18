-- ==========================================================================================================
-- 数据库同步更新脚本 - 补充线上数据库特有的表
-- ==========================================================================================================
-- 
-- 脚本名称: 28_sync_with_online_database.sql
-- 脚本版本: 1.0.0
-- 创建日期: 2025-12-16
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于将初始化脚本与线上真实数据库进行同步，补充以下表：
--    - pbl_channel_school_relations: 渠道商与学校关联表（教师端渠道管理功能）
--    - pbl_learning_records: 学习记录表（替代pbl_course_enrollments，功能更完整）
--    - pbl_template_school_permissions: 课程模板学校开放权限表
--
-- 2. 执行条件:
--    - 已执行 init_database.sql 和 pbl_schema.sql
--    - 数据库字符集为 utf8mb4
--
-- 3. 执行方式:
--    mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < 28_sync_with_online_database.sql
--
-- ==========================================================================================================
-- 执行环境检查
-- ==========================================================================================================

SELECT 
    DATABASE() AS current_database,
    VERSION() AS mysql_version,
    NOW() AS execution_start_time;

-- 设置执行环境
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;

-- 开始事务
START TRANSACTION;

-- ==========================================================================================================
-- 1. 创建渠道商与学校关联表
-- ==========================================================================================================

-- ----------------------------
-- Table structure for pbl_channel_school_relations
-- 渠道商与学校关联表（用于教师端渠道管理）
-- ----------------------------
CREATE TABLE IF NOT EXISTS `pbl_channel_school_relations` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
  `channel_partner_id` int(11) NOT NULL COMMENT '渠道商ID（关联core_users表，role=channel_partner）',
  `school_id` int(11) NOT NULL COMMENT '学校ID（关联core_schools表）',
  `assigned_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `remarks` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_channel_school` (`channel_partner_id`, `school_id`),
  KEY `idx_channel_partner_id` (`channel_partner_id`),
  KEY `idx_school_id` (`school_id`),
  KEY `idx_is_active` (`is_active`),
  CONSTRAINT `fk_channel_school_partner` FOREIGN KEY (`channel_partner_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_channel_school_school` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='渠道商与学校关联表（教师端渠道管理功能）';

-- ==========================================================================================================
-- 2. 创建学习记录表（替代pbl_course_enrollments）
-- ==========================================================================================================

-- ----------------------------
-- Table structure for pbl_learning_records
-- 学习记录表：记录学生的课程学习进度、成绩、行为数据等
-- 说明：此表功能更完整，替代了原 pbl_course_enrollments 表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `pbl_learning_records` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '学习记录ID',
  `uuid` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID唯一标识',
  `course_id` bigint(20) NOT NULL COMMENT '课程ID',
  `user_id` int(11) NOT NULL COMMENT '学生ID',
  `class_id` int(11) DEFAULT NULL COMMENT '通过哪个班级学习此课程（NULL表示非班级课程）',
  `progress` int(11) DEFAULT '0' COMMENT '学习进度(0-100)',
  `current_unit_id` bigint(20) DEFAULT NULL COMMENT '当前学习到的单元ID',
  `completed_units` text COLLATE utf8mb4_unicode_ci COMMENT '已完成的单元ID列表（JSON格式）',
  `learning_status` enum('not_started','in_progress','completed','paused') COLLATE utf8mb4_unicode_ci DEFAULT 'not_started' COMMENT '学习状态',
  `start_learning_at` timestamp NULL DEFAULT NULL COMMENT '开始学习时间',
  `last_learning_at` timestamp NULL DEFAULT NULL COMMENT '最后一次学习时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成学习时间',
  `final_score` int(11) DEFAULT NULL COMMENT '最终成绩(0-100)',
  `total_score` int(11) DEFAULT '0' COMMENT '累计得分',
  `quiz_score` int(11) DEFAULT NULL COMMENT '测验成绩',
  `assignment_score` int(11) DEFAULT NULL COMMENT '作业成绩',
  `project_score` int(11) DEFAULT NULL COMMENT '项目成绩',
  `total_learning_time` int(11) DEFAULT '0' COMMENT '总学习时长（秒）',
  `video_watch_time` int(11) DEFAULT '0' COMMENT '视频观看时长（秒）',
  `practice_time` int(11) DEFAULT '0' COMMENT '练习时长（秒）',
  `login_days` int(11) DEFAULT '0' COMMENT '登录天数',
  `video_view_count` int(11) DEFAULT '0' COMMENT '视频观看次数',
  `quiz_attempt_count` int(11) DEFAULT '0' COMMENT '测验尝试次数',
  `assignment_submit_count` int(11) DEFAULT '0' COMMENT '作业提交次数',
  `teacher_comment` text COLLATE utf8mb4_unicode_ci COMMENT '教师评语',
  `self_evaluation` text COLLATE utf8mb4_unicode_ci COMMENT '学生自评',
  `metadata` json DEFAULT NULL COMMENT '扩展元数据',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_uuid` (`uuid`),
  UNIQUE KEY `uk_course_user_class` (`course_id`, `user_id`, `class_id`),
  KEY `idx_course_id` (`course_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_class_id` (`class_id`),
  KEY `idx_learning_status` (`learning_status`),
  KEY `idx_current_unit_id` (`current_unit_id`),
  KEY `idx_progress` (`progress`),
  KEY `idx_final_score` (`final_score`),
  KEY `idx_start_learning_at` (`start_learning_at`),
  KEY `idx_last_learning_at` (`last_learning_at`),
  CONSTRAINT `fk_learning_records_course` FOREIGN KEY (`course_id`) REFERENCES `pbl_courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_learning_records_user` FOREIGN KEY (`user_id`) REFERENCES `core_users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_learning_records_class` FOREIGN KEY (`class_id`) REFERENCES `pbl_classes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_learning_records_unit` FOREIGN KEY (`current_unit_id`) REFERENCES `pbl_units` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='PBL学习记录表：记录学生的课程学习进度、成绩、行为数据等';

-- ==========================================================================================================
-- 3. 创建课程模板学校开放权限表
-- ==========================================================================================================

-- ----------------------------
-- Table structure for pbl_template_school_permissions
-- 课程模板学校开放权限表：管理平台向学校开放的课程模板权限
-- ----------------------------
CREATE TABLE IF NOT EXISTS `pbl_template_school_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `uuid` char(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID，用于外部API访问',
  `template_id` bigint(20) NOT NULL COMMENT '课程模板ID',
  `school_id` int(11) NOT NULL COMMENT '学校ID',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活（0-禁用，1-启用）',
  `can_customize` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否允许自定义修改（0-不允许，1-允许）',
  `max_instances` int(11) DEFAULT NULL COMMENT '最大创建实例数（NULL表示不限制）',
  `current_instances` int(11) NOT NULL DEFAULT '0' COMMENT '当前已创建实例数',
  `valid_from` timestamp NULL DEFAULT NULL COMMENT '有效开始时间（NULL表示立即生效）',
  `valid_until` timestamp NULL DEFAULT NULL COMMENT '有效结束时间（NULL表示永久有效）',
  `granted_by` int(11) NOT NULL COMMENT '授权人ID（平台管理员）',
  `granted_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `remarks` text COLLATE utf8mb4_unicode_ci COMMENT '备注说明',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_uuid` (`uuid`),
  UNIQUE KEY `uk_template_school` (`template_id`, `school_id`),
  KEY `idx_template_id` (`template_id`),
  KEY `idx_school_id` (`school_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_granted_by` (`granted_by`),
  KEY `idx_valid_period` (`valid_from`, `valid_until`),
  CONSTRAINT `fk_template_permissions_template` FOREIGN KEY (`template_id`) REFERENCES `pbl_course_templates` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_template_permissions_school` FOREIGN KEY (`school_id`) REFERENCES `core_schools` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_template_permissions_granter` FOREIGN KEY (`granted_by`) REFERENCES `core_users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程模板学校开放权限表 - 管理平台向学校开放的课程模板';

-- ==========================================================================================================
-- 数据迁移说明
-- ==========================================================================================================

-- 如果存在 pbl_course_enrollments 表，可以选择将数据迁移到 pbl_learning_records 表
-- 迁移脚本如下（可选执行）：
/*
INSERT INTO pbl_learning_records (
    uuid, course_id, user_id, class_id, progress, 
    learning_status, start_learning_at, last_learning_at, 
    completed_at, final_score, created_at, updated_at
)
SELECT 
    UUID() as uuid,
    course_id, 
    user_id, 
    class_id,
    progress,
    CASE 
        WHEN enrollment_status = 'enrolled' AND progress = 0 THEN 'not_started'
        WHEN enrollment_status = 'enrolled' AND progress > 0 AND progress < 100 THEN 'in_progress'
        WHEN enrollment_status = 'completed' OR progress = 100 THEN 'completed'
        WHEN enrollment_status = 'dropped' THEN 'paused'
        ELSE 'not_started'
    END as learning_status,
    enrolled_at as start_learning_at,
    updated_at as last_learning_at,
    completed_at,
    final_score,
    created_at,
    updated_at
FROM pbl_course_enrollments
WHERE NOT EXISTS (
    SELECT 1 FROM pbl_learning_records lr 
    WHERE lr.course_id = pbl_course_enrollments.course_id 
    AND lr.user_id = pbl_course_enrollments.user_id
);

-- 迁移完成后，可以选择删除旧表（慎重操作）
-- DROP TABLE IF EXISTS pbl_course_enrollments;
*/

-- ==========================================================================================================
-- 恢复外键检查与提交事务
-- ==========================================================================================================

SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;
COMMIT;

-- ==========================================================================================================
-- 验证新增表
-- ==========================================================================================================

SELECT 
    'Newly Added Tables Summary' AS info_type,
    COUNT(*) AS total_tables
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
  AND table_name IN ('pbl_channel_school_relations', 'pbl_learning_records', 'pbl_template_school_permissions');

SELECT 
    table_name AS 'Added Tables',
    table_comment AS 'Comment'
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
  AND table_name IN ('pbl_channel_school_relations', 'pbl_learning_records', 'pbl_template_school_permissions')
ORDER BY table_name;

-- ==========================================================================================================
-- 执行完成信息
-- ==========================================================================================================

SELECT 
    '==========================================================================================================' AS ' ';

SELECT 
    'Database Synchronization Completed Successfully!' AS 'Status',
    'Added 3 new tables from online database' AS 'Changes',
    NOW() AS 'Completion Time';

SELECT 
    '==========================================================================================================' AS ' ';

SELECT 'Added Tables:' AS 'Information';
SELECT '1. pbl_channel_school_relations - 渠道商与学校关联表（教师端功能）' AS 'Table 1';
SELECT '2. pbl_learning_records - 学习记录表（替代pbl_course_enrollments，功能更完整）' AS 'Table 2';
SELECT '3. pbl_template_school_permissions - 课程模板学校开放权限表' AS 'Table 3';

SELECT 
    '==========================================================================================================' AS ' ';

-- ==========================================================================================================
-- 脚本结束
-- ==========================================================================================================

