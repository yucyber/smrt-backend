from database import db
from datetime import datetime

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(255), default='default_icon')
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('Users', backref=db.backref('knowledge_bases', lazy=True))

class KnowledgeBaseDocument(db.Model):
    __tablename__ = 'knowledge_base_documents'

    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_bases.id', ondelete='CASCADE'), primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True)
    added_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    knowledge_base = db.relationship('KnowledgeBase', backref=db.backref('document_associations', lazy='dynamic'))
    document = db.relationship('Documents', backref=db.backref('knowledge_base_associations', lazy='dynamic'))
    added_by_user = db.relationship('Users')

class DocumentAccess(db.Model):
    __tablename__ = 'document_accesses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    document_title = db.Column(db.String(64), nullable=False)
    accessed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('Users', backref=db.backref('document_accesses', lazy=True))
    document = db.relationship('Documents', backref=db.backref('accesses', lazy=True)) 