<h1 align="center" style="border-bottom: none;">🤖 CodeHubot</h1>

<h3 align="center">AI-IoT 智能教学平台 | 跨学科项目制学习 | 软硬件全开源⚡️</h3>

<p align="center">
  <strong>让学生在真实硬件中学习 AI 技术</strong>
</p>

<p align="center">
  <a href="https://github.com/codehubot/codehubot/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
  </a>
  <a href="https://github.com/codehubot/codehubot/releases/latest">
    <img alt="GitHub Release" src="https://img.shields.io/github/v/release/codehubot/codehubot.svg">
  </a>
  <a href="https://github.com/codehubot/codehubot/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/codehubot/codehubot?style=flat-square">
  </a>
  <a href="https://github.com/codehubot/codehubot/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/codehubot/codehubot?style=flat-square">
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

### 💡 为什么有趣？

| 传统学习方式 | 在本平台学习 |
|------------|-------------|
| ❌ 只能在屏幕上看结果 | ✅ 控制真实的灯光、电机、传感器 |
| ❌ 不知道学了有什么用 | ✅ 做出能演示的智能设备 |
| ❌ 一堆理论公式 | ✅ 边做边学，立刻看到效果 |
| ❌ 考完就忘 | ✅ 有自己的作品，有成就感 |


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
- **对话控制设备**：对着智能体说"把灯打开"，灯就真的亮了
- **智能分析**：AI 自动分析温度数据，告诉你规律
- **自动化场景**：说一句话就能设置"回家自动开灯"
- **预测功能**：根据历史数据预测明天的温度



## 💻 技术栈

| 模块 | 技术 | 说明 |
|------|-----|------|
| **前端** | Vue 3 + Element Plus | 现代化 UI |
| **后端** | FastAPI + SQLAlchemy | 高性能 Python |
| **AI** | OpenAI/Claude/千问 + LangChain | 多模型支持 |
| **固件** | ESP-IDF + FreeRTOS | 乐鑫官方框架 |
| **数据库** | MySQL + Redis | 数据持久化和缓存 |
| **通信** | MQTT (Mosquitto) | 物联网标准协议 |
| **部署** | Docker + Nginx | 容器化部署 |


### 📦 多仓库架构

为了更好的模块化管理，本项目采用多仓库架构：


| 仓库 | 说明 | Stars |
|------|------|-------|
| **[🏠 主仓库](https://github.com/codehubot/codehubot)** | 管理后台、后端 API、插件、系统服务 | ![Stars](https://img.shields.io/github/stars/codehubot/codehubot?style=social) |
| **[🤖 智能体平台](https://github.com/codehubot/agent-platform)** | AI 智能体构建、工作流、知识库 | ![Stars](https://img.shields.io/github/stars/codehubot/agent-platform?style=social) |
| **[🔌 固件仓库](https://github.com/codehubot/firmware)** | ESP32 固件、硬件资料 | ![Stars](https://img.shields.io/github/stars/codehubot/firmware?style=social) |



**如何选择？**
- 📊 **只需要管理设备**？→ 克隆主仓库
- 🤖 **想开发 AI 智能体**？→ 克隆智能体平台
- 🔧 **需要硬件开发**？→ 克隆固件仓库
- 🎓 **完整教学使用**？→ 三个仓库都需要

**为什么分仓库？**
- ✅ **模块独立**：各模块可以独立开发和维护
- ✅ **版本管理**：固件和智能体平台有独立的版本号
- ✅ **易于使用**：只需要某个功能的用户可以只下载对应仓库
- ✅ **降低复杂度**：避免单个仓库过于庞大
- ✅ **专注性强**：硬件开发者、AI 开发者可以专注各自领域


## 🎬 案例展示





## 🤝 参与贡献

欢迎教师、学生、开发者参与改进本平台！

### 如何贡献
- 📝 **完善文档**：改进教程、修正错误
- 🔬 **分享实验**：分享你设计的教学实验
- 🐛 **报告问题**：提交 [Issues](https://github.com/codehubot/codehubot/issues)
- 💻 **贡献代码**：提交 Pull Request
- 💬 **交流讨论**：加入以下QQ交流群

### 贡献者
感谢所有为本项目做出贡献的教师、学生和开发者！


## 📄 开源协议

本项目所有**软件代码**采用 [MIT License](https://github.com/codehubot/codehubot/blob/main/LICENSE)

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
