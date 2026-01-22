-- ==========================================================================================================
-- 数据库迁移脚本：学校(School) → 团队(Team)
-- ==========================================================================================================
-- 
-- 脚本名称: 02_school_to_team_migration.sql
-- 创建日期: 2026-01-22
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 
-- 说明：
--   本脚本将系统中的"学校"概念完全迁移为"团队"概念
--   采用"添加新列-复制数据-删除外键-删除列"策略
--   脚本可重复执行（幂等性）
--
-- 执行前提：
--   1. 备份数据库！
--   2. 确保没有正在运行的应用连接数据库
--
-- ==========================================================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET FOREIGN_KEY_CHECKS = 0;

-- ==========================================================================================================
-- 第一步：重命名主表 core_schools → core_teams
-- ==========================================================================================================

SET @table_exists = (SELECT COUNT(*) FROM information_schema.TABLES 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_schools');
SET @sql = IF(@table_exists > 0, 'RENAME TABLE `core_schools` TO `core_teams`', 'SELECT "core_teams already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第二步：修改 core_teams 表字段
-- ==========================================================================================================

SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_teams' AND COLUMN_NAME = 'school_code');
SET @sql = IF(@col_exists > 0, 
  'ALTER TABLE `core_teams` CHANGE COLUMN `school_code` `team_code` VARCHAR(50) NOT NULL COMMENT ''团队代码'', CHANGE COLUMN `school_name` `team_name` VARCHAR(200) NOT NULL COMMENT ''团队名称''',
  'SELECT "core_teams columns already renamed" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第三步：修改 core_users 表
-- ==========================================================================================================

-- 3.1 添加新字段 team_id
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND COLUMN_NAME = 'team_id');
SET @sql = IF(@col_exists = 0, 
  'ALTER TABLE `core_users` ADD COLUMN `team_id` INT(11) DEFAULT NULL COMMENT ''所属团队ID''',
  'SELECT "Column team_id already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.2 添加新字段 team_name
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND COLUMN_NAME = 'team_name');
SET @sql = IF(@col_exists = 0, 
  'ALTER TABLE `core_users` ADD COLUMN `team_name` VARCHAR(200) DEFAULT NULL COMMENT ''团队名称''',
  'SELECT "Column team_name already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.3 复制数据
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'UPDATE `core_users` SET `team_id` = `school_id`, `team_name` = `school_name` WHERE `school_id` IS NOT NULL',
  'SELECT "No school_id to migrate" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.4 更新角色
UPDATE `core_users` SET `role` = 'team_admin' WHERE `role` = 'school_admin';

-- 3.5 删除所有相关外键
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND CONSTRAINT_NAME = 'fk_users_school');
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE `core_users` DROP FOREIGN KEY `fk_users_school`', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND CONSTRAINT_NAME = 'core_users_ibfk_1');
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE `core_users` DROP FOREIGN KEY `core_users_ibfk_1`', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.6 删除旧字段（删除列会自动删除相关索引）
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'ALTER TABLE `core_users` DROP COLUMN `school_id`, DROP COLUMN `school_name`',
  'SELECT "Old columns already dropped" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.7 创建新索引
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND INDEX_NAME = 'idx_team_id');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `core_users` ADD KEY `idx_team_id` (`team_id`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND INDEX_NAME = 'uk_team_teacher_number');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `core_users` ADD UNIQUE KEY `uk_team_teacher_number` (`team_id`, `teacher_number`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND INDEX_NAME = 'uk_team_student_number');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `core_users` ADD UNIQUE KEY `uk_team_student_number` (`team_id`, `student_number`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.8 创建新外键
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'core_users' AND CONSTRAINT_NAME = 'fk_users_team');
SET @sql = IF(@fk_exists = 0, 'ALTER TABLE `core_users` ADD CONSTRAINT `fk_users_team` FOREIGN KEY (`team_id`) REFERENCES `core_teams` (`id`) ON DELETE SET NULL', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第四步：修改 device_main 表
-- ==========================================================================================================

-- 4.1 添加新字段 team_id
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND COLUMN_NAME = 'team_id');
SET @sql = IF(@col_exists = 0, 
  'ALTER TABLE `device_main` ADD COLUMN `team_id` INT(11) DEFAULT NULL COMMENT ''所属团队ID''',
  'SELECT "Column team_id already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.2 复制数据
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'UPDATE `device_main` SET `team_id` = `school_id` WHERE `school_id` IS NOT NULL',
  'SELECT "No school_id to migrate" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.3 删除外键 fk_device_school
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND CONSTRAINT_NAME = 'fk_device_school');
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE `device_main` DROP FOREIGN KEY `fk_device_school`', 'SELECT "FK fk_device_school not exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.4 删除旧字段（删除列会自动删除相关索引）
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'ALTER TABLE `device_main` DROP COLUMN `school_id`',
  'SELECT "Old column already dropped" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.5 创建新索引
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND INDEX_NAME = 'idx_team_id');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `device_main` ADD KEY `idx_team_id` (`team_id`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4.6 创建新外键
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_main' AND CONSTRAINT_NAME = 'fk_device_team');
SET @sql = IF(@fk_exists = 0, 'ALTER TABLE `device_main` ADD CONSTRAINT `fk_device_team` FOREIGN KEY (`team_id`) REFERENCES `core_teams` (`id`) ON DELETE SET NULL', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第五步：修改 device_groups 表
-- ==========================================================================================================

-- 5.1 添加新字段 team_id
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND COLUMN_NAME = 'team_id');
SET @sql = IF(@col_exists = 0, 
  'ALTER TABLE `device_groups` ADD COLUMN `team_id` INT(11) NOT NULL DEFAULT 0 COMMENT ''所属团队ID''',
  'SELECT "Column team_id already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5.2 复制数据
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'UPDATE `device_groups` SET `team_id` = `school_id` WHERE `school_id` IS NOT NULL',
  'SELECT "No school_id to migrate" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5.3 删除外键 device_groups_ibfk_1
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND CONSTRAINT_NAME = 'device_groups_ibfk_1');
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE `device_groups` DROP FOREIGN KEY `device_groups_ibfk_1`', 'SELECT "FK device_groups_ibfk_1 not exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5.4 删除旧字段（删除列会自动删除相关索引）
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'ALTER TABLE `device_groups` DROP COLUMN `school_id`',
  'SELECT "Old column already dropped" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5.5 创建新索引
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND INDEX_NAME = 'idx_team_id');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `device_groups` ADD KEY `idx_team_id` (`team_id`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5.6 创建新外键
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'device_groups' AND CONSTRAINT_NAME = 'device_groups_ibfk_1');
SET @sql = IF(@fk_exists = 0, 'ALTER TABLE `device_groups` ADD CONSTRAINT `device_groups_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `core_teams` (`id`) ON DELETE CASCADE', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第六步：修改 kb_sharing 表
-- ==========================================================================================================

-- 6.1 添加新字段 team_id
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND COLUMN_NAME = 'team_id');
SET @sql = IF(@col_exists = 0, 
  'ALTER TABLE `kb_sharing` ADD COLUMN `team_id` INT(11) DEFAULT NULL COMMENT ''共享给团队ID''',
  'SELECT "Column team_id already exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6.2 复制数据
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'UPDATE `kb_sharing` SET `team_id` = `school_id` WHERE `school_id` IS NOT NULL',
  'SELECT "No school_id to migrate" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6.3 删除外键 fk_kbs_school
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND CONSTRAINT_NAME = 'fk_kbs_school');
SET @sql = IF(@fk_exists > 0, 'ALTER TABLE `kb_sharing` DROP FOREIGN KEY `fk_kbs_school`', 'SELECT "FK fk_kbs_school not exists" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6.4 删除旧字段（删除列会自动删除相关索引）
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND COLUMN_NAME = 'school_id');
SET @sql = IF(@col_exists > 0, 
  'ALTER TABLE `kb_sharing` DROP COLUMN `school_id`',
  'SELECT "Old column already dropped" AS notice');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6.5 创建新索引
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.STATISTICS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND INDEX_NAME = 'idx_team');
SET @sql = IF(@idx_exists = 0, 'ALTER TABLE `kb_sharing` ADD KEY `idx_team` (`team_id`)', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6.6 创建新外键
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'kb_sharing' AND CONSTRAINT_NAME = 'fk_kbs_team');
SET @sql = IF(@fk_exists = 0, 'ALTER TABLE `kb_sharing` ADD CONSTRAINT `fk_kbs_team` FOREIGN KEY (`team_id`) REFERENCES `core_teams` (`id`) ON DELETE CASCADE', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================================================================================
-- 第七步：更新数据
-- ==========================================================================================================

UPDATE `kb_main` SET `scope_type` = 'team' WHERE `scope_type` = 'school';
UPDATE `kb_permissions` SET `role` = 'team_admin' WHERE `role` = 'school_admin';

-- ==========================================================================================================
-- 完成
-- ==========================================================================================================

SET FOREIGN_KEY_CHECKS = 1;

SELECT '==========================================================================================================' AS ' ';
SELECT 'Migration completed successfully!' AS status;
SELECT '所有 school 相关字段已成功迁移为 team' AS message;
SELECT '==========================================================================================================' AS ' ';
