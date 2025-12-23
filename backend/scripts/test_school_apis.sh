#!/bin/bash
# 测试学校相关API的脚本
# 使用方法：./test_school_apis.sh <TOKEN>

if [ -z "$1" ]; then
    echo "使用方法: $0 <ACCESS_TOKEN>"
    echo "示例: $0 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    exit 1
fi

TOKEN="$1"
BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "=========================================="
echo "测试学校相关API"
echo "=========================================="
echo ""

# 测试1: 获取当前学校信息
echo "测试1: 获取当前管理员所属学校信息"
echo "GET $BASE_URL/pbl/school/my-school/info"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/my-school/info" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# 保存学校UUID供后续使用
SCHOOL_UUID=$(curl -s -X GET "$BASE_URL/pbl/school/my-school/info" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['uuid'])")

echo "当前学校UUID: $SCHOOL_UUID"
echo ""
echo ""

# 测试2: 使用新API获取学校用户列表
echo "测试2: 获取当前学校的用户列表（使用便捷API）"
echo "GET $BASE_URL/pbl/school/my-school/users?skip=0&limit=5"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/my-school/users?skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# 测试3: 使用旧API但传入正确的UUID
echo "测试3: 使用旧API获取学校用户列表（传入正确的UUID）"
echo "GET $BASE_URL/pbl/school/$SCHOOL_UUID/users?skip=0&limit=5"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/$SCHOOL_UUID/users?skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# 测试4: 使用旧API但传入错误的UUID（应该返回友好的错误信息）
echo "测试4: 使用旧API传入错误的UUID（测试错误提示）"
echo "GET $BASE_URL/pbl/school/wrong-uuid-123/users"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/wrong-uuid-123/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# 测试5: 角色筛选（只看学生）
echo "测试5: 角色筛选 - 只查看学生"
echo "GET $BASE_URL/pbl/school/my-school/users?role=student&limit=5"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/my-school/users?role=student&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# 测试6: 关键词搜索
echo "测试6: 关键词搜索"
echo "GET $BASE_URL/pbl/school/my-school/users?keyword=admin&limit=5"
echo "------------------------------------------"
curl -s -X GET "$BASE_URL/pbl/school/my-school/users?keyword=admin&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "测试完成！"
echo "=========================================="

