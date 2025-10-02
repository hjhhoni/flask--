class Config:
    # Flask配置
    SECRET_KEY = 'your-secret-key'
    
    # 数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '123456'
    MYSQL_DB = 'flask'
    
    # APScheduler配置
    SCHEDULER_API_ENABLED = True
    JOBS = [
        {
            'id': 'update_fund_data',
            'func': 'app.tasks.scheduled_tasks:update_fund_data',
            'trigger': 'interval',
            'minutes': 30  # 每30分钟更新一次
        }
    ]