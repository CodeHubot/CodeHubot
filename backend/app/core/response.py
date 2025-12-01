"""
统一响应格式
提供标准的 API 响应格式，包含 code、message、data 字段
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """标准响应格式"""
    code: int = Field(..., description="状态码，200表示成功，其他值表示失败")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {}
            }
        }


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(..., description="错误状态码")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 400,
                "message": "请求参数错误",
                "detail": "具体错误信息"
            }
        }


def success_response(data: Any = None, message: str = "操作成功") -> dict:
    """创建成功响应"""
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(code: int, message: str, detail: Optional[str] = None) -> dict:
    """创建错误响应"""
    return {
        "code": code,
        "message": message,
        "detail": detail
    }

