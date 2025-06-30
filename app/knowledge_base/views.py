from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from app.document.models import Documents
from app.auth.models import Users
from .models import KnowledgeBase, KnowledgeBaseDocument, DocumentAccess

# 创建知识库蓝图
knowledge_base_bp = Blueprint('knowledge_base', __name__, url_prefix='/knowledge_base')

# --- 知识库 (Knowledge Bases) API ---

@knowledge_base_bp.route('/knowledge-bases', methods=['POST'])
@jwt_required()
def create_knowledge_base():
    """创建新知识库"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Missing name"}), 400

    current_user_id = get_jwt_identity()
    name = data['name']
    description = data.get('description')
    icon = data.get('icon')

    try:
        new_kb = KnowledgeBase(
            name=name,
            description=description,
            icon=icon,
            creator_id=current_user_id
        )
        db.session.add(new_kb)
        db.session.commit()
        return jsonify({"id": new_kb.id, "name": new_kb.name, "description": new_kb.description, "icon": new_kb.icon}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases', methods=['GET'])
@jwt_required()
def get_user_knowledge_bases():
    """获取当前用户的所有知识库"""
    current_user_id = get_jwt_identity()
    try:
        kbs = KnowledgeBase.query.filter_by(creator_id=current_user_id).all()
        result = [{"id": kb.id, "name": kb.name, "description": kb.description, "icon": kb.icon, "updated_at": kb.updated_at} for kb in kbs]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>', methods=['GET'])
@jwt_required()
def get_knowledge_base_details(kb_id):
    """获取单个知识库详情"""
    current_user_id = get_jwt_identity()
    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=current_user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404
        return jsonify({
            "id": kb.id, "name": kb.name, "description": kb.description, "icon": kb.icon, 
            "creator_id": kb.creator_id, "created_at": kb.created_at, "updated_at": kb.updated_at
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>', methods=['PUT'])
@jwt_required()
def update_knowledge_base(kb_id):
    """更新知识库信息"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    current_user_id = get_jwt_identity()

    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=current_user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404

        kb.name = data.get('name', kb.name)
        kb.description = data.get('description', kb.description)
        kb.icon = data.get('icon', kb.icon)
        
        db.session.commit()
        return jsonify({"message": "Knowledge base updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>', methods=['DELETE'])
@jwt_required()
def delete_knowledge_base(kb_id):
    """删除知识库"""
    current_user_id = get_jwt_identity()
    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=current_user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404
        
        db.session.delete(kb)
        db.session.commit()
        return jsonify({"message": "Knowledge base deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- 知识库-文档关联 (Knowledge Base Documents) API ---

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>/documents', methods=['GET'])
@jwt_required()
def get_documents_in_knowledge_base(kb_id):
    """获取知识库中的所有文档"""
    user_id = get_jwt_identity()
    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404
            
        documents = db.session.query(
                Documents.id, Documents.title, Documents.updated_at, Documents.category, Documents.word_count
            ).join(KnowledgeBaseDocument, Documents.id == KnowledgeBaseDocument.document_id)\
            .filter(KnowledgeBaseDocument.knowledge_base_id == kb_id).all()

        result = [dict(zip(['id', 'title', 'updated_at', 'category', 'word_count'], doc)) for doc in documents]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>/documents', methods=['POST'])
@jwt_required()
def add_document_to_knowledge_base(kb_id):
    """向知识库添加文档"""
    data = request.get_json()
    if not data or 'document_id' not in data:
        return jsonify({"error": "Missing document_id"}), 400

    doc_id = data['document_id']
    user_id = get_jwt_identity()

    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404
        
        # 检查是否已存在
        existing_rel = KnowledgeBaseDocument.query.filter_by(knowledge_base_id=kb_id, document_id=doc_id).first()
        if existing_rel:
            return jsonify({"error": "Document already exists in this knowledge base"}), 409

        new_rel = KnowledgeBaseDocument(
            knowledge_base_id=kb_id,
            document_id=doc_id,
            added_by_user_id=user_id
        )
        db.session.add(new_rel)
        db.session.commit()
        return jsonify({"message": "Document added to knowledge base successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/knowledge-bases/<int:kb_id>/documents/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def remove_document_from_knowledge_base(kb_id, doc_id):
    """从知识库移除文档"""
    user_id = get_jwt_identity()
    try:
        kb = KnowledgeBase.query.filter_by(id=kb_id, creator_id=user_id).first()
        if not kb:
            return jsonify({"error": "Knowledge base not found or access denied"}), 404

        rel = KnowledgeBaseDocument.query.filter_by(knowledge_base_id=kb_id, document_id=doc_id).first()
        if not rel:
            return jsonify({"error": "Document not found in this knowledge base"}), 404
            
        db.session.delete(rel)
        db.session.commit()
        return jsonify({"message": "Document removed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- 用户最近访问 (User Recent Access) API ---

@knowledge_base_bp.route('/user/recent-documents', methods=['GET'])
@jwt_required()
def get_recent_documents():
    """获取用户最近访问的10个文档"""
    user_id = get_jwt_identity()
    try:
        recent_accesses = db.session.query(
                DocumentAccess.document_id, 
                DocumentAccess.document_title, 
                db.func.max(DocumentAccess.accessed_at).label('last_accessed_at')
            ).filter_by(user_id=user_id)\
            .group_by(DocumentAccess.document_id, DocumentAccess.document_title)\
            .order_by(db.desc('last_accessed_at'))\
            .limit(10).all()

        result = [dict(zip(['document_id', 'document_title', 'last_accessed_at'], access)) for access in recent_accesses]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_base_bp.route('/user/document-access', methods=['POST'])
@jwt_required()
def record_document_access():
    """记录用户对文档的访问"""
    data = request.get_json()
    if not data or 'document_id' not in data:
        return jsonify({"error": "Missing document_id"}), 400
    
    doc_id = data['document_id']
    user_id = get_jwt_identity()
    
    try:
        doc = Documents.query.get(doc_id)
        if not doc:
            return jsonify({"error": "Document not found"}), 404
        
        new_access = DocumentAccess(
            user_id=user_id,
            document_id=doc_id,
            document_title=doc.title
        )
        db.session.add(new_access)
        db.session.commit()
        return jsonify({"message": "Access recorded"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500 