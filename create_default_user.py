from app import create_app
from app.auth.models import Users
from database import db

def create_default_user():
    """创建默认测试用户"""
    app = create_app()
    with app.app_context():
        # 检查是否已存在测试用户
        if Users.query.filter_by(email='test@example.com').first() is None:
            # 创建测试用户
            test_user = Users(
                username='测试用户',
                email='test@example.com'
            )
            test_user.set_password('123456')  # 设置密码为123456
            db.session.add(test_user)
            db.session.commit()
            print('创建默认测试用户成功!')
            print('用户名: 测试用户')
            print('邮箱: test@example.com')
            print('密码: 123456')
        else:
            print('默认测试用户已存在')
            print('用户名: 测试用户')
            print('邮箱: test@example.com')
            print('密码: 123456')

if __name__ == '__main__':
    create_default_user() 