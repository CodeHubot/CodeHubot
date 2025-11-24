-- 初始化数据库脚本
-- 在 MySQL 容器启动时自动执行

-- 创建 aiot_device 数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS aiot_device CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 授予 aiot_user 用户对 aiot_device 数据库的权限
GRANT ALL PRIVILEGES ON aiot_device.* TO 'aiot_user'@'%';
FLUSH PRIVILEGES;

