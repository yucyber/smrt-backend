import json
from datetime import datetime
import logging
import traceback

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from . import document
from .comment_models import Comments
from .models import Documents

# 添加评论
@document.route('/comment', methods=['POST'])
@jwt_required()
def add_comment():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['id', 'document_id', 'text', 'selected_text']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'缺少必要字段: {field}', 'code': '400'}), 400
                
        # 验证range相关字段
        if ('range_from' not in data or 'range_to' not in data) and ('range' not in data or 'from' not in data['range'] or 'to' not in data['range']):
            return jsonify({'message': '缺少必要字段: range_from/range_to 或 range.from/range.to', 'code': '400'}), 400
        
        # 验证文档是否存在
        document = Documents.query.get(data['document_id'])
        if not document:
            return jsonify({'message': '文档不存在', 'code': '404'}), 404
        
        # 创建评论
        # 优先使用直接提供的range_from和range_to字段，如果没有则从range对象中获取
        range_from = data.get('range_from')
        range_to = data.get('range_to')
        
        if range_from is None and 'range' in data and 'from' in data['range']:
            range_from = data['range']['from']
            
        if range_to is None and 'range' in data and 'to' in data['range']:
            range_to = data['range']['to']
            
        comment = Comments(
            id=data['id'],
            document_id=data['document_id'],
            user_id=user_id,
            text=data['text'],
            selected_text=data['selected_text'],
            range_from=range_from,
            range_to=range_to
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # 返回评论信息，包括用户信息
        from app.auth.models import Users
        user = Users.query.get(user_id)
        
        result = comment.to_dict()
        result['user'] = {
            'id': user.id,
            'name': user.username
        }
        
        return jsonify({'message': '评论添加成功', 'comment': result, 'code': '200'})
    except Exception as e:
        logging.error(f"添加评论失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': f'添加评论失败: {str(e)}', 'code': '500'}), 500

# 获取文档的所有评论
@document.route('/comment/document/<int:document_id>', methods=['GET'])
@jwt_required()
def get_document_comments(document_id):
    try:
        # 验证文档是否存在
        document = Documents.query.get(document_id)
        if not document:
            return jsonify({'message': '文档不存在', 'code': '404'}), 404
        
        # 获取文档的所有未删除评论
        comments = Comments.query.filter_by(document_id=document_id, is_deleted=False).all()
        
        # 获取用户信息
        from app.auth.models import Users
        result = []
        for comment in comments:
            comment_dict = comment.to_dict()
            user = Users.query.get(comment.user_id)
            comment_dict['user'] = {
                'id': user.id,
                'name': user.username
            }
            result.append(comment_dict)
        
        return jsonify({'comments': result, 'code': '200'})
    except Exception as e:
        logging.error(f"获取评论失败: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'message': f'获取评论失败: {str(e)}', 'code': '500'}), 500

# 删除评论
@document.route('/comment/<string:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    try:
        user_id = get_jwt_identity()
        
        # 查找评论
        comment = Comments.query.get(comment_id)
        if not comment:
            return jsonify({'message': '评论不存在', 'code': '404'}), 404
        
        # 验证是否是评论作者
        if comment.user_id != user_id:
            # 检查是否是文档所有者
            document = Documents.query.get(comment.document_id)
            if document.user_id != user_id:
                return jsonify({'message': '无权删除此评论', 'code': '403'}), 403
        
        # 软删除评论
        comment.is_deleted = True
        db.session.commit()
        
        return jsonify({'message': '评论删除成功', 'code': '200'})
    except Exception as e:
        logging.error(f"删除评论失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': f'删除评论失败: {str(e)}', 'code': '500'}), 500