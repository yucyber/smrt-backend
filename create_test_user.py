from app import create_app
from app.auth.models import Users
from database import db
from werkzeug.security import generate_password_hash

def create_test_user():
    """创建测试用户，直接设置密码哈希"""
    app = create_app()
    with app.app_context():
        # 首先删除可能存在的测试用户
        existing_user = Users.query.filter_by(email='test@example.com').first()
        if existing_user:
            print(f"删除现有测试用户: {existing_user.username} ({existing_user.email})")
            db.session.delete(existing_user)
            db.session.commit()
            
        # 创建新的测试用户
        test_user = Users(
            username='测试用户',
            email='test@example.com',
            password_hash=generate_password_hash('123456')
        )
        db.session.add(test_user)
        db.session.commit()
        
        # 创建管理员用户
        admin_user = Users.query.filter_by(email='admin@smarteditor.com').first()
        if not admin_user:
            print("创建管理员用户...")
            admin_user = Users(
                username='admin',
                email='admin@smarteditor.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            db.session.commit()
        
        # 验证用户已创建
        new_user = Users.query.filter_by(email='test@example.com').first()
        if new_user:
            print(f"测试用户创建成功!")
            print(f"用户ID: {new_user.id}")
            print(f"用户名: {new_user.username}")
            print(f"邮箱: {new_user.email}")
            print(f"密码哈希: {new_user.password_hash[:20]}...")
            print(f"测试密码: 123456")
            
            # 验证密码
            if new_user.check_password('123456'):
                print("密码验证成功!")
            else:
                print("警告: 密码验证失败!")
        else:
            print("错误: 创建用户后无法找到该用户!")

if __name__ == '__main__':
    create_test_user() 