from app import create_app

app = create_app()

# 注册路由
from app.routes import index, get_funds, update_funds, analysis
app.add_url_rule('/', 'index', index)
app.add_url_rule('/api/funds', 'get_funds', get_funds)
app.add_url_rule('/api/update', 'update_funds', update_funds)
app.add_url_rule('/analysis', 'analysis', analysis)

if __name__ == '__main__':
    app.run(debug=True)