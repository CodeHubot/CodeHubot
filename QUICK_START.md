# CodeHubot 快速开始指南

> 5分钟快速部署 CodeHubot 智能物联网管理平台

---

## 🚀 最简单的部署方式（推荐新手）

### 前提条件

- Docker 和 Docker Compose（[安装指南](https://docs.docker.com/get-docker/)）
- Git

### 快速部署步骤

#### 1. 克隆项目

```bash
git clone https://gitee.com/codehubot/CodeHubot.git
cd CodeHubot
```

#### 2. 配置环境变量

```bash
# 复制配置文件
cp docker/.env.example docker/.env

# 编辑配置文件
nano docker/.env  # 或使用你喜欢的编辑器
```

**最少必须修改以下3项：**

```bash
# 1. JWT密钥（安全必需）
SECRET_KEY=你的密钥_执行命令生成: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 内部API密钥（安全必需）
INTERNAL_API_KEY=你的API密钥_执行命令生成: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. 阿里云DashScope密钥（AI功能必需）
DASHSCOPE_API_KEY=sk-你的阿里云密钥
```

**可选配置：**

```bash
# 4. 数据库密码（建议修改）
MYSQL_PASSWORD=your_secure_password
MYSQL_ROOT_PASSWORD=your_root_password
```

> 💡 **关于设备MQTT配置**：从v2.0版本开始，设备MQTT地址已迁移到数据库管理，请通过系统管理界面的"系统配置"页面进行配置，无需在.env文件中设置。

#### 3. 一键启动

```bash
chmod +x deploy.sh
./script/deploy.sh
```

选择 `1) 标准模式（内置MySQL）`，然后等待启动完成。

#### 4. 访问系统

- **前端界面**：http://localhost:8080
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

**默认管理员账号：**
- 用户名：`admin`
- 密码：`admin123`（首次登录需修改密码）

---

## 📖 详细配置说明

### 如何获取阿里云DashScope密钥？

1. 访问 https://dashscope.console.aliyun.com/
2. 登录阿里云账号（没有的话需要注册）
3. 开通 DashScope 服务（免费额度足够测试）
4. 在"API-KEY管理"页面创建密钥
5. 复制密钥（格式：`sk-xxxxxxxxxxxxxxxxxxxxxxxx`）
6. 粘贴到配置文件中

### 如何生成安全密钥？

**方法1：使用Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**方法2：使用OpenSSL**
```bash
openssl rand -base64 32
```

**方法3：使用在线工具**
访问 https://www.random.org/strings/ 生成随机字符串（至少32字符）

### 设备MQTT地址如何配置？

**如果你有物联网设备需要连接：**

请在系统启动后，通过**系统管理 > 系统配置**页面配置设备MQTT地址：

1. **使用公网IP**（推荐生产环境）
   - 例如：`47.100.200.300`

2. **使用域名**（推荐）
   - 例如：`mqtt.yourdomain.com`

3. **使用内网IP**（开发测试）
   - 例如：`192.168.1.100`

配置项包括：
- `device_mqtt_broker`：MQTT服务器地址
- `device_mqtt_port`：MQTT服务器端口（默认1883）
- `device_mqtt_use_ssl`：是否使用SSL（默认false）

---

## 🔧 常见问题

### Q1: 启动后无法访问？

**检查端口是否被占用：**
```bash
# 检查8080端口（前端）
lsof -i:8080

# 检查8000端口（后端）
lsof -i:8000
```

**解决方法：**
- 关闭占用端口的程序
- 或修改 `docker/.env` 中的端口配置

### Q2: 提示"数据库连接失败"？

**检查Docker容器状态：**
```bash
docker-compose -f docker/docker-compose.yml ps
```

**如果MySQL容器未启动：**
```bash
docker-compose -f docker/docker-compose.yml logs mysql
```

### Q3: 如何停止服务？

```bash
./script/deploy.sh
# 选择 9) 停止所有服务
```

或直接使用：
```bash
docker-compose -f docker/docker-compose.yml down
```

### Q4: 如何查看日志？

```bash
# 查看所有服务日志
docker-compose -f docker/docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker/docker-compose.yml logs -f backend
docker-compose -f docker/docker-compose.yml logs -f frontend
```

### Q5: 忘记管理员密码怎么办？

**方法1：重置数据库（会清空所有数据）**
```bash
docker-compose -f docker/docker-compose.yml down -v
./script/deploy.sh  # 重新部署
```

**方法2：手动修改数据库**
```bash
# 进入MySQL容器
docker-compose -f docker/docker-compose.yml exec mysql mysql -uroot -p

# 执行SQL重置密码（密码会被设置为 admin123）
USE aiot_admin;
UPDATE aiot_core_users SET password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr6PkqR3e' WHERE username='admin';
```

---

## 📚 下一步

### ⚠️ 重要：部署后必须配置

#### 1. 配置设备MQTT服务器地址（使用物联网设备必需）

部署完成后，需要在管理平台中配置设备连接的MQTT服务器地址：

1. **登录管理平台**：访问 `http://你的服务器IP` 或域名
2. **进入系统配置**：导航到 `系统管理` -> `MQTT配置`
3. **配置MQTT地址**：
   ```
   MQTT Broker地址：你的服务器IP或域名（如：192.168.1.100 或 mqtt.yourdomain.com）
   MQTT端口：1883（默认）
   启用SSL：根据实际情况选择
   ```
4. **保存配置**：点击保存，配置会自动同步

> 💡 **提示**：
> - 设备在启动时会从配置服务（config-service）获取这个MQTT地址
> - 配置服务地址通常和管理平台是同一个地址
> - 如果使用域名，确保设备能够解析该域名
> - 如果使用内网IP，确保设备和服务器在同一网络

**配置路径说明：**
```
设备启动 → 请求配置服务 → 获取MQTT地址 → 连接MQTT服务器
         (config-service)
```

### 基础功能

- ✅ 创建第一个智能体
- ✅ 上传知识库文档
- ✅ 配置LLM模型
- ✅ 注册物联网设备

### 进阶功能

- 📖 [设备管理指南](docs_技术文档/README.md)
- 📖 [AI智能体开发](docs_技术文档/README.md)
- 📖 [工作流编排](docs_技术文档/README.md)
- 📖 [插件开发](docs_技术文档/README.md)

### 开发文档

- 📖 [完整部署文档](docker/README.md)
- 📖 [环境变量配置说明](docs/环境变量配置说明.md)
- 📖 [API开发指南](docs_技术文档/01_开发规范/API开发规范.md)
- 📖 [数据库设计](docs_技术文档/02_系统架构/数据库设计.md)

---

## 🆘 获取帮助

- 📮 提交Issue：https://github.com/CodeHubot/CodeHubot/issues
- 📖 完整文档：[docs_技术文档](docs_技术文档/)
- 💬 社区讨论：https://github.com/CodeHubot/CodeHubot/discussions

---

## ⚠️ 重要提示

### 生产环境部署

如果要部署到生产环境，请：

1. ✅ **修改所有默认密码**
2. ✅ **使用HTTPS（配置Nginx反向代理）**
3. ✅ **配置防火墙规则**
4. ✅ **定期备份数据库**
5. ✅ **使用外部数据库**（参考 `docker/.env.external-db.example`）

### 安全检查清单

- [ ] SECRET_KEY 已修改（不使用示例值）
- [ ] INTERNAL_API_KEY 已修改（不使用示例值）
- [ ] 数据库密码已修改（不使用默认值）
- [ ] 管理员密码已修改（首次登录后）
- [ ] 阿里云密钥已配置
- [ ] **设备MQTT服务器地址已配置**（在管理平台 -> 系统管理 -> MQTT配置中设置）

---

**最后更新：** 2026-01-15  
**版本：** v1.0.0
