# API 测试方法和工具

## 概述

API 测试是确保后端接口正确性和稳定性的重要环节。本文档介绍在 CodeHubot 项目中使用的 API 测试方法和工具，适合教学使用。

## 测试工具对比

| 工具 | 类型 | 适用场景 | 学习曲线 | 推荐度 |
|------|------|---------|---------|--------|
| **Postman** | GUI工具 | 手动测试、接口调试 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Apifox** | GUI工具 | 接口文档+测试（国产） | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **curl** | 命令行 | 快速测试、脚本自动化 | ⭐ | ⭐⭐⭐⭐ |
| **httpie** | 命令行 | 命令行测试（更友好） | ⭐ | ⭐⭐⭐⭐ |
| **pytest** | 代码框架 | 自动化测试、CI/CD | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **FastAPI TestClient** | 代码 | 单元测试 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 1. FastAPI 自动文档

### Swagger UI

FastAPI 自动生成交互式 API 文档，这是最快速的测试方法。

**访问地址**: http://localhost:8000/docs

**功能**：
- ✅ 查看所有 API 端点
- ✅ 查看请求/响应格式
- ✅ 在线测试 API
- ✅ 查看数据模型

**使用步骤**：

```
1. 打开浏览器访问 /docs
2. 找到要测试的接口
3. 点击 "Try it out"
4. 填写参数
5. 点击 "Execute"
6. 查看响应结果
```

**示例**：

```python
# 定义 API 时添加详细文档
@router.post(
    "/users",
    response_model=UserResponse,
    tags=["用户管理"],
    summary="创建用户",
    description="""
    创建新用户账号
    
    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6字符）
    """
)
async def create_user(user: UserCreate):
    """创建用户"""
    return user
```

### ReDoc

更美观的 API 文档展示。

**访问地址**: http://localhost:8000/redoc

## 2. Postman/Apifox 测试

### Postman 基础使用

#### 安装
- 官网下载：https://www.postman.com/downloads/
- 或使用 Web 版本

#### 创建请求

```
1. 新建 Request
2. 设置请求方法（GET/POST/PUT/DELETE）
3. 输入 URL
4. 设置请求头
5. 设置请求体
6. 发送请求
```

#### GET 请求示例

```
方法: GET
URL: http://localhost:8000/api/devices
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Query Params:
  page: 1
  size: 20
```

#### POST 请求示例

```
方法: POST
URL: http://localhost:8000/api/auth/login
Headers:
  Content-Type: application/json

Body (JSON):
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

### 环境变量

在 Postman 中使用环境变量，避免重复输入：

```javascript
// 环境变量
{
  "base_url": "http://localhost:8000",
  "access_token": ""
}

// 在请求中使用
URL: {{base_url}}/api/devices
Headers:
  Authorization: Bearer {{access_token}}
```

### 测试脚本

Postman 支持编写测试脚本：

```javascript
// Tests 标签页
pm.test("状态码为 200", function () {
    pm.response.to.have.status(200);
});

pm.test("响应时间小于 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

pm.test("返回成功标志", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(true);
});

// 保存 token 到环境变量
var jsonData = pm.response.json();
pm.environment.set("access_token", jsonData.data.access_token);
```

### Collection（集合）

将相关的 API 组织成集合：

```
CodeHubot API
├── 认证
│   ├── 用户登录
│   ├── 刷新 Token
│   └── 登出
├── 用户管理
│   ├── 创建用户
│   ├── 获取用户列表
│   ├── 获取用户详情
│   ├── 更新用户
│   └── 删除用户
└── 设备管理
    ├── 创建设备
    ├── 获取设备列表
    └── ...
```

### Apifox 特色功能

Apifox 是国产工具，集成了接口文档、测试、Mock 等功能。

**特点**：
- ✅ 接口文档自动生成
- ✅ 数据 Mock
- ✅ 自动化测试
- ✅ 团队协作
- ✅ 中文界面

## 3. 命令行测试

### curl

最基础的命令行 HTTP 工具：

```bash
# GET 请求
curl http://localhost:8000/api/devices

# GET 请求（带查询参数）
curl "http://localhost:8000/api/devices?page=1&size=20"

