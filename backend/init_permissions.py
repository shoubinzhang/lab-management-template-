from sqlalchemy.orm import Session
from models import Role, Permission, User
from permissions import Permissions, Roles
from database import get_db, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def init_permissions_and_roles(db: Session):
    """初始化权限和角色数据"""
    
    # 创建权限
    permissions_data = [
        # 用户管理权限
        {"name": Permissions.USER_CREATE, "description": "创建用户", "resource": "user", "action": "create"},
        {"name": Permissions.USER_READ, "description": "查看用户", "resource": "user", "action": "read"},
        {"name": Permissions.USER_UPDATE, "description": "更新用户", "resource": "user", "action": "update"},
        {"name": Permissions.USER_DELETE, "description": "删除用户", "resource": "user", "action": "delete"},
        {"name": Permissions.USER_MANAGE, "description": "管理用户", "resource": "user", "action": "manage"},
        
        # 设备管理权限
        {"name": Permissions.DEVICE_CREATE, "description": "创建设备", "resource": "device", "action": "create"},
        {"name": Permissions.DEVICE_READ, "description": "查看设备", "resource": "device", "action": "read"},
        {"name": Permissions.DEVICE_UPDATE, "description": "更新设备", "resource": "device", "action": "update"},
        {"name": Permissions.DEVICE_DELETE, "description": "删除设备", "resource": "device", "action": "delete"},
        {"name": Permissions.DEVICE_MANAGE, "description": "管理设备", "resource": "device", "action": "manage"},
        
        # 试剂管理权限
        {"name": Permissions.REAGENT_CREATE, "description": "创建试剂", "resource": "reagent", "action": "create"},
        {"name": Permissions.REAGENT_READ, "description": "查看试剂", "resource": "reagent", "action": "read"},
        {"name": Permissions.REAGENT_UPDATE, "description": "更新试剂", "resource": "reagent", "action": "update"},
        {"name": Permissions.REAGENT_DELETE, "description": "删除试剂", "resource": "reagent", "action": "delete"},
        {"name": Permissions.REAGENT_MANAGE, "description": "管理试剂", "resource": "reagent", "action": "manage"},
        
        # 耗材管理权限
        {"name": Permissions.CONSUMABLE_CREATE, "description": "创建耗材", "resource": "consumable", "action": "create"},
        {"name": Permissions.CONSUMABLE_READ, "description": "查看耗材", "resource": "consumable", "action": "read"},
        {"name": Permissions.CONSUMABLE_UPDATE, "description": "更新耗材", "resource": "consumable", "action": "update"},
        {"name": Permissions.CONSUMABLE_DELETE, "description": "删除耗材", "resource": "consumable", "action": "delete"},
        {"name": Permissions.CONSUMABLE_MANAGE, "description": "管理耗材", "resource": "consumable", "action": "manage"},
        
        # 实验记录权限
        {"name": Permissions.RECORD_CREATE, "description": "创建实验记录", "resource": "record", "action": "create"},
        {"name": Permissions.RECORD_READ, "description": "查看实验记录", "resource": "record", "action": "read"},
        {"name": Permissions.RECORD_UPDATE, "description": "更新实验记录", "resource": "record", "action": "update"},
        {"name": Permissions.RECORD_DELETE, "description": "删除实验记录", "resource": "record", "action": "delete"},
        {"name": Permissions.RECORD_MANAGE, "description": "管理实验记录", "resource": "record", "action": "manage"},
        
        # 申请相关权限
        {"name": "reagent.request", "description": "申请领用试剂", "resource": "request", "action": "reagent"},
        {"name": "consumable.request", "description": "申请领用耗材", "resource": "request", "action": "consumable"},
        {"name": "request.approve", "description": "审批申请", "resource": "request", "action": "approve"},
        
        # 数据调阅权限
        {"name": "data.access", "description": "调阅实验数据", "resource": "data", "action": "access"},
        
        # 系统管理权限
        {"name": Permissions.SYSTEM_ADMIN, "description": "系统管理", "resource": "system", "action": "admin"},
        {"name": Permissions.SYSTEM_CONFIG, "description": "系统配置", "resource": "system", "action": "config"},
    ]
    
    # 创建权限记录
    created_permissions = {}
    for perm_data in permissions_data:
        existing_permission = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_permission:
            permission = Permission(**perm_data)
            db.add(permission)
            db.flush()  # 获取ID
            created_permissions[perm_data["name"]] = permission
        else:
            created_permissions[perm_data["name"]] = existing_permission
    
    # 创建角色
    roles_data = [
        {
            "name": Roles.ADMIN,
            "description": "系统管理员 - 拥有所有权限",
            "permissions": list(created_permissions.values())  # 管理员拥有所有权限
        },
        {
            "name": Roles.MANAGER,
            "description": "实验室管理员 - 管理实验室资源和用户",
            "permissions": [
                created_permissions[Permissions.USER_READ],
                created_permissions[Permissions.USER_UPDATE],
                created_permissions[Permissions.DEVICE_MANAGE],
                created_permissions[Permissions.REAGENT_MANAGE],
                created_permissions[Permissions.CONSUMABLE_MANAGE],
                created_permissions[Permissions.RECORD_MANAGE],
            ]
        },
        {
            "name": Roles.RESEARCHER,
            "description": "研究员 - 可以使用设备和管理自己的实验记录",
            "permissions": [
                created_permissions[Permissions.DEVICE_READ],
                created_permissions[Permissions.DEVICE_UPDATE],
                created_permissions[Permissions.REAGENT_READ],
                created_permissions[Permissions.REAGENT_UPDATE],
                created_permissions[Permissions.CONSUMABLE_READ],
                created_permissions[Permissions.CONSUMABLE_UPDATE],
                created_permissions[Permissions.RECORD_CREATE],
                created_permissions[Permissions.RECORD_READ],
                created_permissions[Permissions.RECORD_UPDATE],
            ]
        },
        {
            "name": Roles.USER,
            "description": "普通用户 - 基本查看权限",
            "permissions": [
                created_permissions[Permissions.DEVICE_READ],
                created_permissions[Permissions.REAGENT_READ],
                created_permissions[Permissions.CONSUMABLE_READ],
                created_permissions[Permissions.RECORD_READ],
            ]
        },
        {
            "name": Roles.GUEST,
            "description": "访客 - 只读权限",
            "permissions": [
                created_permissions[Permissions.DEVICE_READ],
                created_permissions[Permissions.REAGENT_READ],
                created_permissions[Permissions.CONSUMABLE_READ],
            ]
        },
        {
            "name": Roles.LAB_TECHNICIAN,
            "description": "实验技术员 - 可申请试剂耗材，书写和查看实验记录",
            "permissions": [
                created_permissions["reagent.request"],
                created_permissions["consumable.request"],
                created_permissions[Permissions.RECORD_CREATE],
                created_permissions[Permissions.RECORD_READ],
                created_permissions[Permissions.REAGENT_READ],
                created_permissions[Permissions.CONSUMABLE_READ],
            ]
        },
        {
            "name": Roles.WAREHOUSE_MANAGER,
            "description": "仓库管理员 - 可审批申请和管理库存",
            "permissions": [
                created_permissions["request.approve"],
                created_permissions[Permissions.REAGENT_MANAGE],
                created_permissions[Permissions.CONSUMABLE_MANAGE],
                created_permissions[Permissions.REAGENT_READ],
                created_permissions[Permissions.CONSUMABLE_READ],
            ]
        },
        {
            "name": Roles.DOC_MANAGER,
            "description": "文档管理员 - 可调阅实验数据",
            "permissions": [
                created_permissions["data.access"],
                created_permissions[Permissions.RECORD_READ],
                created_permissions[Permissions.RECORD_MANAGE],
            ]
        }
    ]
    
    # 创建角色记录
    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )
            role.permissions = role_data["permissions"]
            db.add(role)
        else:
            # 更新现有角色的权限
            existing_role.permissions = role_data["permissions"]
    
    db.commit()
    print("权限和角色初始化完成")

