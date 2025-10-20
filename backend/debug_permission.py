from database import get_db
from models import User
from permissions import PermissionChecker, Permissions
from auth import get_current_user
from jose import jwt

# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def debug_permission_check():
    # 获取数据库会话
    db = next(get_db())
    
    # 查找管理员用户
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        print("管理员用户不存在")
        return
    
    print(f"找到管理员用户: {admin_user.username}")
    print(f"用户角色: {[role.name for role in admin_user.roles]}")
    
    # 测试权限检查器
    checker = PermissionChecker(db)
    has_permission = checker.user_has_permission(admin_user, Permissions.REAGENT_READ)
    print(f"用户是否有REAGENT_READ权限: {has_permission}")
    
    # 获取用户所有权限
    all_permissions = checker.get_user_permissions(admin_user)
    print(f"用户所有权限: {all_permissions}")
    
    # 测试JWT token解析
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NzA1ODE3M30.1KrDF2tleDfabQCxh5oQ6eFEDdXWkYWFDvJyLqNltjY"
    try:
        payload = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token解析成功: {payload}")
    except Exception as e:
        print(f"Token解析失败: {e}")
    
    db.close()

if __name__ == "__main__":
    debug_permission_check()