# GET 请求（带 Token）
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/devices

# POST 请求（JSON）
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"admin123"}' \
     http://localhost:8000/api/auth/login

# POST 请求（表单）
curl -X POST \
     -F "file=@document.pdf" \
     http://localhost:8000/api/documents

# PUT 请求
curl -X PUT \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"name":"新设备名"}' \
     http://localhost:8000/api/devices/1

# DELETE 请求
curl -X DELETE \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/devices/1

# 显示响应头
curl -i http://localhost:8000/api/devices

# 只显示响应头
curl -I http://localhost:8000/api/devices

# 保存响应到文件
curl -o response.json http://localhost:8000/api/devices

# 显示详细信息
curl -v http://localhost:8000/api/devices
```

### httpie

更友好的命令行 HTTP 客户端：

```bash
# 安装
pip install httpie

# GET 请求
http GET localhost:8000/api/devices

# GET 请求（带查询参数）
http GET localhost:8000/api/devices page==1 size==20

# GET 请求（带 Token）
http GET localhost:8000/api/devices \
     Authorization:"Bearer YOUR_TOKEN"

# POST 请求（JSON）
http POST localhost:8000/api/auth/login \
     email=admin@example.com \
     password=admin123

# POST 请求（文件上传）
http -f POST localhost:8000/api/documents \
     file@document.pdf

# PUT 请求
http PUT localhost:8000/api/devices/1 \
     Authorization:"Bearer YOUR_TOKEN" \
     name="新设备名"

# DELETE 请求
http DELETE localhost:8000/api/devices/1 \
     Authorization:"Bearer YOUR_TOKEN"

# 只显示响应头
http --headers localhost:8000/api/devices

# 只显示响应体
http --body localhost:8000/api/devices

# 下载文件
http --download localhost:8000/api/export/data.csv
```

## 4. Python 测试（pytest）

### 安装

```bash
pip install pytest
pip install httpx  # FastAPI 测试客户端依赖
```

### FastAPI TestClient

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CodeHubot API"}

def test_create_user():
    """测试创建用户"""
    response = client.post(
        "/api/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["username"] == "testuser"

def test_login():
    """测试登录"""
    # 先创建用户
    client.post("/api/users", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # 登录
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
```

### 使用 Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import Base, engine

@pytest.fixture(scope="module")
def test_client():
    """创建测试客户端"""
    # 创建测试数据库
    Base.metadata.create_all(bind=engine)
    
    client = TestClient(app)
    yield client
    
    # 清理
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_user(test_client):
    """创建测试用户"""
    response = test_client.post(
        "/api/users",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    return response.json()["data"]

@pytest.fixture(scope="module")
def auth_token(test_client, test_user):
    """获取认证 Token"""
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]

