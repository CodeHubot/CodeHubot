-- =====================================================
-- 为 core_users 表添加 uuid 字段
-- =====================================================
-- 可重复执行：是（使用动态SQL检查）
-- 兼容性：MySQL 5.7-8.0
-- 说明：为用户表添加 UUID 字段，并为现有用户生成 UUID
-- =====================================================

-- 检查 uuid 列是否存在
SET @column_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'core_users' 
    AND COLUMN_NAME = 'uuid'
);

-- 如果不存在则添加 uuid 列
SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `core_users` ADD COLUMN `uuid` VARCHAR(36) NULL COMMENT \'UUID，用于外部API访问\' AFTER `id`',
    'SELECT "Column uuid already exists in core_users" AS notice'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查 uuid 唯一索引是否存在
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'core_users' 
    AND INDEX_NAME = 'uk_uuid'
);

-- 为现有用户生成 UUID（仅当字段刚添加时）
-- 注意：MySQL 5.7 不支持直接生成 UUID，需要使用 UUID() 函数
UPDATE `core_users` 
SET `uuid` = CONCAT(
    SUBSTR(MD5(CONCAT(id, username, UNIX_TIMESTAMP())), 1, 8), '-',
    SUBSTR(MD5(CONCAT(id, username, UNIX_TIMESTAMP())), 9, 4), '-',
    '4', SUBSTR(MD5(CONCAT(id, username, UNIX_TIMESTAMP())), 14, 3), '-',
    SUBSTR('89ab', 1 + (FLOOR(RAND() * 4)), 1), SUBSTR(MD5(CONCAT(id, username, UNIX_TIMESTAMP())), 18, 3), '-',
    SUBSTR(MD5(CONCAT(id, username, UNIX_TIMESTAMP())), 21, 12)
)
WHERE `uuid` IS NULL OR `uuid` = '';

-- 将 uuid 设置为 NOT NULL
SET @sql_not_null = IF(@column_exists = 0,
    'ALTER TABLE `core_users` MODIFY COLUMN `uuid` VARCHAR(36) NOT NULL COMMENT \'UUID，用于外部API访问\'',
    'SELECT "UUID column already configured" AS notice'
);

PREPARE stmt_not_null FROM @sql_not_null;
EXECUTE stmt_not_null;
DEALLOCATE PREPARE stmt_not_null;

-- 添加唯一索引
SET @sql_index = IF(@index_exists = 0,
    'ALTER TABLE `core_users` ADD UNIQUE KEY `uk_uuid` (`uuid`)',
    'SELECT "Index uk_uuid already exists" AS notice'
);

PREPARE stmt_index FROM @sql_index;
EXECUTE stmt_index;
DEALLOCATE PREPARE stmt_index;

-- 显示执行结果
SELECT 
    CASE 
        WHEN @column_exists = 0 THEN '✅ 字段 uuid 已成功添加到 core_users 表，并为现有用户生成了 UUID'
        ELSE '✓ 字段 uuid 已存在，无需添加'
    END AS result;

-- 显示统计信息
SELECT 
    COUNT(*) as total_users,
    COUNT(uuid) as users_with_uuid,
    COUNT(*) - COUNT(uuid) as users_without_uuid
FROM `core_users`;

