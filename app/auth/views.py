import os
import random
import logging

from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message

from database import *
from mail import mail
from . import auth
from .models import Users


#  生成验证码并发送邮件
@auth.route('/varify/<string:username>&<string:email>')
def varify(username, email):
    # 生成一个6位数的验证码
    verification_code = str(random.randint(100000, 999999))
    # 将验证码和用户的邮箱一起存储到 Redis 中
    redis_client.setex(f'verification_code:{email}', 300, verification_code)
    # 创建邮件消息
    msg = Message('【妙笔】用户注册邮箱验证', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
    msg.body = ('Hi，【{}】：\n\n您正尝试通过本邮箱接收注册【妙笔】时所需的验证码。\n\n'
                '验证码：【{}】，5分钟内有效，如非本人操作，请忽略本邮件。').format(username, verification_code)
    # 发送邮件
    mail.send(msg)
    return jsonify({'message': '验证码已发送，请注意查收！', 'code': 200})


# 用户注册
@auth.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        # 从 Redis 中获取验证码
        verification_code = redis_client.get(f'verification_code:{data["email"]}')
        # 验证验证码
        if verification_code is None or data['verification_code'] != verification_code:
            return jsonify({'message': '验证码错误或已失效！', 'code': 400})
        # 验证邮箱是否已被注册
        if Users.query.filter_by(email=data['email']).first():
            return jsonify({'message': '邮箱已被注册！', 'code': 400})
        # 注册新用户
        new_user = Users(username=data['username'], email=data['email'])
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': '用户注册成功！', 'code': 200})
    except Exception as e:
        logging.error(f"注册失败: {str(e)}")
        return jsonify({'message': f'注册失败: {str(e)}', 'code': 500}), 500


# 用户登录
@auth.route('/login', methods=['POST'])
def login():
    try:
        # 获取请求数据
        request_data = request.get_data(as_text=True)
        logging.info(f"登录请求数据: {request_data[:100]}...")
        
        # 尝试解析JSON
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logging.error(f"登录请求JSON解析失败: {str(e)}")
            return jsonify({'message': f'登录失败! 无效的JSON格式: {str(e)}', 'code': 422}), 422
            
        # 验证请求数据
        if not data:
            return jsonify({'message': '请求数据为空！', 'code': 400})
            
        if 'email' not in data:
            return jsonify({'message': '缺少邮箱！', 'code': 400})
            
        if 'password' not in data:
            return jsonify({'message': '缺少密码！', 'code': 400})
        
        # 验证用户是否存在
        user = Users.query.filter_by(email=data['email']).first()
        if user is None:
            return jsonify({'message': '邮箱未注册！', 'code': 400})
        
        # 验证密码是否正确
        if not user.check_password(data['password']):
            return jsonify({'message': '密码错误！', 'code': 400})
        
        # 用户登录成功，生成 JWT
        access_token = create_access_token(identity=user.id)
        logging.info(f"生成的访问令牌: {access_token[:20]}...")
        
        # 记录成功登录
        logging.info(f"用户登录成功: user_id={user.id}, email={user.email}")
        
        # 将 JWT 发送给前端
        response_data = {
            'message': '用户登录成功！', 
            'code': 200,
            'data': {
                'access_token': access_token, 
                'username': user.username, 
                'email': user.email,
                'user_id': user.id
            }
        }
        
        # 打印响应数据
        logging.info(f"登录响应: message={response_data['message']}, code={response_data['code']}")
        
        return jsonify(response_data)
    except Exception as e:
        logging.error(f"登录异常: {str(e)}")
        return jsonify({'message': f'登录失败: {str(e)}', 'code': 500}), 500


# 重置密码验证
@auth.route("/reset_varify", methods=["GET"])
@jwt_required()
def reset_varify():
    # 使用get_jwt_identity访问当前用户的身份
    current_user = get_jwt_identity()
    user = Users.query.get(current_user)
    email = user.email
    # 生成一个6位数的验证码
    verification_code = str(random.randint(100000, 999999))
    # 将验证码和用户的邮箱一起存储到 Redis 中
    redis_client.setex(f'verification_code:{email}', 300, verification_code)
    # 创建邮件消息
    msg = Message('【妙笔】用户密码重置', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
    msg.body = ('Hi，【{}】：\n\n您正尝试通过本邮箱重置【妙笔】时所需的验证码。\n\n'
                '验证码：【{}】，5分钟内有效，如非本人操作，请忽略本邮件。').format(user.username, verification_code)
    # 发送邮件
    mail.send(msg)
    return jsonify({'message': '验证码已发送，请注意查收！', 'code': 200})


# 用户密码重置
@auth.route("/reset_password", methods=["POST"])
@jwt_required()
def reset_password():
    current_user = get_jwt_identity()
    user = Users.query.get(current_user)
    email = user.email
    data = request.get_json()
    # 从 Redis 中获取验证码
    verification_code = redis_client.get(f'verification_code:{email}')
    # 验证验证码
    if verification_code is None or data['verification_code'] != verification_code:
        return jsonify({'message': '验证码错误或已失效！', 'code': 400})
    # 重置用户密码
    user.set_password(data['password'])
    db.session.commit()
    return jsonify({'message': '用户密码重置成功！', 'code': 200})
