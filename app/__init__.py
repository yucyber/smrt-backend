import os
import logging
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from database import *
from mail import mail

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)  # 允许跨域请求

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载环境变量
    try:
        load_dotenv()  # 加载 .env 文件(存储敏感信息)
        logging.info("成功加载 .env 文件")
    except Exception as e:
        logging.warning(f"加载 .env 文件失败: {str(e)}，将使用默认配置")
    
    # 配置 JWT 密钥
    jwt_secret = os.getenv('JWT_SECRET')
    if not jwt_secret:
        jwt_secret = 'prod_secret_key'  # 生产模式下的默认密钥
        logging.warning("JWT_SECRET 未设置，使用生产模式默认密钥")
    app.config['JWT_SECRET_KEY'] = jwt_secret
    
    # JWT 过期配置
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 60 * 60  # 设置 ACCESS_TOKEN 过期时间为24小时
    
    # 数据库配置
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        # 如果环境变量中没有配置，使用默认的 MySQL 配置
        db_uri = 'mysql+pymysql://root:root@localhost/smart_editor'
        logging.warning(f"数据库URI未设置，使用默认MySQL数据库: {db_uri}")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Redis 配置
    redis_uri = os.getenv('REDIS_DATABASE_URI')
    if not redis_uri:
        redis_uri = 'redis://localhost:6379/0'
        logging.warning(f"Redis URI未设置，使用默认配置: {redis_uri}")
    app.config['REDIS_URL'] = redis_uri
    
    # 邮件配置
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '465'))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'True').lower() in ('true', '1', 't')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
    
    # 开发模式配置 - 默认使用生产模式
    app.config['DEVELOPMENT_MODE'] = os.getenv('DEVELOPMENT_MODE', 'False').lower() in ('true', '1', 't')
    if app.config['DEVELOPMENT_MODE']:
        logging.warning("应用运行在开发模式下，某些安全检查将被绕过")
    else:
        logging.info("应用运行在生产模式下，所有安全检查均已启用")

    # 初始化数据库连接
    try:
        db.init_app(app)  # 创建 MySQL 连接
        
        # 在应用上下文中创建数据库表
        with app.app_context():
            try:
                db.create_all()  # 确保数据库表存在
                logging.info("数据库表已创建或已存在")
            except Exception as e:
                logging.error(f"创建数据库表失败: {str(e)}")
                logging.error(traceback.format_exc())
    except Exception as e:
        logging.error(f"初始化数据库连接失败: {str(e)}")
        logging.error(traceback.format_exc())

    # 初始化 Redis 连接
    try:
        redis_client.init_app(app)  # 创建 Redis 连接
        logging.info("Redis 连接已初始化")
    except Exception as e:
        logging.error(f"初始化 Redis 连接失败: {str(e)}")
        logging.error(traceback.format_exc())

    # 初始化邮件客户端
    try:
        mail.init_app(app)  # 创建邮件客户端连接
        logging.info("邮件客户端已初始化")
    except Exception as e:
        logging.error(f"初始化邮件客户端失败: {str(e)}")
        logging.error(traceback.format_exc())
    
    # 配置 JWT
    jwt = JWTManager(app)  # 创建 JWTManager 实例
    
    # JWT 错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        logging.warning(f"过期的 JWT 令牌: {jwt_payload.get('sub', 'unknown')}")
        if app.config['DEVELOPMENT_MODE']:
            # 在开发模式下，允许使用过期的令牌
            return jsonify({"message": "令牌已过期，但在开发模式下被接受", "code": "200"}), 200
        return jsonify({"message": "Token已过期", "code": "401"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        logging.warning(f"无效的 JWT 令牌: {error}")
        if app.config['DEVELOPMENT_MODE']:
            # 在开发模式下，允许使用无效的令牌
            return jsonify({"message": "无效的令牌，但在开发模式下被接受", "code": "200"}), 200
        return jsonify({"message": f"无效的Token: {error}", "code": "401"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        logging.warning(f"缺少 JWT 令牌: {error}")
        if app.config['DEVELOPMENT_MODE']:
            # 在开发模式下，允许未认证的请求
            return jsonify({"message": "缺少令牌，但在开发模式下被接受", "code": "200"}), 200
        return jsonify({"message": f"缺少Token: {error}", "code": "401"}), 401

    # 导入蓝图
    from .auth import auth as auth_blueprint
    from .document import document as document_blueprint
    from .function import function as function_blueprint
    from .knowledge_base.views import knowledge_base_bp
    from .auth.utils import create_default_users  # 导入创建默认用户的函数

    # 注册蓝图 - 恢复原始路径（无/api前缀）
    app.register_blueprint(auth_blueprint, url_prefix='/auth')  # 注册蓝图
    app.register_blueprint(document_blueprint, url_prefix='/document')  # 注册蓝图
    app.register_blueprint(function_blueprint, url_prefix='/function')  # 注册蓝图
    app.register_blueprint(knowledge_base_bp, url_prefix='/knowledge_base')  # 注册知识库蓝图
    
    # 记录蓝图注册信息
    logging.info("已注册蓝图: auth, document, function, knowledge_base")

    # 初始化默认用户
    try:
        # 创建默认用户
        create_default_users(app)
        logging.info("默认用户初始化完成")
    except Exception as e:
        logging.error(f"初始化默认用户失败: {str(e)}")
        logging.error(traceback.format_exc())

    return app
