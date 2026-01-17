# CodeHubot 数据库初始化脚本

本目录包含 CodeHubot 系统的数据库初始化脚本。

## 文件说明

### 主要文件

- `01_init_database.sql` - 数据库结构脚本（1341行）
  - 创建所有数据表
  - 定义表结构、字段、索引
  - 设置外键约束
  - MySQL 5.7/8.0 兼容

- `02_init_data.sql` - 初始数据脚本（227行）
  - 插入系统初始数据
  - 包含默认配置、示例数据等

### 更新脚本目录

- `update/` - 数据库更新脚本目录
  - 存放数据库增量更新脚本
  - 按序号命名（如 `01_xxx.sql`, `02_xxx.sql`）

## Docker 部署时的自动执行

在使用 Docker 部署时，这些 SQL 脚本会在 MySQL 容器**首次启动**时自动执行：

1. MySQL 容器启动时会自动扫描 `/docker-entrypoint-initdb.d/` 目录
2. 按文件名顺序执行 `.sql` 文件
3. 执行顺序：
   - `01_init_database.sql` - 先创建表结构
   - `02_init_data.sql` - 再插入初始数据

**重要提示：**
- ⚠️ 只有在**首次启动**（数据卷为空）时才会执行
- ⚠️ 如果数据库已存在，脚本不会重复执行
- ⚠️ 要重新执行，需要删除 MySQL 数据卷后重启

## 手动执行（外部数据库）

如果使用外部 MySQL 数据库（不使用 Docker MySQL），需要手动执行：

```bash
# 进入项目根目录
cd /path/to/CodeHubot

# 1. 执行数据库结构脚本
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/01_init_database.sql

# 2. 执行初始数据脚本
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/02_init_data.sql
```

或者一次性执行：

```bash
cat SQL/01_init_database.sql SQL/02_init_data.sql | mysql -h YOUR_HOST -u aiot_user -p aiot_admin
```

## 重新初始化数据库

### Docker 环境

```bash
# 方法1: 删除数据卷后重新启动（会自动执行SQL）
docker-compose -f docker/docker-compose.prod.yml down -v
docker-compose -f docker/docker-compose.prod.yml up -d

# 方法2: 进入容器手动执行
docker exec -i codehubot-mysql mysql -u root -p数据库密码 aiot_admin < SQL/01_init_database.sql
docker exec -i codehubot-mysql mysql -u root -p数据库密码 aiot_admin < SQL/02_init_data.sql
```

### 外部数据库

```bash
# 1. 删除数据库
mysql -h YOUR_HOST -u root -p -e "DROP DATABASE IF EXISTS aiot_admin; CREATE DATABASE aiot_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 重新执行初始化脚本
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/01_init_database.sql
mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/02_init_data.sql
```

## 数据库更新

如果需要更新现有数据库结构，请：

1. 创建新的更新脚本到 `update/` 目录
2. 按序号命名（如 `03_add_new_feature.sql`）
3. 手动执行更新脚本：
   ```bash
   mysql -h YOUR_HOST -u aiot_user -p aiot_admin < SQL/update/03_add_new_feature.sql
   ```

## 注意事项

1. **字符集**：所有表使用 `utf8mb4` 字符集和 `utf8mb4_unicode_ci` 排序规则
2. **兼容性**：脚本兼容 MySQL 5.7 和 8.0
3. **幂等性**：初始化脚本使用 `IF NOT EXISTS`，可以安全地重复执行
4. **备份**：修改数据库前，请先备份数据
5. **权限**：确保数据库用户有足够的权限（CREATE, ALTER, INSERT 等）

## 故障排查

### 问题：SQL脚本未执行

**原因：** 数据库已存在，MySQL 不会重复执行初始化脚本

**解决：**
```bash
# 删除数据卷后重启
docker-compose -f docker/docker-compose.prod.yml down -v
docker-compose -f docker/docker-compose.prod.yml up -d
```

### 问题：SQL执行出错

**排查：**
1. 查看 MySQL 容器日志：
   ```bash
   docker-compose -f docker/docker-compose.prod.yml logs mysql
   ```

2. 进入容器检查：
   ```bash
   docker exec -it codehubot-mysql bash
   mysql -u root -p
   SHOW DATABASES;
   USE aiot_admin;
   SHOW TABLES;
   ```

3. 手动执行脚本查看错误信息：
   ```bash
   docker exec -i codehubot-mysql mysql -u root -p数据库密码 aiot_admin < SQL/01_init_database.sql
   ```
