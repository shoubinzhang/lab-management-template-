from database import get_db
from models import User
from app import verify_password, get_password_hash

def check_admin_password():
    db = next(get_db())
    
    # 查找admin用户
    admin_user = db.query(User).filter(User.username == 'admin').first()
    if not admin_user:
        print("Admin user not found")
        return
    
    print(f"Admin user found: {admin_user.username}")
    print(f"Password hash: {admin_user.hashed_password[:50]}...")
    
    # 测试密码验证
    test_passwords = ['admin', 'password', '123456', 'admin123']
    
    for pwd in test_passwords:
        if verify_password(pwd, admin_user.hashed_password):
            print(f"✓ Password '{pwd}' is correct!")
            db.close()
            return pwd
        else:
            print(f"✗ Password '{pwd}' is incorrect")
    
    # 如果没有找到正确密码，重置为'admin'
    print("\nResetting password to 'admin'...")
    admin_user.hashed_password = get_password_hash('admin')
    db.commit()
    print("Password reset successfully!")
    
    db.close()
    return 'admin'

if __name__ == "__main__":
    check_admin_password()