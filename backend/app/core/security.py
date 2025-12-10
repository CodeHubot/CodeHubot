from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文 - 支持bcrypt和pbkdf2_sha256算法
# bcrypt 用于新密码（更安全），pbkdf2_sha256 用于兼容旧密码
pwd_context = CryptContext(
    schemes=["bcrypt", "pbkdf2_sha256"],
    deprecated="auto"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密码验证失败: {e}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
        
    Note:
        - bcrypt 有 72 字节的密码长度限制
        - 对于超过 72 字节的密码，自动使用 pbkdf2_sha256
        - 对于 72 字节以内的密码，优先使用 bcrypt（更安全）
    """
    try:
        # 检查密码长度（以字节计算）
        password_bytes = password.encode('utf-8')
        
        if len(password_bytes) > 72:
            # 密码太长，使用 pbkdf2_sha256（无长度限制）
            logger.info(f"密码长度超过72字节({len(password_bytes)}字节)，使用pbkdf2_sha256算法")
            return pwd_context.hash(password, scheme="pbkdf2_sha256")
        else:
            # 密码长度合适，使用 bcrypt（更安全）
            return pwd_context.hash(password, scheme="bcrypt")
            
    except Exception as e:
        logger.error(f"密码哈希失败: {e}", exc_info=True)
        logger.error(f"密码长度: {len(password.encode('utf-8'))} 字节")
        # 如果 bcrypt 失败，尝试使用 pbkdf2_sha256 作为后备方案
        try:
            logger.warning("尝试使用 pbkdf2_sha256 作为后备方案")
            return pwd_context.hash(password, scheme="pbkdf2_sha256")
        except Exception as fallback_e:
            logger.error(f"后备方案也失败: {fallback_e}", exc_info=True)
            raise ValueError("密码哈希失败")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建access token
    
    注意：如果 data 中已包含 "type" 字段，将使用该值，否则默认为 "access"
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # 如果 data 中没有 type 字段，才设置为 "access"
    if "type" not in to_encode:
        to_encode["type"] = "access"
    
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建refresh token
    
    Args:
        data: token中包含的数据
        expires_delta: 自定义过期时间
        
    Returns:
        str: 编码后的JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: Optional[str] = "access") -> dict:
    """验证token
    
    Args:
        token: JWT token
        token_type: token类型（access、refresh、password_reset 等）。如果为 None，则不验证类型
        
    Returns:
        dict: token payload
        
    Raises:
        HTTPException: token无效或类型不匹配
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # 如果指定了 token_type，验证类型是否匹配
        if token_type is not None:
            payload_type = payload.get("type")
            if payload_type != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"无效的token类型，期望: {token_type}，实际: {payload_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return payload
    except HTTPException:
        # 重新抛出 HTTPException（类型不匹配）
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_internal_api_key(api_key: str) -> bool:
    """验证内部API密钥
    
    用于内部服务（如plugin-service）调用后端API时的认证
    
    Args:
        api_key: 内部API密钥
        
    Returns:
        bool: 密钥是否有效
    """
    # 从配置中获取内部API密钥
    internal_api_key = getattr(settings, 'internal_api_key', None)
    
    # 如果未配置内部API密钥，则不允许访问
    if not internal_api_key:
        logger.warning("未配置内部API密钥，拒绝访问")
        return False
    
    # 验证密钥是否匹配
    return api_key == internal_api_key