def assign_admin_role_to_existing_admins(db: Session):
    """为现有的admin用户分配管理员角色"""
    admin_role = db.query(Role).filter(Role.name == Roles.ADMIN).first()
    if not admin_role:
        print("管理员角色不存在")
        return
    
    # 查找所有role字段为admin的用户
    admin_users = db.query(User).filter(User.role == "admin").all()
    
    for user in admin_users:
        # 检查用户是否已经有管理员角色
        if admin_role not in user.roles:
            user.roles.append(admin_role)
    
    db.commit()
    print(f"为 {len(admin_users)} 个管理员用户分配了管理员角色")

def assign_user_role_to_existing_users(db: Session):
    """为现有的普通用户分配用户角色"""
    user_role = db.query(Role).filter(Role.name == Roles.USER).first()
    if not user_role:
        print("用户角色不存在")
        return
    
    # 查找所有role字段为user的用户
    regular_users = db.query(User).filter(User.role == "user").all()
    
    for user in regular_users:
        # 检查用户是否已经有用户角色
        if user_role not in user.roles:
            user.roles.append(user_role)
    
    db.commit()
    print(f"为 {len(regular_users)} 个普通用户分配了用户角色")

def initialize_permissions_and_roles():
    """初始化所有权限和角色"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        init_permissions_and_roles(db)
        assign_admin_role_to_existing_admins(db)
        assign_user_role_to_existing_users(db)
        print("权限系统初始化完成")
    except Exception as e:
        print(f"权限系统初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

def init_all_permissions():
    """初始化所有权限和角色（向后兼容）"""
    initialize_permissions_and_roles()

if __name__ == "__main__":
    init_all_permissions()