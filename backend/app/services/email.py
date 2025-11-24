from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 邮件配置（延迟初始化，只有在配置完整时才创建）
_conf: Optional[ConnectionConfig] = None
_fastmail: Optional[FastMail] = None

def _get_mail_config() -> Optional[ConnectionConfig]:
    """获取邮件配置，如果配置不完整则返回 None"""
    global _conf
    if _conf is not None:
        return _conf
    
    # 检查必需的邮件配置
    if not all([settings.mail_username, settings.mail_password, settings.mail_from]):
        logger.warning("邮件配置不完整，邮件功能已禁用")
        return None
    
    try:
        _conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_tls,
            MAIL_SSL_TLS=settings.mail_ssl,
            USE_CREDENTIALS=settings.use_credentials,
            VALIDATE_CERTS=settings.validate_certs
        )
        return _conf
    except Exception as e:
        logger.error(f"创建邮件配置失败: {e}")
        return None

def _get_fastmail() -> Optional[FastMail]:
    """获取 FastMail 实例，如果配置不完整则返回 None"""
    global _fastmail
    if _fastmail is not None:
        return _fastmail
    
    conf = _get_mail_config()
    if conf is None:
        return None
    
    try:
        _fastmail = FastMail(conf)
        return _fastmail
    except Exception as e:
        logger.error(f"创建 FastMail 实例失败: {e}")
        return None

async def send_welcome_email(email: str, username: str):
    """发送欢迎邮件"""
    fastmail = _get_fastmail()
    if fastmail is None:
        logger.warning("邮件服务未配置，跳过发送欢迎邮件")
        return False
    
    message = MessageSchema(
        subject="欢迎注册物联网设备服务系统",
        recipients=[email],
        body=f"""
        <html>
        <body>
            <h2>欢迎注册物联网设备服务系统！</h2>
            <p>亲爱的 {username}，</p>
            <p>感谢您注册我们的物联网设备服务系统。您的账户已成功创建。</p>
            <p>您现在可以：</p>
            <ul>
                <li>登录系统管理您的设备</li>
                <li>添加和配置物联网设备</li>
                <li>监控设备状态</li>
                <li>查看设备数据</li>
            </ul>
            <p>如果您有任何问题，请随时联系我们的技术支持团队。</p>
            <br>
            <p>祝您使用愉快！</p>
            <p>物联网设备服务系统团队</p>
        </body>
        </html>
        """,
        subtype="html"
    )
    
    try:
        await fastmail.send_message(message)
        logger.info(f"欢迎邮件已发送: {email}")
        return True
    except Exception as e:
        logger.error(f"发送欢迎邮件失败: {e}")
        return False

async def send_password_reset_email(email: str, username: str, reset_token: str):
    """发送密码重置邮件"""
    fastmail = _get_fastmail()
    if fastmail is None:
        logger.warning("邮件服务未配置，跳过发送密码重置邮件")
        return False
    
    reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
    
    message = MessageSchema(
        subject="密码重置 - 物联网设备服务系统",
        recipients=[email],
        body=f"""
        <html>
        <body>
            <h2>密码重置请求</h2>
            <p>亲爱的 {username}，</p>
            <p>我们收到了您的密码重置请求。请点击下面的链接来重置您的密码：</p>
            <p><a href="{reset_url}" style="background-color: #409eff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">重置密码</a></p>
            <p>如果按钮无法点击，请复制以下链接到浏览器中打开：</p>
            <p>{reset_url}</p>
            <p><strong>注意：</strong>此链接将在24小时后过期。</p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <br>
            <p>物联网设备服务系统团队</p>
        </body>
        </html>
        """,
        subtype="html"
    )
    
    try:
        await fastmail.send_message(message)
        logger.info(f"密码重置邮件已发送: {email}")
        return True
    except Exception as e:
        logger.error(f"发送密码重置邮件失败: {e}")
        return False
