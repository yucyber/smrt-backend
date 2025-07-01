from datetime import datetime
from database import db

class Comments(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID格式
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)  # 评论内容
    selected_text = db.Column(db.Text, nullable=True)  # 被评论的文本
    range_from = db.Column(db.Integer, nullable=False)  # 评论范围起始位置
    range_to = db.Column(db.Integer, nullable=False)  # 评论范围结束位置
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)  # 软删除标记
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'text': self.text,
            'selected_text': self.selected_text,
            'range': {
                'from': self.range_from,
                'to': self.range_to
            },
            'timestamp': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_deleted': self.is_deleted
        }