-- =====================================================
-- 为 core_users 表添加 company_name 字段
-- 用于存储渠道商的公司名称信息
-- 创建时间: 2026-01-03
-- 兼容性: MySQL 5.7-8.0
-- 可重复执行: 是（使用动态SQL检查）
-- =====================================================

-- 检查字段是否存在，不存在则添加
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'core_users' 
    AND COLUMN_NAME = 'company_name'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `core_users` ADD COLUMN `company_name` VARCHAR(200) NULL COMMENT \'公司名称（仅渠道商有）\' AFTER `subject`',
    'SELECT "Column company_name already exists in core_users" AS notice'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 显示执行结果
SELECT 
    CASE 
        WHEN @column_exists = 0 THEN '✅ 字段 company_name 已成功添加到 core_users 表'
        ELSE '✓ 字段 company_name 已存在，无需添加'
    END AS result;

