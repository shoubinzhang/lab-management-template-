from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

# 用户角色关联表（多对多关系）
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# 角色权限关联表（多对多关系）
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# 权限表
class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 权限名称，如：user.create, user.read, user.update, user.delete
    description = Column(String)  # 权限描述
    resource = Column(String)  # 资源类型：user, device, reagent, consumable, record
    action = Column(String)  # 操作类型：create, read, update, delete, manage
    
    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

# 角色表
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 角色名称：admin, manager, researcher, user
    description = Column(String)  # 角色描述
    is_active = Column(Boolean, default=True)  # 角色是否激活
    
    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

# 用户表
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # 保留原有角色字段以兼容现有代码
    is_active = Column(Boolean, default=True)  # 用户是否激活
    created_at = Column(DateTime, default=lambda: datetime.utcnow())  # 创建时间
    
    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")

# 设备表
class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    status = Column(String, default="available")  # 设备状态：available, in_use, maintenance, broken
    location = Column(String)
    model = Column(String)  # 设备型号
    serial_number = Column(String, unique=True)  # 序列号
    purchase_date = Column(Date)  # 购买日期
    warranty_expiry = Column(Date)  # 保修到期日期
    last_maintenance = Column(Date)  # 上次维护日期
    next_maintenance = Column(Date)  # 下次维护日期
    maintenance_interval = Column(Integer, default=90)  # 维护间隔（天）
    responsible_person = Column(String)  # 负责人
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关系
    maintenance_records = relationship("DeviceMaintenance", back_populates="device")
    reservations = relationship("DeviceReservation", back_populates="device")

# 试剂表
class Reagent(Base):
    __tablename__ = "reagents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 试剂类别
    manufacturer = Column(String)  # 制造商
    product_number = Column(String)  # 产品货号
    batch_number = Column(String)  # 批次号
    expiry_date = Column(DateTime)
    quantity = Column(Float)
    unit = Column(String)  # 单位：mL, g, etc.
    storage_temperature = Column(String)  # 存储温度
    storage_location = Column(String)  # 存储位置
    cas_number = Column(String)  # CAS号
    molecular_formula = Column(String)  # 分子式
    molecular_weight = Column(Float)  # 分子量
    purity = Column(Float)  # 纯度（%）
    supplier = Column(String)  # 供应商
    specification = Column(String)  # 规格
    safety_notes = Column(String)  # 安全注意事项
    price = Column(Float)  # 价格
    min_threshold = Column(Float, default=10.0)  # 最小库存阈值
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

# 耗材表
class Consumable(Base):
    __tablename__ = "consumables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # 耗材类别
    manufacturer = Column(String)  # 制造商
    model = Column(String)  # 型号
    specification = Column(String)  # 规格
    quantity = Column(Integer, default=0)  # 库存数量
    unit = Column(String, default="个")  # 单位：个, 盒, etc.
    location = Column(String)  # 存放位置
    min_stock = Column(Integer, default=10)  # 最小库存
    price = Column(Float)  # 单价
    supplier = Column(String)  # 供应商
    notes = Column(String)  # 备注
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

# 实验记录表
class ExperimentRecord(Base):
    __tablename__ = "experiment_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    description = Column(String)

# 知识库表
class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    category = Column(String)  # 分类：safety, protocol, etc.

# 反馈表
class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    status = Column(String, default="pending")  # 反馈状态：pending, resolved

# 设备维护记录表
class DeviceMaintenance(Base):
    __tablename__ = "device_maintenance"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    maintenance_type = Column(String)  # 维护类型：routine, repair, calibration
    description = Column(String)  # 维护描述
    performed_by = Column(String)  # 执行人
    maintenance_date = Column(Date)  # 维护日期
    cost = Column(Float, default=0.0)  # 维护成本
    status = Column(String, default="completed")  # 状态：scheduled, in_progress, completed
    notes = Column(String)  # 备注
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # 关系
    device = relationship("Device", back_populates="maintenance_records")

# 设备预约表
class DeviceReservation(Base):
    __tablename__ = "device_reservations"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)  # 预约开始时间
    end_time = Column(DateTime)  # 预约结束时间
    purpose = Column(String)  # 使用目的
    status = Column(String, default="pending")  # 状态：pending, approved, rejected, completed, cancelled
    notes = Column(String)  # 备注
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关系
    device = relationship("Device", back_populates="reservations")
    user = relationship("User")

# 通知表
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)  # 通知标题
    message = Column(String)  # 通知内容
    type = Column(String)  # 通知类型：reagent_low_stock, reagent_expiring, equipment_maintenance, experiment_completed, system_alert, approval_request, reservation_approved
    priority = Column(String, default="normal")  # 优先级：low, normal, high, urgent
    is_read = Column(Boolean, default=False)  # 是否已读
    data = Column(String)  # 额外数据（JSON格式）
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    expires_at = Column(DateTime)  # 过期时间
    
    # 关系
    user = relationship("User")

# 申请表模型
class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, nullable=False)  # 'reagent' 或 'consumable'
    item_id = Column(Integer, nullable=False)  # 试剂或耗材的ID
    item_name = Column(String, nullable=False)  # 试剂或耗材名称
    quantity = Column(Float, nullable=False)  # 申请数量
    unit = Column(String, nullable=False)  # 单位
    purpose = Column(Text, nullable=False)  # 使用目的
    notes = Column(Text)  # 备注
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 申请人ID
    status = Column(String, default="pending")  # 状态: pending, approved, rejected
    approved_by_id = Column(Integer, ForeignKey("users.id"))  # 审批人ID
    approved_at = Column(DateTime)  # 审批时间
    approval_notes = Column(Text)  # 审批备注
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关系
    requester = relationship("User", foreign_keys=[requester_id], back_populates="requests")
    approver = relationship("User", foreign_keys=[approved_by_id])

# 使用记录表
class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)  # 关联的申请ID
    item_type = Column(String, nullable=False)  # 'reagent' 或 'consumable'
    item_id = Column(Integer, nullable=False)  # 试剂或耗材的ID
    item_name = Column(String, nullable=False)  # 试剂或耗材名称
    quantity_used = Column(Float, nullable=False)  # 使用数量
    unit = Column(String, nullable=False)  # 单位
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 使用者ID
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 批准者ID
    purpose = Column(Text, nullable=False)  # 使用目的
    notes = Column(Text)  # 备注
    used_at = Column(DateTime, default=lambda: datetime.utcnow())  # 使用时间（批准时间）
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # 关系
    request = relationship("Request", back_populates="usage_record")
    user = relationship("User", foreign_keys=[user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

# 更新Request模型，添加usage_record关系
Request.usage_record = relationship("UsageRecord", back_populates="request", uselist=False)

# 更新User模型，添加requests关系
User.requests = relationship("Request", foreign_keys="Request.requester_id", back_populates="requester")

# 设备借用记录表
class DeviceBorrow(Base):
    __tablename__ = "device_borrows"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    borrow_time = Column(DateTime, default=lambda: datetime.utcnow())
    return_time = Column(DateTime, nullable=True)
    status = Column(String, default="borrowed")  # 状态: borrowed, returned
    notes = Column(String)  # 备注
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # 关系
    device = relationship("Device")
    user = relationship("User")

# WebSocket连接管理表
class WebSocketConnection(Base):
    __tablename__ = "websocket_connections"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    connection_id = Column(String, unique=True, index=True)  # WebSocket连接ID
    is_active = Column(Boolean, default=True)  # 连接是否活跃
    last_ping = Column(DateTime, default=lambda: datetime.utcnow())  # 最后心跳时间
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # 关系
    user = relationship("User")