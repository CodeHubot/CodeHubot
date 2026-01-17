-- ==========================================================================================================
-- CodeHubot 数据库迁移脚本 (从旧版本迁移到新版本)
-- ==========================================================================================================
-- 
-- 脚本名称: migration_from_old_to_new.sql
-- 脚本版本: 1.0.0
-- 创建日期: 2026-01-17
-- 兼容版本: MySQL 5.7.x, 8.0.x
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
--
-- ==========================================================================================================
-- 脚本说明
-- ==========================================================================================================
--
-- 1. 用途说明:
--    本脚本用于将旧版本 aiot-demo 数据库的数据迁移到新版本 CodeHubot 数据库
--    
-- 2. 迁移内容:
--    - 用户数据 (users → core_users)
--    - 产品数据 (products → device_products)
--    - 固件数据 (firmware_versions → device_firmware_versions)
--    - 设备数据 (devices → device_main)
--    - 设备绑定历史 (device_binding_history → device_binding_history)
--    - 访问日志 (access_logs → device_access_logs)
--
-- 3. 前置条件:
--    - 新数据库必须已经执行过 01_init_database.sql 和 02_init_data.sql
--    - 旧数据库 aiot-demo 必须可以访问
--    - 确保有足够的权限进行跨数据库查询和插入
--
-- 4. 执行方式:
--    方式一 (推荐): 
--      mysql -h hostname -u username -p --default-character-set=utf8mb4 aiot_admin < migration_from_old_to_new.sql
--    
--    方式二:
--      mysql> USE aiot_admin;
--      mysql> SOURCE /path/to/migration_from_old_to_new.sql;
--
-- 5. 注意事项:
--    - 本脚本会跳过已存在的数据 (使用 INSERT IGNORE)
--    - 执行前请务必备份新数据库
--    - 建议在测试环境先执行一次验证
--    - 迁移过程中不会删除旧数据库的数据
--
-- 6. 数据映射说明:
--    - 旧数据库中没有学校概念,所有用户 school_id 设为 NULL (独立用户)
--    - 用户角色统一设置为 'individual' (个人用户)
--    - UUID 字段使用 UUID() 函数自动生成
--    - 旧数据库中不存在的字段使用默认值或 NULL
--
-- ==========================================================================================================
-- 执行环境检查
-- ==========================================================================================================

SELECT '==========================================================================================================' AS '';
SELECT 'CodeHubot 数据迁移开始' AS 'Status';
SELECT '==========================================================================================================' AS '';

-- 设置 SQL 模式
SET SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 禁用外键检查（提升导入性能）
SET FOREIGN_KEY_CHECKS = 0;

-- 禁用唯一性检查
SET UNIQUE_CHECKS = 0;

-- 开始事务
START TRANSACTION;

-- ==========================================================================================================
-- 步骤 1: 迁移用户数据 (users → core_users)
-- ==========================================================================================================

SELECT '步骤 1/6: 开始迁移用户数据...' AS '';

INSERT INTO `core_users` (
    `id`,
    `uuid`,
    `email`,
    `username`,
    `name`,
    `password_hash`,
    `role`,
    `school_id`,
    `is_active`,
    `created_at`,
    `updated_at`
)
SELECT 
    u.`id`,
    UUID() AS `uuid`,
    u.`email`,
    u.`username`,
    u.`username` AS `name`,  -- 使用 username 作为 name
    u.`password_hash`,
    'individual' AS `role`,  -- 所有旧用户都设置为个人用户
    NULL AS `school_id`,     -- 旧数据库没有学校概念
    u.`is_active`,
    u.`created_at`,
    u.`updated_at`
FROM `aiot-demo`.`users` AS u
WHERE NOT EXISTS (
    SELECT 1 FROM `core_users` WHERE `id` = u.`id`
);

