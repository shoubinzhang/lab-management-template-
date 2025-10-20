from database import get_db
from models import User, Role

def check_admin_permissions():
    db = next(get_db())
    
    # 查找admin用户
    admin_user = db.query(User).filter(User.username == 'admin').first()
    if not admin_user:
        print("Admin user not found")
        return
    
    print(f"Admin user: {admin_user.username}, role: {admin_user.role}")
    print(f"User roles: {[role.name for role in admin_user.roles]}")
    
    # 查找admin角色
    admin_role = db.query(Role).filter(Role.name == 'admin').first()
    if admin_role:
        print(f"Admin role found with {len(admin_role.permissions)} permissions")
        print(f"First 5 permissions: {[perm.name for perm in admin_role.permissions[:5]]}")
        reagent_read_perm = [perm for perm in admin_role.permissions if perm.name == 'reagent.read']
        print(f"Has reagent.read permission: {len(reagent_read_perm) > 0}")
    else:
        print("Admin role not found")
    
    db.close()

if __name__ == "__main__":
    check_admin_permissions()