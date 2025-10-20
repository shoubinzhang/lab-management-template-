#!/usr/bin/env python3
"""
重置管理员密码脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_password(new_password: str = "admin"):
    """重置admin用户的密码"""
    db = SessionLocal()
    try:
        # 查找admin用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("❌ 未找到admin用户")
            return False
        
        # 生成新的密码哈希
        new_hashed_password = pwd_context.hash(new_password)
        
        # 更新密码
        admin_user.hashed_password = new_hashed_password
        db.commit()
        
        print(f"✅ admin用户密码已重置为: {new_password}")
        print(f"用户名: admin")
        print(f"新密码: {new_password}")
        return True
        
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # 可以通过命令行参数指定新密码
    new_password = sys.argv[1] if len(sys.argv) > 1 else "admin"
    reset_admin_password(new_password)