from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base
from app.utils.timezone import get_beijing_time_naive
import uuid as uuid_lib

class LLMProvider(Base):
    """
    大模型提供商信息模型
    """
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), comment="唯一标识UUID")
    code = Column(String(50), unique=True, nullable=False, comment="提供商代码")
    name = Column(String(100), nullable=False, comment="提供商名称")
    title = Column(String(200), nullable=False, comment="完整标题")
    description = Column(Text, comment="提供商描述")
    apply_url = Column(String(500), comment="API申请地址")
    doc_url = Column(String(500), comment="文档地址")
    default_api_base = Column(String(500), comment="默认API地址")
    has_free_quota = Column(Integer, default=0, comment="是否提供免费额度")
    icon = Column(String(200), comment="图标URL或图标名称")
    tag_type = Column(String(20), default="primary", comment="标签类型")
    country = Column(String(20), default="cn", comment="国家")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=get_beijing_time_naive)
    updated_at = Column(DateTime, default=get_beijing_time_naive, onupdate=get_beijing_time_naive)
    
    def __repr__(self):
        return f"<LLMProvider(id={self.id}, name='{self.name}', code='{self.code}')>"

