<h1 align="center" style="border-bottom: none;">🤖 CodeHubot</h1>

<h3 align="center">AIoT智能体开发与管理平台 | 软硬件全栈 | 开源⚡️</h3>

<p align="center">
  <strong>让物联网设备拥有AI智能体的思维能力</strong>
</p>

<p align="center">
  <a href="https://gitee.com/codehubot/CodeHubot/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
  </a>
  <a href="https://gitee.com/codehubot/CodeHubot/releases/latest">
    <img alt="Gitee Release" src="https://gitee.com/codehubot/CodeHubot/badge/star.svg?theme=dark" alt="star">
  </a>
  <a href="https://gitee.com/codehubot/CodeHubot/members">
    <img alt="Gitee forks" src="https://gitee.com/codehubot/CodeHubot/badge/fork.svg?theme=dark" alt="fork">
  </a>
</p>


---

## 🚀 快速开始

### 最简单的部署方式（5分钟上手）

```bash
# 1. 克隆项目
git clone https://gitee.com/codehubot/CodeHubot.git
cd CodeHubot

# 2. 配置环境变量
cd docker
cp .env.example .env
# 编辑 .env 文件，修改必要配置

# 3. 一键启动
./script/deploy.sh
```

> 📖 **部署后重要配置**：如果使用物联网设备功能，需要在管理平台中配置设备MQTT服务器地址（系统管理 -> MQTT配置）。详见 [快速开始指南](QUICK_START.md)。

📖 **详细教程**：[5分钟快速开始指南](QUICK_START.md)

### 前提条件

- Docker 和 Docker Compose
- Python 3.8+（可选，仅本地开发需要）
- 阿里云 DashScope API Key（用于AI功能）

---

## 📖 项目简介

**CodeHubot** 是一个开源的 AIoT 智能体开发与管理平台。平台将大语言模型智能体（AI Agent）与物联网设备（IoT）深度融合，提供完整的智能体构建工具链、设备管理系统和工作流编排能力。用户可以轻松创建具有推理能力的 AI 智能体，并通过 MQTT 协议让智能体与 ESP32 等物联网设备实时交互，实现真正的"智能物联"。

### 🎯 核心理念

- **🤖 智能体优先**：不只是对话机器人，而是能感知、推理、决策、执行的完整智能体
- **🔗 软硬一体**：AI智能体与物联网设备无缝连接，实现端到端的智能化
- **🛠️ 全栈开发**：从前端界面、后端服务、智能体编排到硬件固件，全栈开源
- **⚡ 开箱即用**：Docker一键部署，5分钟即可拥有自己的智能体平台


## ✨ 平台特色

### 🤖 完整的智能体开发工具链
- **对话式智能体**：基于大语言模型，支持自然语言交互
- **知识库增强**：RAG技术让智能体拥有领域知识
- **插件扩展**：通过插件系统扩展智能体的感知和执行能力
- **工作流编排**：可视化编排智能体的推理和决策流程
- **提示词工程**：内置提示词模板库，快速构建专业智能体

### 🌐 AIoT深度融合
- **实时设备控制**：智能体通过MQTT直接控制物联网设备
- **设备数据感知**：智能体实时获取传感器数据进行推理
- **双向通信**：设备可主动上报状态，智能体可下发指令
- **多设备协同**：一个智能体可同时管理多个IoT设备
- **边缘智能**：支持ESP32等边缘设备本地运行轻量级AI

### 🔧 完善的设备管理系统
- **产品建模**：灵活的产品模型定义，支持各类IoT设备
- **远程管理**：在线状态监控、远程配置、OTA升级
- **数据可视化**：设备数据实时展示、历史数据图表分析
- **固件管理**：支持多版本固件管理和在线烧录
- **MQTT集成**：内置Mosquitto服务，开箱即用

### 🎯 开箱即用
- **快速部署**：Docker一键部署，5分钟启动
- **文档完善**：详细的API文档和使用指南
- **即时反馈**：实时查看设备状态和智能体响应
- **完全开源**：MIT协议，可自由使用和修改

### 🤖 AI智能体能力
- **智能体管理**：创建和管理多个 AI 智能体，配置不同的提示词和插件
- **插件系统**：支持 OpenAPI 3.0 格式插件，轻松扩展 AI 能力
- **对话控制设备**：通过自然语言控制IoT设备
- **智能分析**：AI 自动分析设备数据，发现规律和趋势
- **自动化场景**：基于智能体的场景编排和自动化执行
- **数据预测**：根据历史数据进行智能预测



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


## 🚀 快速开始

📖 **部署文档**：请查看 [部署指南](DEPLOYMENT_SUMMARY.md) 了解详细的部署步骤和配置说明。

---

## 🎬 案例展示





## 🤝 参与贡献

欢迎开发者参与改进本平台！

### 如何贡献
- 📝 **完善文档**：改进文档、修正错误
- 🔬 **分享案例**：分享你的应用案例
- 🐛 **报告问题**：提交 [Issues](https://gitee.com/codehubot/CodeHubot/issues)
- 💻 **贡献代码**：提交 Pull Request

### 代码仓库
- 🇨🇳 **Gitee（主仓库）**：https://gitee.com/codehubot/CodeHubot
- 🌐 **GitHub（镜像）**：https://github.com/CodeHubot/CodeHubot

### 贡献者
感谢所有为本项目做出贡献的开发者！


## 📄 开源协议

本项目所有**软件代码**采用 [MIT License](https://gitee.com/codehubot/CodeHubot/blob/main/LICENSE)

- ✅ 前端代码（Vue 3）
- ✅ 后端代码（FastAPI）
- ✅ 固件代码（ESP-IDF）
- ✅ 可以自由使用、修改
- ✅ 可以商业使用
- ✅ 只需保留版权声明


---

<div align="center">

**⭐ 如果本项目对你有帮助，请给个 Star 支持一下！**

**让更多开发者发现这个平台，一起推动 AIoT 技术发展 🚀**

**CodeHubot** - AIoT智能体开发与管理平台

Made with ❤️ by CodeHubot Team

</div>
