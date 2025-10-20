from database import get_db
from models import User
from permissions import PermissionChecker, Permissions

def test_permission_checker():
    db = next(get_db())
    
    # 查找admin用户
    admin_user = db.query(User).filter(User.username == 'admin').first()
    if not admin_user:
        print("Admin user not found")
        return
    
    # 创建权限检查器
    checker = PermissionChecker(db)
    
    # 测试权限检查
    has_reagent_read = checker.user_has_permission(admin_user, Permissions.REAGENT_READ)
    print(f"Admin user has reagent.read permission: {has_reagent_read}")
    
    # 获取用户所有权限
    user_permissions = checker.get_user_permissions(admin_user)
    print(f"Total permissions: {len(user_permissions)}")
    print(f"Has reagent.read in permissions list: {'reagent.read' in user_permissions}")
    
    # 检查用户角色
    user_roles = checker.get_user_roles(admin_user)
    print(f"User roles: {user_roles}")
    
    db.close()

if __name__ == "__main__":
    test_permission_checker()