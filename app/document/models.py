from database import db
from datetime import datetime
import pytz   # 导入 pytz 以处理时区
import uuid

class Documents(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)  # 表示文档是否被收藏
    is_deleted = db.Column(db.Boolean, default=False)  # 表示文档是否被逻辑删除
    is_template = db.Column(db.Boolean, default=False)  # 表示文档是否为模板

    def __repr__(self):
        return '<Document %r>' % self.title

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class DocumentVersions(db.Model):
    """文档版本历史表"""
    __tablename__ = 'document_versions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)  # 版本号，从1开始递增
    content = db.Column(db.Text, nullable=False)  # 该版本的文档内容
    summary = db.Column(db.String(255), default='')  # 版本摘要/说明
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), nullable=False)
    is_current = db.Column(db.Boolean, default=False)  # 是否为当前版本
    
    # 建立关系
    document = db.relationship('Documents', backref=db.backref('versions', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<DocumentVersion {self.document_id}-v{self.version_number}>'
    
    def to_dict(self):
        """转换为字典格式，用于API返回"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'version_number': self.version_number,
            'content': self.content,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_current': self.is_current,
            'author': 'User'  # 可以后续扩展为真实用户名
        }
