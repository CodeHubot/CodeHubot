# Git 工作流程说明

## 📋 仓库配置

### 远程仓库

```bash
origin   → git@github.com:zhangqx2025/CodeHubot.git  (你的 fork)
upstream → git@github.com:CodeHubot/CodeHubot.git     (原仓库)
```

### 工作流程

```
1. 本地开发
   ↓
2. 提交到你的 fork (origin)
   ↓
3. 创建 Pull Request 到原仓库 (upstream)
   ↓
4. 代码审查和合并
```

## 🚀 日常工作流程

### 1. 开始新功能/修复

```bash
# 同步上游最新代码
git fetch upstream
git checkout main
git merge upstream/main

# 创建新分支（可选，推荐）
git checkout -b feature/your-feature-name
```

### 2. 开发和提交

```bash
# 查看修改
git status

# 添加修改
git add .

# 提交
git commit -m "feat: 你的功能描述"

# 推送到你的 fork
git push origin main
# 或推送到功能分支
git push origin feature/your-feature-name
```

### 3. 创建 Pull Request

1. 访问你的 fork：https://github.com/zhangqx2025/CodeHubot
2. 点击 "Pull requests" → "New pull request"
3. 选择：
   - **base repository**: `CodeHubot/CodeHubot`
   - **base branch**: `main`
   - **head repository**: `zhangqx2025/CodeHubot`
   - **compare branch**: `main` 或你的功能分支
4. 填写 PR 标题和描述
5. 点击 "Create pull request"

### 4. 保持同步

定期同步上游仓库的最新代码：

```bash
# 拉取上游最新代码
git fetch upstream

# 合并到本地 main
git checkout main
git merge upstream/main

# 推送到你的 fork
git push origin main
```

## 📝 提交信息规范

使用语义化提交信息：

```bash
feat:     新功能
fix:      修复bug
docs:     文档修改
style:    代码格式（不影响功能）
refactor: 重构（不增加功能，不修复bug）
perf:     性能优化
test:     测试相关
chore:    构建/工具相关
```

**示例**：
```bash
git commit -m "feat: 新增设备批量导入功能"
git commit -m "fix: 修复传感器数据查询失败的问题"
git commit -m "docs: 更新部署文档"
```

## 🔄 常用命令

### 查看远程仓库
```bash
git remote -v
```

### 查看当前分支
```bash
git branch
```

### 切换分支
```bash
git checkout branch-name
```

### 创建并切换到新分支
```bash
git checkout -b new-branch-name
```

### 查看提交历史
```bash
git log --oneline -10
```

### 查看某次提交的详情
```bash
git show commit-hash
```

### 撤销工作区修改
```bash
git restore file-name
```

### 撤销暂存区文件
```bash
git restore --staged file-name
```

## 🛠️ 解决冲突

如果合并时出现冲突：

```bash
# 1. 拉取上游最新代码
git fetch upstream
git merge upstream/main

# 2. 如果有冲突，手动解决
# 编辑冲突文件，移除冲突标记：
# <<<<<<< HEAD
# =======
# >>>>>>> upstream/main

# 3. 标记冲突已解决
git add .

# 4. 完成合并
git commit

# 5. 推送到你的 fork
git push origin main
```

## 📚 参考资料

### GitHub Fork 工作流
- [GitHub 官方文档](https://docs.github.com/cn/get-started/quickstart/fork-a-repo)
- [贡献开源项目指南](https://docs.github.com/cn/get-started/quickstart/contributing-to-projects)

### Git 命令参考
- [Git 官方文档](https://git-scm.com/doc)
- [Git 备忘清单](https://training.github.com/downloads/zh_CN/github-git-cheat-sheet/)

## ⚠️ 注意事项

1. **不要直接推送到 upstream**
   - 你没有直接推送到原仓库的权限
   - 所有更改都应该通过 Pull Request

2. **保持 fork 同步**
   - 定期同步上游代码：`git fetch upstream && git merge upstream/main`
   - 避免 fork 落后太多

3. **代码审查**
   - 创建 PR 后，等待代码审查
   - 根据反馈修改代码
   - 修改后推送到同一分支会自动更新 PR

4. **分支管理**
   - 大功能建议使用独立分支
   - 小修改可以直接在 main 分支

## 🎯 快速参考

```bash
# 日常提交流程（最常用）
git add .
git commit -m "feat: 你的功能"
git push origin main

# 同步上游代码（定期执行）
git fetch upstream
git merge upstream/main
git push origin main

# 创建 PR
访问 https://github.com/zhangqx2025/CodeHubot
点击 "Pull requests" → "New pull request"
```

---

**配置完成！** 现在你可以安全地向自己的 fork 提交代码，然后创建 PR 到原仓库。🎉