# tests/test_api.py
def test_get_devices(test_client, auth_token):
    """测试获取设备列表（需要认证）"""
    response = test_client.get(
        "/api/devices",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

### 参数化测试

```python
import pytest

@pytest.mark.parametrize("username,email,password,expected_status", [
    ("user1", "user1@example.com", "pass123", 200),  # 正常
    ("", "user2@example.com", "pass123", 422),        # 用户名为空
    ("user3", "invalid-email", "pass123", 422),       # 邮箱格式错误
    ("user4", "user4@example.com", "12345", 422),     # 密码太短
])
def test_create_user_validation(test_client, username, email, password, expected_status):
    """测试用户创建验证"""
    response = test_client.post(
        "/api/users",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    assert response.status_code == expected_status
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_api.py

# 运行特定测试
pytest tests/test_api.py::test_create_user

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s

# 生成覆盖率报告
pytest --cov=app tests/

# 并行运行测试
pytest -n auto
```

## 5. 性能测试

### 使用 locust

```bash
# 安装
pip install locust
```

```python
# locustfile.py
from locust import HttpUser, task, between

class CodeHubotUser(HttpUser):
    wait_time = between(1, 3)  # 等待1-3秒
    
    def on_start(self):
        """登录获取 Token"""
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        self.token = response.json()["access_token"]
    
    @task(3)  # 权重为3
    def get_devices(self):
        """获取设备列表"""
        self.client.get(
            "/api/devices",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)  # 权重为1
    def create_device(self):
        """创建设备"""
        self.client.post(
            "/api/devices",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "name": "Test Device",
                "device_type": "ESP32"
            }
        )
```

```bash
# 启动性能测试
locust -f locustfile.py

# 访问 http://localhost:8089
# 设置用户数和增长速率
```

## 6. 集成测试

### GitHub Actions CI/CD

```yaml
# .github/workflows/test.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpass
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest --cov=app tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 测试最佳实践

### 1. 测试金字塔

```
        /\
       /  \  E2E 测试（少量）
      /────\
     /      \ 集成测试（适量）
    /────────\
   /          \ 单元测试（大量）
  /────────────\
```

### 2. 测试命名

```python
# ✅ 好的命名
def test_create_user_with_valid_data_returns_200():
    pass

def test_login_with_invalid_password_returns_401():
    pass

# ❌ 不好的命名
def test_user():
    pass

def test_1():
    pass
```

### 3. AAA 模式

```python
def test_create_device():
    # Arrange（准备）
    user = create_test_user()
    token = get_auth_token(user)
    device_data = {
        "name": "Test Device",
        "device_type": "ESP32"
    }
    
    # Act（执行）
    response = client.post(
        "/api/devices",
        headers={"Authorization": f"Bearer {token}"},
        json=device_data
    )
    
    # Assert（断言）
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Test Device"
```

### 4. 独立性

```python
# ✅ 每个测试独立
def test_a():
    # 自己准备数据
    user = create_user()
    # 测试
    # 清理数据

def test_b():
    # 自己准备数据
    user = create_user()
    # 测试
    # 清理数据

# ❌ 测试相互依赖
shared_user = None

def test_a():
    global shared_user
    shared_user = create_user()

def test_b():
    # 依赖 test_a 的结果
    assert shared_user is not None
```

## CodeHubot 项目测试示例

```python
# tests/test_device_api.py
import pytest
from fastapi.testclient import TestClient

class TestDeviceAPI:
    """设备 API 测试"""
    
    def test_list_devices(self, client, auth_headers):
        """测试获取设备列表"""
        response = client.get("/api/devices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_create_device(self, client, auth_headers):
        """测试创建设备"""
        device_data = {
            "name": "测试设备",
            "device_type": "ESP32",
            "description": "这是一个测试设备"
        }
        response = client.post(
            "/api/devices",
            headers=auth_headers,
            json=device_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["name"] == "测试设备"
    
    def test_get_device_detail(self, client, auth_headers, test_device):
        """测试获取设备详情"""
        device_id = test_device["id"]
        response = client.get(
            f"/api/devices/{device_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == device_id
    
    def test_update_device(self, client, auth_headers, test_device):
        """测试更新设备"""
        device_id = test_device["id"]
        update_data = {"name": "更新后的设备名"}
        
        response = client.put(
            f"/api/devices/{device_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "更新后的设备名"
    
    def test_delete_device(self, client, auth_headers, test_device):
        """测试删除设备"""
        device_id = test_device["id"]
        
        response = client.delete(
            f"/api/devices/{device_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # 验证已删除
        response = client.get(
            f"/api/devices/{device_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
```

## 教学要点总结

### 测试类型
1. **手动测试**：Postman/Apifox
2. **单元测试**：pytest + TestClient
3. **集成测试**：数据库 + API
4. **性能测试**：locust
5. **自动化测试**：CI/CD

### 测试工具选择
- 🔰 **初学者**：FastAPI Docs + Postman
- 👨‍💻 **开发者**：pytest + TestClient
- 🏢 **团队协作**：Apifox + CI/CD
- ⚡ **性能测试**：locust

### 最佳实践
- ✅ 测试独立性
- ✅ AAA 模式
- ✅ 合理的测试覆盖率
- ✅ 持续集成

## 相关文档

- [FastAPI框架](../05_核心技术/FastAPI框架.md) - API 开发
- [调试技巧](./调试技巧.md) - 调试方法
- [API开发规范](../../docs_开发规范/01_API开发规范.md) - API 规范
