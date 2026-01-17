# CodeHubot 部署指南

> 快速、清晰、实用的部署文档

---

## 🚀 快速开始

### 方式1：Docker部署（推荐）

```bash
# 1. 克隆项目
git clone https://gitee.com/codehubot/CodeHubot.git
cd CodeHubot

# 2. 配置环境变量
cd docker
cp .env.example .env
# 编辑 .env 文件，修改必要配置（SECRET_KEY、INTERNAL_API_KEY、DASHSCOPE_API_KEY等）

# 3. 一键部署
cd ..
./script/deploy.sh
```

**适用场景**：生产环境、快速部署、最小化配置

📖 **详细步骤**：查看 [快速开始指南](../QUICK_START.md) 或 [Docker部署文档](docs/docker-deployment.md)

---

### 方式2：本地开发

```bash
# 1. 启动基础服务（MySQL、Redis、MQTT）
cd docker
docker-compose up -d mysql redis mqtt

# 2. 配置并启动后端
cd ../backend
cp .env.example .env
# 编辑 .env 文件
pip install -r requirements.txt
python main.py

# 3. 配置并启动前端
cd ../frontend
npm install
npm run dev
```

**适用场景**：开发调试、代码修改、功能测试

📖 **详细步骤**：查看 [开发环境指南](docs/development-guide.md)

---

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [Docker部署](docs/docker-deployment.md) | Docker完整部署流程 |
| [部署后配置](docs/post-deployment-config.md) | 部署后必要配置（MQTT等） |
| [手动部署](docs/manual-deployment.md) | 传统手动部署方式 |
| [开发环境](docs/development-guide.md) | 本地开发环境配置 |
| [重新构建镜像](docs/rebuild-images.md) | Docker镜像重新编译 |
| [快速参考](docs/quick-reference.md) | 常用命令速查表 |

---

## 🔗 相关链接

- [项目主页](../README.md) - 项目介绍和特性
- [快速开始指南](../QUICK_START.md) - 5分钟上手教程
- [部署脚本](../script/deploy.sh) - 自动化部署工具
- [技术文档](../docs_技术文档/) - 深入技术文档
- [开发规范](../docs_开发规范/) - 代码规范指南

---

## 💡 选择建议

| 需求 | 推荐方式 | 查看文档 |
|------|---------|---------|
| 快速部署到生产 | Docker | [Docker部署](docs/docker-deployment.md) |
| 部署后配置设备 | - | [部署后配置](docs/post-deployment-config.md) ⚠️ |
| 本地开发调试 | 混合模式 | [开发环境](docs/development-guide.md) |
| 精细化控制 | 手动部署 | [手动部署](docs/manual-deployment.md) |
| 重新构建镜像 | - | [重新构建镜像](docs/rebuild-images.md) |
| 查找命令 | - | [快速参考](docs/quick-reference.md) |

---

**更新时间**：2026-01-17
