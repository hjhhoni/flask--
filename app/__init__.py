from flask import Flask
from config import Config

# 创建全局app变量
app = Flask(__name__)
app.config.from_object(Config)

def create_app():
    # 使用全局app变量而不是创建新的实例
    global app
    
    # 确保routes.py中导入了Blueprint
    # 导入并注册蓝图
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app