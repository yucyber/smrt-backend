from flask import Blueprint

collaboration = Blueprint('collaboration', __name__)

from . import views
from .websocket_test import websocket_test

# 注册测试路由
collaboration.register_blueprint(websocket_test)