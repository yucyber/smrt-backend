import logging
from .models import Users
from database import db

def create_default_users(app):
    """初始化默认用户，确保系统中存在必要的账号"""
    with app.app_context():
        try:
            # 检查是否需要创建默认用户
            if Users.query.count() < 20:  # 如果数据库中用户数少于20个，初始化默认用户
                logging.info("检测到需要创建默认用户")
                
                # 检查并创建管理员用户
                admin = Users.query.filter_by(email='admin@smarteditor.com').first()
                if not admin:
                    admin = Users(username='admin', email='admin@smarteditor.com')
                    admin.set_password('admin123')
                    db.session.add(admin)
                    logging.info("创建管理员用户: admin@smarteditor.com")
                
                # 检查并创建模板管理员
                template_admin = Users.query.filter_by(email='template@admin.com').first()
                if not template_admin:
                    template_admin = Users(username='template_admin', email='template@admin.com')
                    template_admin.set_password('template123')
                    db.session.add(template_admin)
                    logging.info("创建模板管理员: template@admin.com")
                
                # 检查并创建测试用户
                test_user = Users.query.filter_by(email='test@example.com').first()
                if not test_user:
                    test_user = Users(username='测试用户', email='test@example.com')
                    test_user.set_password('123456')
                    db.session.add(test_user)
                    logging.info("创建测试用户: test@example.com")
                
                # 检查并创建其他测试用户
                user_test = Users.query.filter_by(email='user@test.com').first()
                if not user_test:
                    user_test = Users(username='用户测试', email='user@test.com')
                    user_test.set_password('123456')
                    db.session.add(user_test)
                    logging.info("创建测试用户: user@test.com")
                
                example_user = Users.query.filter_by(email='example@test.com').first()
                if not example_user:
                    example_user = Users(username='示例用户', email='example@test.com')
                    example_user.set_password('123456')
                    db.session.add(example_user)
                    logging.info("创建示例用户: example@test.com")
                
                # 提交所有更改
                db.session.commit()
                logging.info("默认用户创建完成")
                
                # 验证用户创建是否成功
                verify_user = Users.query.filter_by(email='test@example.com').first()
                if verify_user and verify_user.check_password('123456'):
                    logging.info("测试用户密码验证成功")
                else:
                    logging.error("测试用户密码验证失败！请检查密码哈希生成机制")
                
            else:
                logging.info("数据库中已有足够的用户，跳过默认用户创建")
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"创建默认用户时发生错误: {str(e)}") 