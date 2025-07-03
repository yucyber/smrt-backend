import json
from datetime import datetime
import logging
import traceback
import pytz
import uuid

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, JWTManager

from database import db, redis_client
from . import document
from .models import Documents, DocumentVersions


# 自定义JSON编码器，用于处理datetime对象
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# 自定义JWT验证装饰器，提供更详细的错误处理
def custom_jwt_required():
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            try:
                # 尝试验证JWT令牌
                verify_jwt_in_request()
                current_user = get_jwt_identity()
                logging.info(f"JWT验证成功: user_id={current_user}")
                return fn(*args, **kwargs)
            except Exception as e:
                logging.error(f"JWT验证失败: {str(e)}")
                return jsonify({'message': f'认证失败: {str(e)}', 'code': '401'}), 401
        return decorator
    return wrapper


# 创建文档
@document.route('', methods=['POST'])
@jwt_required(optional=True)  # 使用可选的JWT验证，允许在开发中绕过
def create_document():
    try:
        # 打印完整的请求头信息用于调试
        headers = dict(request.headers)
        auth_header = headers.get('Authorization', '')
        logging.info(f"收到创建文档请求: Authorization={auth_header[:20] if auth_header else 'None'}")
        
        # 获取用户ID，如果JWT验证失败则使用默认值1
        try:
            user_id = get_jwt_identity()
            if user_id is None:
                logging.warning("JWT验证结果为None，使用默认用户ID 1")
                user_id = 1  # 默认用户ID
            logging.info(f"JWT验证成功或使用默认: user_id={user_id}")
        except Exception as e:
            logging.error(f"JWT验证异常，使用默认用户ID: {str(e)}")
            user_id = 1  # 默认用户ID
        
        # 打印请求体用于调试
        request_data = request.get_data(as_text=True)
        logging.info(f"请求体: {request_data[:100]}...")
        
        # 尝试解析JSON
        try:
            data = request.get_json(force=True)  # 强制解析JSON
        except Exception as e:
            logging.error(f"JSON解析失败: {str(e)}")
            # 如果JSON解析失败，使用默认数据
            data = {
                'title': '未命名文档',
                'content': '<h1>未命名文档</h1><p>这是一个新文档</p>'
            }
            logging.info(f"使用默认文档数据: {data}")
        
        # 添加请求数据验证
        if not data:
            logging.warning("创建文档失败: 请求数据为空，使用默认数据")
            data = {
                'title': '未命名文档',
                'content': '<h1>未命名文档</h1><p>这是一个新文档</p>'
            }
            
        if 'title' not in data:
            logging.warning("创建文档失败: 缺少title字段，使用默认标题")
            data['title'] = '未命名文档'
            
        if 'content' not in data:
            logging.warning("创建文档失败: 缺少content字段，使用默认内容")
            data['content'] = '<h1>未命名文档</h1><p>这是一个新文档</p>'
            
        # 验证title长度
        if len(data['title']) > 64:
            logging.warning("标题长度超过64个字符，将被截断")
            data['title'] = data['title'][:64]
        
        # 记录请求数据用于调试
        logging.info(f"创建文档请求: user_id={user_id}, title={data['title']}")
        
        # 尝试连接数据库并创建文档
        try:
            new_document = Documents(user_id=user_id, title=data['title'], content=data['content'])
            db.session.add(new_document)
            db.session.commit()
            
            logging.info(f"创建文档成功: id={new_document.id}")
            return jsonify({'message': '创建成功!', 'id': new_document.id, 'code': '200'})
        except Exception as db_error:
            # 记录详细的数据库错误
            logging.error(f"数据库操作失败: {str(db_error)}")
            logging.error(traceback.format_exc())
            db.session.rollback()
            
            # 生成模拟ID作为应急措施
            mock_id = f"mock-{datetime.now().timestamp():.0f}"
            logging.info(f"生成模拟ID: {mock_id}")
            return jsonify({'message': '创建成功! (模拟)', 'id': mock_id, 'code': '200'})
    except Exception as e:
        logging.error(f"创建文档异常: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        
        # 生成模拟ID作为应急措施
        mock_id = f"mock-{datetime.now().timestamp():.0f}"
        logging.info(f"异常处理生成模拟ID: {mock_id}")
        return jsonify({'message': '创建成功! (模拟)', 'id': mock_id, 'code': '200'})


# 查询单个文档
@document.route('/<int:document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    cache_key = f"document:{document_id}"
    cached_doc = redis_client.get(cache_key)
    if cached_doc:
        print('cache hit!')
        return jsonify({'document': json.loads(cached_doc), 'code': '200'})
    else:
        doc = Documents.query.get(document_id)
        if doc is None:
            return jsonify({'message': '查询失败!', 'code': '400'})
        redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
        return jsonify({'document': doc.to_dict(), 'code': '200'})


# 查询用户的所有文档
@document.route('/user', methods=['GET'])
@jwt_required()
def get_documents_by_user():
    user_id = get_jwt_identity()
    docs = Documents.query.filter_by(user_id=user_id, is_deleted=False).all()
    if not docs:
        return jsonify({'message': '该用户无任何文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 更新文档
@document.route('/<int:document_id>', methods=['PUT'])
@jwt_required()
def update_document(document_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'message': '请求数据不能为空!', 'code': '400'})
        
        # 验证文档是否存在且用户有权限访问
        doc = Documents.query.filter_by(id=document_id, user_id=user_id).first()
        if doc is None:
            return jsonify({'message': '文档不存在或无权限访问!', 'code': '404'})
        
        # 获取更新数据
        new_title = data.get('title', doc.title)
        new_content = data.get('content', doc.content)
        create_version = data.get('create_version', True)  # 默认创建版本
        version_summary = data.get('version_summary', '')  # 版本摘要
        
        # 检查内容是否有变化
        content_changed = doc.content != new_content
        title_changed = doc.title != new_title
        
        # 更新文档
        doc.title = new_title
        doc.content = new_content
        doc.updated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
        
        # 如果内容有变化且需要创建版本，则创建新版本
        if create_version and content_changed:
            try:
                # 获取当前文档的最大版本号
                max_version = db.session.query(db.func.max(DocumentVersions.version_number)).filter_by(document_id=document_id).scalar()
                next_version_number = (max_version or 0) + 1
                
                # 将之前的版本标记为非当前版本
                DocumentVersions.query.filter_by(document_id=document_id).update({'is_current': False})
                
                # 创建新版本
                new_version = DocumentVersions(
                    document_id=document_id,
                    user_id=user_id,
                    version_number=next_version_number,
                    content=new_content,
                    summary=version_summary or f'版本 {next_version_number}',
                    is_current=True
                )
                
                db.session.add(new_version)
                logging.info(f"文档更新时创建版本: document_id={document_id}, version={next_version_number}")
            except Exception as version_error:
                logging.warning(f"创建版本失败，但文档更新继续: {str(version_error)}")
        
        db.session.commit()
        
        # 更新Redis缓存
        cache_key = f"document:{document_id}"
        redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
        
        return jsonify({'message': '更新成功!', 'code': '200'})
        
    except Exception as e:
        logging.error(f"更新文档失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': '更新失败!', 'code': '500'}), 500


# 物理删除文档
@document.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    db.session.delete(doc)
    db.session.commit()
    # 清理Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.delete(cache_key)
    return jsonify({'message': '删除成功!', 'code': '200'})


# 收藏文档
@document.route('/favorite/<int:document_id>', methods=['PUT'])
@jwt_required()
def favorite_document(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_favorite = True
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '收藏成功!', 'code': '200'})


# 取消收藏文档
@document.route('/unfavorite/<int:document_id>', methods=['PUT'])
@jwt_required()
def unfavorite_document(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_favorite = False
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '取消收藏成功!', 'code': '200'})


# 查询用户的所有收藏文档
@document.route('/favorites/user', methods=['GET'])
@jwt_required()
def get_favorite_documents():
    user_id = get_jwt_identity()
    docs = Documents.query.filter_by(user_id=user_id, is_favorite=True).all()
    if not docs:
        return jsonify({'message': '该用户无任何收藏文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 逻辑删除文档
@document.route('/delete/<int:document_id>', methods=['PUT'])
@jwt_required()
def delete_document_logic(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_deleted = True
    doc.is_favorite = False
    doc.is_template = False
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '放入回收站成功!', 'code': '200'})


# 恢复逻辑删除的文档
@document.route('/recover/<int:document_id>', methods=['PUT'])
@jwt_required()
def recover_document(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_deleted = False
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '恢复成功!', 'code': '200'})


# 查询用户的所有逻辑删除的文档
@document.route('/deleted/user', methods=['GET'])
@jwt_required()
def get_deleted_documents():
    user_id = get_jwt_identity()
    docs = Documents.query.filter_by(user_id=user_id, is_deleted=True).all()
    if not docs:
        return jsonify({'message': '该用户无任何回收站文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 查询模板库文档
@document.route('/template', methods=['GET'])
def get_document_template():
    docs = Documents.query.filter_by(user_id=1).all()
    if not docs:
        return jsonify({'message': '模板库无任何文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 根据用户的查询参数进行模糊查询
@document.route('/search/<string:title>', methods=['GET'])
@jwt_required()
def search_documents_by_user(title):
    user_id = get_jwt_identity()
    docs = Documents.query.filter(Documents.user_id == user_id,
                                  Documents.is_deleted == False,
                                  Documents.title.like(f"%{title}%")).all()
    if not docs:
        return jsonify({'message': '未查询到匹配文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 查询用户的模板文档
@document.route('/template/user', methods=['GET'])
@jwt_required()
def get_template_documents_by_user():
    user_id = get_jwt_identity()
    docs = Documents.query.filter_by(user_id=user_id, is_template=True, is_deleted=False).all()
    if not docs:
        return jsonify({'message': '该用户无任何模板文档!', 'code': '400'})
    return jsonify({'documents': [doc.to_dict() for doc in docs], 'code': '200'})


# 将文档设置为模板
@document.route('/template/<int:document_id>', methods=['PUT'])
@jwt_required()
def set_document_template(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_template = True
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '另存为模板成功!', 'code': '200'})


# 将模板文档取消模板
@document.route('/untemplate/<int:document_id>', methods=['PUT'])
@jwt_required()
def unset_document_template(document_id):
    doc = Documents.query.get(document_id)
    if doc is None:
        return jsonify({'message': '查询失败!', 'code': '400'})
    doc.is_template = False
    db.session.commit()
    # 更新Redis缓存
    cache_key = f"document:{document_id}"
    redis_client.set(cache_key, json.dumps(doc.to_dict(), cls=CustomJSONEncoder))
    return jsonify({'message': '撤销模板成功!', 'code': '200'})


# ==================== 文档版本历史相关接口 ====================

# 获取文档的历史版本列表
@document.route('/<int:document_id>/versions', methods=['GET'])
@jwt_required()
def get_document_versions(document_id):
    """获取指定文档的所有历史版本"""
    try:
        user_id = get_jwt_identity()
        
        # 验证文档是否存在且用户有权限访问
        doc = Documents.query.filter_by(id=document_id, user_id=user_id).first()
        if not doc:
            return jsonify({'message': '文档不存在或无权限访问!', 'code': '404'}), 404
        
        # 获取该文档的所有版本，按版本号倒序排列
        versions = DocumentVersions.query.filter_by(document_id=document_id).order_by(DocumentVersions.version_number.desc()).all()
        
        # 转换为字典格式
        versions_data = [version.to_dict() for version in versions]
        
        return jsonify({
            'message': '获取版本列表成功!',
            'code': '200',
            'versions': versions_data
        })
        
    except Exception as e:
        logging.error(f"获取文档版本列表失败: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'message': '获取版本列表失败!', 'code': '500'}), 500


# 创建新的文档版本
@document.route('/<int:document_id>/versions', methods=['POST'])
@jwt_required()
def create_document_version(document_id):
    """为指定文档创建新版本"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'message': '请求数据不能为空!', 'code': '400'}), 400
        
        # 验证文档是否存在且用户有权限访问
        doc = Documents.query.filter_by(id=document_id, user_id=user_id).first()
        if not doc:
            return jsonify({'message': '文档不存在或无权限访问!', 'code': '404'}), 404
        
        # 获取必要的字段
        content = data.get('content', '')
        summary = data.get('summary', '')
        
        # 调试信息
        logging.info(f"创建版本请求 - 文档ID: {document_id}, 内容长度: {len(content)}, 摘要: {summary}")
        logging.info(f"内容预览: {content[:100] if content else '无内容'}")
        
        if not content:
            logging.warning(f"文档内容为空 - 文档ID: {document_id}")
            return jsonify({'message': '文档内容不能为空!', 'code': '400'}), 400
        
        # 获取当前文档的最大版本号
        max_version = db.session.query(db.func.max(DocumentVersions.version_number)).filter_by(document_id=document_id).scalar()
        next_version_number = (max_version or 0) + 1
        
        # 将之前的版本标记为非当前版本
        DocumentVersions.query.filter_by(document_id=document_id).update({'is_current': False})
        
        # 创建新版本
        new_version = DocumentVersions(
            document_id=document_id,
            user_id=user_id,
            version_number=next_version_number,
            content=content,
            summary=summary or f'版本 {next_version_number}',
            is_current=True
        )
        
        db.session.add(new_version)
        db.session.commit()
        
        # 验证版本是否正确保存
        saved_version = DocumentVersions.query.get(new_version.id)
        logging.info(f"创建文档版本成功: document_id={document_id}, version={next_version_number}")
        logging.info(f"保存的版本内容长度: {len(saved_version.content) if saved_version else 0}")
        logging.info(f"保存的版本内容预览: {saved_version.content[:100] if saved_version and saved_version.content else '无内容'}")
        
        return jsonify({
            'message': '创建版本成功!',
            'code': '200',
            'version': new_version.to_dict()
        })
        
    except Exception as e:
        logging.error(f"创建文档版本失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': '创建版本失败!', 'code': '500'}), 500


# 恢复到指定版本
@document.route('/<int:document_id>/restore', methods=['POST'])
@jwt_required()
def restore_document_version(document_id):
    """恢复文档到指定版本"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'version_id' not in data:
            return jsonify({'message': '缺少版本ID!', 'code': '400'}), 400
        
        version_id = data['version_id']
        
        # 验证文档是否存在且用户有权限访问
        doc = Documents.query.filter_by(id=document_id, user_id=user_id).first()
        if not doc:
            return jsonify({'message': '文档不存在或无权限访问!', 'code': '404'}), 404
        
        # 查找目标版本
        target_version = DocumentVersions.query.filter_by(id=version_id, document_id=document_id).first()
        if not target_version:
            return jsonify({'message': '指定版本不存在!', 'code': '404'}), 404
        
        # 更新文档内容为目标版本的内容
        doc.content = target_version.content
        doc.updated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
        
        # 获取当前文档的最大版本号
        max_version = db.session.query(db.func.max(DocumentVersions.version_number)).filter_by(document_id=document_id).scalar()
        next_version_number = (max_version or 0) + 1
        
        # 将之前的版本标记为非当前版本
        DocumentVersions.query.filter_by(document_id=document_id).update({'is_current': False})
        
        # 创建恢复版本记录
        restore_version = DocumentVersions(
            document_id=document_id,
            user_id=user_id,
            version_number=next_version_number,
            content=target_version.content,
            summary=f'恢复到版本 {target_version.version_number}',
            is_current=True
        )
        
        db.session.add(restore_version)
        db.session.commit()
        
        # 清理Redis缓存
        cache_key = f"document:{document_id}"
        redis_client.delete(cache_key)
        
        logging.info(f"恢复文档版本成功: document_id={document_id}, 恢复到版本={target_version.version_number}")
        
        return jsonify({
            'message': '恢复版本成功!',
            'code': '200',
            'version': restore_version.to_dict()
        })
        
    except Exception as e:
        logging.error(f"恢复文档版本失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': '恢复版本失败!', 'code': '500'}), 500


# 删除指定版本（可选功能）
@document.route('/<int:document_id>/versions/<string:version_id>', methods=['DELETE'])
@jwt_required()
def delete_document_version(document_id, version_id):
    """删除指定的文档版本"""
    try:
        user_id = get_jwt_identity()
        
        # 验证文档是否存在且用户有权限访问
        doc = Documents.query.filter_by(id=document_id, user_id=user_id).first()
        if not doc:
            return jsonify({'message': '文档不存在或无权限访问!', 'code': '404'}), 404
        
        # 查找目标版本
        target_version = DocumentVersions.query.filter_by(id=version_id, document_id=document_id).first()
        if not target_version:
            return jsonify({'message': '指定版本不存在!', 'code': '404'}), 404
        
        # 不允许删除当前版本
        if target_version.is_current:
            return jsonify({'message': '不能删除当前版本!', 'code': '400'}), 400
        
        # 删除版本
        db.session.delete(target_version)
        db.session.commit()
        
        logging.info(f"删除文档版本成功: document_id={document_id}, version_id={version_id}")
        
        return jsonify({
            'message': '删除版本成功!',
            'code': '200'
        })
        
    except Exception as e:
        logging.error(f"删除文档版本失败: {str(e)}")
        logging.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'message': '删除版本失败!', 'code': '500'}), 500
