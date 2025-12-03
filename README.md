<h1 align="center" style="border-bottom: none;">🤖 CodeHubot</h1>

<h3 align="center">AI-IoT 智能教学平台 | 跨学科项目制学习 | 软硬件全开源⚡️</h3>

<p align="center">
  <strong>让学生在真实硬件中学习 AI 技术</strong>
</p>

<p align="center">
  <a href="https://github.com/CodeHubot/CodeHubot/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
  </a>
  <a href="https://github.com/CodeHubot/CodeHubot/releases/latest">
    <img alt="GitHub Release" src="https://img.shields.io/github/v/release/CodeHubot/CodeHubot.svg">
  </a>
  <a href="https://github.com/CodeHubot/CodeHubot/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/CodeHubot/CodeHubot?style=flat-square">
  </a>
  <a href="https://github.com/CodeHubot/CodeHubot/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/CodeHubot/CodeHubot?style=flat-square">
  </a>

</p>


---

## 📖 项目简介

**CodeHubot** 是一个跨学科项目制的 AI-IoT 智能教学平台。平台通过将大语言模型与真实的 ESP32 物联网硬件结合，让学生能够动手搭建智能硬件系统、训练能听懂人话的 AI 助手。平台提供完整的智能体构建工具、物联网设备管理系统、开源硬件生态以及丰富的跨学科教学实验，支持项目式学习，让学生在创造真实作品的过程中理解 AI 和物联网技术，真正做到"让 AI 教学不再纸上谈兵"。

### 🎯 学习理念

- **🚀 动手做项目**：不只是学知识点，而是完成一个个真实的小项目
- **🔀 跨学科融合**：一个项目融合信息技术、物理、数学、生物等多个学科知识
- **💻 软硬结合**：既能看到代码运行效果，又能看到 LED 灯真的亮了
- **🎓 边做边学**：通过动手实践来理解原理，而不是死记硬背


## ✨ 平台特色

### 🚀 做真实的项目
- **完整流程体验**：从想法 → 设计 → 编程 → 测试 → 改进，就像真正的工程师
- **解决实际问题**：做智能台灯、自动浇花、温度监控等有用的东西
- **看得见的成果**：每个项目都能演示给家人朋友看
- **可以创新**：在项目基础上加入自己的想法
- **培养能力**：学会分析问题、动手解决问题

### 🔀 融合多学科知识
- **📘 信息技术**：学编程、做网页、设计数据库
- **📗 物理知识**：认识传感器、连接电路、理解电磁通信
- **📕 数学应用**：数据统计分析、绘制图表、算法设计
- **📙 生物实践**：监测植物生长环境、理解温湿度影响
- **🤖 AI 技术**：让设备听懂人话、自动做决定、预测趋势
- **🔧 动手能力**：搭建硬件、焊接电路、调试排错

### 🎓 容易上手
- **零基础也能学**：提供可视化操作界面，不需要先学很多理论
- **循序渐进**：从最简单的控制灯开始，一步步做更复杂的项目
- **即时反馈**：写完代码马上能看到效果
- **完全免费开源**：可以随意修改和使用

### 🤖 能做什么？（AI 功能）
- **智能体管理**：创建和管理多个 AI 智能体，配置不同的提示词和插件
- **插件系统**：支持 OpenAPI 3.0 格式插件，轻松扩展 AI 能力
- **对话控制设备**：对着智能体说"把灯打开"，灯就真的亮了
- **智能分析**：AI 自动分析温度数据，告诉你规律
- **自动化场景**：说一句话就能设置"回家自动开灯"
- **预测功能**：根据历史数据预测明天的温度



## 💻 技术栈

| 模块 | 技术 | 说明 |
|------|-----|------|
| **前端** | Vue 3 + Vite + Element Plus | 现代化 UI 框架 |
| **后端** | FastAPI + SQLAlchemy + Pydantic | 高性能 Python Web 框架 |
| **AI** | Deepseek/通义千问/文心一言/智谱GLM/Kimi/混元/豆包等 | 全面支持国产大模型 |
| **插件服务** ⭐ | plugin-service + plugin-backend | 双层架构，性能提升 |
| **数据库** | MySQL 8.0 | 关系型数据库 |
| **消息队列** | MQTT (Mosquitto) | 物联网标准通信协议 |
| **反向代理** | Nginx | Web 服务器和负载均衡 |
| **容器化** | Docker + Docker Compose | 容器化部署方案 |


## 🚀 一键部署

### 前置要求

- Docker 20.10+ 和 Docker Compose 2.0+
- 至少 4GB 内存和 20GB 磁盘空间

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/CodeHubot/CodeHubot.git CodeHubot
cd CodeHubot

# 2. 配置环境变量（使用新架构配置）
cd docker
cp .env.example .env
nano .env  # 设置 MYSQL_PASSWORD, SECRET_KEY, ADMIN_PASSWORD 等

# 重要：首次部署时，建议设置管理员账号：
# ADMIN_USERNAME=admin          # 管理员用户名（默认：admin）
# ADMIN_PASSWORD=your_password  # 管理员密码（必须设置才会自动创建）
# ADMIN_EMAIL=admin@example.com # 管理员邮箱（可选）

# 3. 一键部署（包含新的 plugin-backend-service）
docker-compose -f docker-compose.plugin.yml up -d

# 或使用旧配置（不推荐）
cp .env.example .env
cd ..
./deploy.sh deploy
```

部署完成后访问：
- **前端**: http://localhost:80
- **后端 API**: http://localhost/api (通过nginx反向代理，8000端口不对外暴露)
- **API 文档**: http://localhost/api/docs (通过nginx访问)
- **Plugin Service**: http://localhost:9000 (插件对外接口)
- **Plugin Backend**: http://localhost:9002 (插件内部服务) 

📖 **详细部署文档**：
- [完整部署指南](deploy/DEPLOYMENT_COMPLETE_GUIDE.md) ⭐ 推荐
- [快速开始](deploy/QUICK_START_PLUGIN_BACKEND.md)
- [Docker 部署](deploy/docs/docker-deployment.md)

---

## 🎬 案例展示





## 🤝 参与贡献

欢迎教师、学生、开发者参与改进本平台！

### 如何贡献
- 📝 **完善文档**：改进教程、修正错误
- 🔬 **分享实验**：分享你设计的教学实验
- 🐛 **报告问题**：提交 [Issues](https://github.com/CodeHubot/CodeHubot/issues)
- 💻 **贡献代码**：提交 Pull Request

### 贡献者
感谢所有为本项目做出贡献的教师、学生和开发者！


## 📄 开源协议

本项目所有**软件代码**采用 [MIT License](https://github.com/CodeHubot/CodeHubot/blob/main/LICENSE)

- ✅ 前端代码（Vue 3）
- ✅ 后端代码（FastAPI）
- ✅ 固件代码（ESP-IDF）
- ✅ 可以自由使用、修改
- ✅ 可以用于教学和科研
- ✅ 可以商业使用
- ✅ 只需保留版权声明


---

<div align="center">

**⭐ 如果本项目对你的教学有帮助，请给个 Star 支持一下！**

**让更多教师发现这个平台，一起推动 AI 教育 🚀**

**CodeHubot** - 让 AI 教学不再纸上谈兵

Made with ❤️ for AI Education

</div>
