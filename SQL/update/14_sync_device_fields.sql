-- ============================================================================
-- 同步设备表字段（与后端模型保持一致）
-- ============================================================================
-- 说明：后端 Device 模型包含的字段，数据库中必须存在
-- 本脚本添加缺失的字段
-- ============================================================================

-- 添加产品相关字段
ALTER TABLE `aiot_core_devices`
ADD COLUMN `last_product_report` datetime DEFAULT NULL COMMENT '最后产品上报时间' AFTER `product_version`,
ADD COLUMN `product_switch_count` int NOT NULL DEFAULT '0' COMMENT '产品切换次数' AFTER `last_product_report`,
ADD COLUMN `auto_created_product` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否自动创建产品' AFTER `product_switch_count`;

-- 添加分组和位置字段
ALTER TABLE `aiot_core_devices`
ADD COLUMN `group_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分组' AFTER `location`,
ADD COLUMN `room` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '房间' AFTER `group_name`,
ADD COLUMN `floor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '楼层' AFTER `room`;

-- 添加生产和质量信息字段
ALTER TABLE `aiot_core_devices`
ADD COLUMN `production_date` date DEFAULT NULL COMMENT '生产日期' AFTER `device_settings`,
ADD COLUMN `serial_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '序列号' AFTER `production_date`,
ADD COLUMN `quality_grade` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '质量等级' AFTER `serial_number`;

-- 添加运行状态字段
ALTER TABLE `aiot_core_devices`
ADD COLUMN `error_count` int NOT NULL DEFAULT '0' COMMENT '错误次数' AFTER `last_heartbeat`,
ADD COLUMN `last_error` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '最后错误信息' AFTER `error_count`,
ADD COLUMN `uptime` bigint DEFAULT NULL COMMENT '运行时间(秒)' AFTER `last_error`;

-- 添加维护信息字段
ALTER TABLE `aiot_core_devices`
ADD COLUMN `installation_date` date DEFAULT NULL COMMENT '安装日期' AFTER `uptime`,
ADD COLUMN `warranty_expiry` date DEFAULT NULL COMMENT '保修到期日' AFTER `installation_date`,
ADD COLUMN `last_maintenance` date DEFAULT NULL COMMENT '最后维护日期' AFTER `warranty_expiry`,
ADD COLUMN `next_maintenance` date DEFAULT NULL COMMENT '下次维护日期' AFTER `last_maintenance`;

-- 验证字段是否添加成功
SHOW COLUMNS FROM `aiot_core_devices`;

-- ============================================================================
-- 执行完成后，重启后端服务让 SQLAlchemy 重新加载表结构
-- ============================================================================

