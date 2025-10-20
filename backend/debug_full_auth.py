from fastapi import HTTPException
from database import get_db
from models import User
from permissions import PermissionChecker, Permissions, check_permission
from auth import get_current_user
from jose import jwt, JWTError
from fastapi.security import HTTPAuthorizationCredentials

# JWT配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

def simulate_auth_flow():
    """模拟完整的认证和权限检查流程"""
    # 测试token
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1NzA1ODE3M30.1KrDF2tleDfabQCxh5oQ6eFEDdXWkYWFDvJyLqNltjY"
    
    print("=== 模拟认证流程 ===")
    
    # 1. 解析JWT token
    try:
        payload = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        print(f"1. Token解析成功，用户名: {username}")
    except JWTError as e:
        print(f"1. Token解析失败: {e}")
        return
    
    # 2. 获取用户
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print("2. 用户不存在")
        return
    print(f"2. 找到用户: {user.username}")
    
    # 3. 检查权限
    checker = PermissionChecker(db)
    has_permission = checker.user_has_permission(user, Permissions.REAGENT_READ)
    print(f"3. 用户是否有REAGENT_READ权限: {has_permission}")
    print(f"   REAGENT_READ常量值: {Permissions.REAGENT_READ}")
    
    # 4. 模拟权限依赖函数
    print("\n=== 模拟权限依赖函数 ===")
    try:
        # 创建模拟的HTTPAuthorizationCredentials
        class MockCredentials:
            def __init__(self, token):
                self.credentials = token
        
        mock_credentials = MockCredentials(test_token)
        
        # 模拟get_current_user函数
        current_user = get_current_user(mock_credentials, db)
        print(f"4. get_current_user成功: {current_user.username}")
        
        # 模拟权限检查依赖
        permission_checker = PermissionChecker(db)
        if not permission_checker.user_has_permission(current_user, Permissions.REAGENT_READ):
            print(f"5. 权限检查失败：需要 {Permissions.REAGENT_READ} 权限")
        else:
            print(f"5. 权限检查成功：用户有 {Permissions.REAGENT_READ} 权限")
            
    except Exception as e:
        print(f"4-5. 权限检查过程出错: {e}")
    
    # 6. 检查用户的所有权限
    all_permissions = checker.get_user_permissions(user)
    print(f"\n6. 用户所有权限数量: {len(all_permissions)}")
    print(f"   是否包含reagent.read: {'reagent.read' in all_permissions}")
    
    db.close()

if __name__ == "__main__":
    simulate_auth_flow()