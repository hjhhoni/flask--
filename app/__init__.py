from flask import Flask
from config import Config

# 创建全局app变量
app = Flask(__name__)
app.config.from_object(Config)

def create_app():
    # 导入路由函数
    from app import routes
    
    # 注册路由
    app.add_url_rule('/', 'index', routes.index)
    app.add_url_rule('/api/funds', 'get_funds', routes.get_funds)
    app.add_url_rule('/api/update-funds', 'update_funds', routes.update_funds)
    app.add_url_rule('/analysis', 'analysis', routes.analysis)
    app.add_url_rule('/api/chart-data', 'get_chart_data', routes.get_chart_data)
    app.add_url_rule('/prediction', 'prediction', routes.prediction)
    app.add_url_rule('/api/predictions', 'get_predictions', routes.get_predictions)
    
    # 添加新的路由
    app.add_url_rule('/dashboard', 'dashboard', routes.dashboard)
    app.add_url_rule('/api/dashboard-data', 'get_dashboard_data', routes.get_dashboard_data)
    
    return app