SELECT CONCAT('✓ 用户数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 步骤 2: 迁移产品数据 (products → device_products)
-- ==========================================================================================================

SELECT '步骤 2/6: 开始迁移产品数据...' AS '';

INSERT INTO `device_products` (
    `id`,
    `product_code`,
    `name`,
    `description`,
    `category`,
    `sensor_types`,
    `control_ports`,
    `device_capabilities`,
    `default_device_config`,
    `firmware_version`,
    `hardware_version`,
    `is_active`,
    `manufacturer`,
    `total_devices`,
    `is_system`,
    `created_at`,
    `updated_at`
)
SELECT 
    p.`id`,
    p.`product_code`,
    p.`name`,
    p.`description`,
    p.`category`,
    p.`sensor_types`,
    p.`control_ports`,
    p.`device_capabilities`,
    '{}' AS `default_device_config`,  -- 旧数据库没有此字段
    p.`firmware_version`,
    p.`hardware_version`,
    p.`is_active`,
    p.`manufacturer`,
    p.`total_devices`,
    0 AS `is_system`,  -- 迁移的产品不是系统内置
    p.`created_at`,
    p.`updated_at`
FROM `aiot-demo`.`products` AS p
WHERE NOT EXISTS (
    SELECT 1 FROM `device_products` WHERE `id` = p.`id`
);

SELECT CONCAT('✓ 产品数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 步骤 3: 迁移固件版本数据 (firmware_versions → device_firmware_versions)
-- ==========================================================================================================

SELECT '步骤 3/6: 开始迁移固件版本数据...' AS '';

INSERT INTO `device_firmware_versions` (
    `id`,
    `product_code`,
    `version`,
    `firmware_url`,
    `file_size`,
    `file_hash`,
    `description`,
    `release_notes`,
    `is_active`,
    `is_latest`,
    `created_at`,
    `updated_at`
)
SELECT 
    f.`id`,
    f.`product_code`,
    f.`version`,
    f.`firmware_url`,
    f.`file_size`,
    f.`file_hash`,
    f.`description`,
    f.`release_notes`,
    f.`is_active`,
    f.`is_latest`,
    f.`created_at`,
    f.`updated_at`
FROM `aiot-demo`.`firmware_versions` AS f
WHERE NOT EXISTS (
    SELECT 1 FROM `device_firmware_versions` WHERE `id` = f.`id`
);

SELECT CONCAT('✓ 固件版本数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 步骤 4: 迁移设备数据 (devices → device_main)
-- ==========================================================================================================

SELECT '步骤 4/6: 开始迁移设备数据...' AS '';

INSERT INTO `device_main` (
    `id`,
    `uuid`,
    `device_id`,
    `product_id`,
    `user_id`,
    `school_id`,
    `name`,
    `description`,
    `device_secret`,
    `firmware_version`,
    `hardware_version`,
    `device_status`,
    `is_online`,
    `is_active`,
    `last_seen`,
    `last_report_data`,
    `product_code`,
    `ip_address`,
    `mac_address`,
    `location`,
    `group_name`,
    `production_date`,
    `serial_number`,
    `quality_grade`,
    `last_heartbeat`,
    `error_count`,
    `last_error`,
    `uptime`,
    `installation_date`,
    `warranty_expiry`,
    `last_maintenance`,
    `next_maintenance`,
    `created_at`,
    `updated_at`
)
SELECT 
    d.`id`,
    d.`uuid`,
    d.`device_id`,
    d.`product_id`,
    d.`user_id`,
    NULL AS `school_id`,  -- 旧数据库没有学校概念
    d.`name`,
    d.`description`,
    d.`device_secret`,
    d.`firmware_version`,
    d.`hardware_version`,
    d.`device_status`,
    d.`is_online`,
    d.`is_active`,
    d.`last_seen`,
    d.`last_report_data`,
    d.`product_code`,
    d.`ip_address`,
    d.`mac_address`,
    d.`location`,
    d.`group_name`,
    d.`production_date`,
    d.`serial_number`,
    d.`quality_grade`,
    d.`last_heartbeat`,
    d.`error_count`,
    d.`last_error`,
    d.`uptime`,
    d.`installation_date`,
    d.`warranty_expiry`,
    d.`last_maintenance`,
    d.`next_maintenance`,
    d.`created_at`,
    d.`updated_at`
FROM `aiot-demo`.`devices` AS d
WHERE NOT EXISTS (
    SELECT 1 FROM `device_main` WHERE `id` = d.`id`
);

SELECT CONCAT('✓ 设备数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 步骤 5: 迁移设备绑定历史 (device_binding_history → device_binding_history)
-- ==========================================================================================================

SELECT '步骤 5/6: 开始迁移设备绑定历史数据...' AS '';

INSERT INTO `device_binding_history` (
    `id`,
    `mac_address`,
    `device_uuid`,
    `device_id`,
    `device_name`,
    `user_id`,
    `user_email`,
    `user_username`,
    `product_id`,
    `product_code`,
    `product_name`,
    `action`,
    `action_time`,
    `notes`,
    `created_at`
)
SELECT 
    h.`id`,
    h.`mac_address`,
    h.`device_uuid`,
    h.`device_id`,
    h.`device_name`,
    h.`user_id`,
    h.`user_email`,
    h.`user_username`,
    h.`product_id`,
    h.`product_code`,
    h.`product_name`,
    h.`action`,
    h.`action_time`,
    h.`notes`,
    h.`created_at`
FROM `aiot-demo`.`device_binding_history` AS h
WHERE NOT EXISTS (
    SELECT 1 FROM `device_binding_history` WHERE `id` = h.`id`
);

SELECT CONCAT('✓ 设备绑定历史数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 步骤 6: 迁移访问日志数据 (access_logs → device_access_logs)
-- ==========================================================================================================

SELECT '步骤 6/6: 开始迁移访问日志数据...' AS '';

INSERT INTO `device_access_logs` (
    `id`,
    `ip_address`,
    `endpoint`,
    `mac_address`,
    `success`,
    `timestamp`,
    `user_agent`
)
SELECT 
    a.`id`,
    a.`ip_address`,
    a.`endpoint`,
    a.`mac_address`,
    a.`success`,
    a.`timestamp`,
    a.`user_agent`
FROM `aiot-demo`.`access_logs` AS a
WHERE NOT EXISTS (
    SELECT 1 FROM `device_access_logs` WHERE `id` = a.`id`
);

SELECT CONCAT('✓ 访问日志数据迁移完成，共迁移 ', ROW_COUNT(), ' 条记录') AS '';

-- ==========================================================================================================
-- 数据验证与统计
-- ==========================================================================================================

SELECT '==========================================================================================================' AS '';
SELECT '数据迁移验证与统计' AS '';
SELECT '==========================================================================================================' AS '';

-- 统计各表迁移数据量
SELECT 
    '用户数据' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `core_users`
UNION ALL
SELECT 
    '产品数据' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `device_products`
UNION ALL
SELECT 
    '固件版本数据' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `device_firmware_versions`
UNION ALL
SELECT 
    '设备数据' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `device_main`
UNION ALL
SELECT 
    '设备绑定历史' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `device_binding_history`
UNION ALL
SELECT 
    '访问日志' AS '数据类型',
    COUNT(*) AS '总数量'
FROM `device_access_logs`;

-- 验证外键关系是否正常
SELECT '验证外键关系...' AS '';

-- 检查是否有设备关联了不存在的用户
SELECT 
    '设备-用户关联检查' AS '检查项',
    COUNT(*) AS '孤立记录数'
FROM `device_main` d
LEFT JOIN `core_users` u ON d.`user_id` = u.`id`
WHERE d.`user_id` IS NOT NULL AND u.`id` IS NULL;

-- 检查是否有设备关联了不存在的产品
SELECT 
    '设备-产品关联检查' AS '检查项',
    COUNT(*) AS '孤立记录数'
FROM `device_main` d
LEFT JOIN `device_products` p ON d.`product_id` = p.`id`
WHERE d.`product_id` IS NOT NULL AND p.`id` IS NULL;

-- 检查是否有绑定历史关联了不存在的用户
SELECT 
    '绑定历史-用户关联检查' AS '检查项',
    COUNT(*) AS '孤立记录数'
FROM `device_binding_history` h
LEFT JOIN `core_users` u ON h.`user_id` = u.`id`
WHERE h.`user_id` IS NOT NULL AND u.`id` IS NULL;

-- ==========================================================================================================
-- 清理与完成
-- ==========================================================================================================

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 重新启用唯一性检查
SET UNIQUE_CHECKS = 1;

-- 提交事务
COMMIT;

SELECT '==========================================================================================================' AS '';
SELECT 'CodeHubot 数据迁移完成！' AS 'Status';
SELECT '==========================================================================================================' AS '';

-- ==========================================================================================================
-- 后续步骤提示
-- ==========================================================================================================

SELECT '后续步骤:' AS '';
SELECT '1. 验证数据完整性' AS '步骤 1';
SELECT '2. 检查应用程序连接和功能' AS '步骤 2';
SELECT '3. 测试设备上线和数据上报' AS '步骤 3';
SELECT '4. 如确认无误，可以考虑归档旧数据库' AS '步骤 4';
SELECT '==========================================================================================================' AS '';

-- ==========================================================================================================
-- 注意事项
-- ==========================================================================================================

SELECT '注意事项:' AS '';
SELECT '1. 旧数据库中的 device_data_logs、interaction_logs 等日志表数据未迁移' AS '提示 1';
SELECT '2. 这些历史日志数据量可能很大，建议保留在旧数据库中作为归档' AS '提示 2';
SELECT '3. 如需迁移日志数据，请联系管理员编写专门的迁移脚本' AS '提示 3';
SELECT '4. 新系统使用 device_sensors 表存储传感器数据，结构与旧版不同' AS '提示 4';
SELECT '==========================================================================================================' AS '';

-- ==========================================================================================================
-- 脚本结束
-- ==========================================================================================================
