from flask import render_template, request, jsonify, Flask, current_app, Blueprint, send_file
from datetime import datetime
import pymysql
import pandas as pd  # 添加pandas导入
from config import Config
from app.crawler.fund_crawler import FundCrawler
from app.analysis.fund_analyzer import FundAnalyzer
import os

# 创建蓝图
main_bp = Blueprint('main', __name__)

# Database configuration
db_config = {
    'host': Config.MYSQL_HOST,
    'user': Config.MYSQL_USER,
    'password': Config.MYSQL_PASSWORD,
    'database': Config.MYSQL_DB,
    'charset': 'utf8mb4'
}

# 修改这里，使用main_bp而不是app
@main_bp.route('/')
def index():
    # 将根路由重定向到index页面
    from flask import redirect, url_for
    return redirect(url_for('main.login_page'))

# 添加登录页面路由
@main_bp.route('/index')
def login_page():
    return render_template('index.html')

# 添加funds页面路由
@main_bp.route('/funds')
def funds_page():
    return render_template('funds.html')

@main_bp.route('/api/funds')
def get_funds():
    search = request.args.get('search', '')
    
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        if search:
            sql = """SELECT * FROM funds 
                    WHERE fund_code LIKE %s OR fund_name LIKE %s 
                    ORDER BY daily_growth_rate DESC"""
            cursor.execute(sql, (f'%{search}%', f'%{search}%'))
        else:
            sql = "SELECT * FROM funds ORDER BY daily_growth_rate DESC LIMIT 10000"
            cursor.execute(sql)
            
        funds = cursor.fetchall()
        
        return jsonify({'funds': funds})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@main_bp.route('/api/update', methods=['GET', 'POST'])
def update_funds():
    try:
        # 获取前端传递的参数
        max_items = request.args.get('max_items', default=15000, type=int)
        max_pages = request.args.get('max_pages', default=1, type=int)
        
        crawler = FundCrawler()
        funds_data = crawler.crawl_funds(max_items=max_items, max_pages=max_pages)
        
        if funds_data:
            crawler.save_to_db(funds_data)
            return jsonify({'message': f'成功更新 {len(funds_data)} 条基金数据'})
        else:
            return jsonify({'message': '未获取到基金数据'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/analysis')
def analysis():
    return render_template('analysis.html', now=datetime.now())

@main_bp.route('/api/chart-data')
def get_chart_data():
    """获取图表数据的API端点"""
    # 函数内容保持不变
    conn = None
    cursor = None
    try:
        # 建立数据库连接
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 简化查询 - 只获取必要的数据
        funds_query = """
        SELECT fund_code, fund_name, latest_net_value, daily_growth_rate 
        FROM funds 
        WHERE latest_net_value > 0 AND daily_growth_rate IS NOT NULL
        """
        cursor.execute(funds_query)
        funds = cursor.fetchall()
        
        # 确保数据不为空
        if not funds:
            return jsonify({'error': '数据库中没有找到有效的基金数据'}), 404
        
        # 对数据进行排序，获取表现最佳和最差的基金
        funds_sorted = sorted(funds, key=lambda x: x['daily_growth_rate'] if x['daily_growth_rate'] is not None else 0)
        bottom_funds = funds_sorted[:20]  # 表现最差的20个
        top_funds = funds_sorted[-20:]    # 表现最佳的20个
        top_funds.reverse()  # 反转顺序，使最高的在前面
        
        # 计算正负增长比例
        positive = sum(1 for fund in funds if fund['daily_growth_rate'] > 0)
        negative = sum(1 for fund in funds if fund['daily_growth_rate'] < 0)
        zero = sum(1 for fund in funds if fund['daily_growth_rate'] == 0)
        
        # 构建返回数据
        data = {
            'top_funds': {
                'names': [str(fund['fund_name']) for fund in top_funds],
                'codes': [str(fund['fund_code']) for fund in top_funds],
                'rates': [float(fund['daily_growth_rate']) for fund in top_funds]
            },
            'bottom_funds': {
                'names': [str(fund['fund_name']) for fund in bottom_funds],
                'codes': [str(fund['fund_code']) for fund in bottom_funds],
                'rates': [float(fund['daily_growth_rate']) for fund in bottom_funds]
            },
            'distribution': {
                'values': [float(fund['daily_growth_rate']) for fund in funds]
            },
            'net_value_distribution': {
                'values': [float(fund['latest_net_value']) for fund in funds if fund['latest_net_value'] is not None]
            },
            'scatter': {
                'net_values': [float(fund['latest_net_value']) for fund in funds if fund['latest_net_value'] is not None],
                'growth_rates': [float(fund['daily_growth_rate']) for fund in funds if fund['daily_growth_rate'] is not None]
            },
            'pie_chart': {
                'labels': ['正增长', '负增长', '零增长'],
                'values': [positive, negative, zero]
            }
        }
        
        return jsonify(data)
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"获取图表数据出错: {error_msg}")
        print(error_trace)
        return jsonify({'error': f'服务器错误: {error_msg}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@main_bp.route('/prediction')
def prediction():
    """显示基金预测页面"""
    now = datetime.now()
    return render_template('prediction.html', now=now)

@main_bp.route('/api/predictions')
def get_predictions():
    """获取基金预测数据的API"""
    try:
        # 获取预测时间范围参数
        prediction_range = request.args.get('range', default=30, type=int)
        
        # 从数据库获取基金数据
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = "SELECT * FROM funds ORDER BY daily_growth_rate DESC"
        cursor.execute(sql)
        funds = cursor.fetchall()
        
        if not funds:
            return jsonify({'error': '没有找到基金数据'}), 404
        
        # 生成模拟预测数据，传递预测时间范围
        predictions = generate_prediction_data(funds, prediction_range)
        
        return jsonify({'predictions': predictions})
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"获取预测数据时出错: {error_msg}")
        print(error_trace)
        return jsonify({'error': '获取预测数据失败'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# 修改generate_prediction_data函数，接受预测时间范围参数
def generate_prediction_data(funds, prediction_range=30):
    """生成模拟的预测数据"""
    import random
    from datetime import datetime, timedelta
    
    # 市场趋势预测
    today = datetime.now()
    # 根据预测时间范围调整历史数据的天数
    history_days = min(30, prediction_range)
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(history_days, 0, -1)]
    future_dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, prediction_range + 1)]
    
    # 生成历史数据和预测数据
    base_value = 3000
    actual_values = []
    for i in range(history_days):
        change = random.uniform(-50, 50)
        base_value += change
        actual_values.append(round(base_value, 2))
    
    # 预测未来趋势
    predicted_values = []
    last_value = actual_values[-1]
    
    # 根据不同的预测时间范围调整波动幅度
    if prediction_range <= 3:
        volatility = (-10, 15)  # 短期波动较小
    elif prediction_range <= 7:
        volatility = (-15, 20)  # 一周波动适中
    elif prediction_range <= 30:
        volatility = (-30, 40)  # 一个月波动较大
    else:
        volatility = (-50, 60)  # 半年波动很大
    
    for i in range(prediction_range):
        change = random.uniform(volatility[0], volatility[1])
        last_value += change
        predicted_values.append(round(last_value, 2))
    
    # 确定整体趋势
    trend = 'stable'
    if predicted_values[-1] > actual_values[-1] * 1.05:
        trend = 'up'
    elif predicted_values[-1] < actual_values[-1] * 0.95:
        trend = 'down'
    
    # 构建时间线数据
    timeline = []
    for i in range(history_days):
        timeline.append({
            'date': dates[i],
            'actual': actual_values[i],
            'predicted': None
        })
    
    for i in range(prediction_range):
        if i < min(5, prediction_range // 6):  # 前几天显示实际值和预测值的重叠
            timeline.append({
                'date': future_dates[i],
                'actual': None,
                'predicted': predicted_values[i]
            })
        else:
            timeline.append({
                'date': future_dates[i],
                'actual': None,
                'predicted': predicted_values[i]
            })
    
    # 根据预测时间范围调整市场趋势摘要文本
    time_range_text = ''
    if prediction_range <= 3:
        time_range_text = '未来三天'
    elif prediction_range <= 7:
        time_range_text = '未来一周'
    elif prediction_range <= 30:
        time_range_text = '未来一个月'
    else:
        time_range_text = '未来半年'
    
    # 市场趋势摘要
    market_trend = {
        'overallTrend': trend,
        'confidence': random.randint(60, 95),
        'summary': f'根据历史数据分析和市场指标预测，{time_range_text}市场整体呈{("上涨" if trend == "up" else "下跌" if trend == "down" else "稳定")}趋势。主要受{random.choice(["政策调整", "经济数据", "市场情绪", "外部环境", "资金流向"])}等因素影响。',
        'timeline': timeline
    }
    
    # 基金类型预测
    fund_types = ['股票型', '债券型', '混合型', '指数型', '货币型', 'QDII', '其他']
    fund_type_predictions = {}
    for fund_type in fund_types:
        predicted_growth = round(random.uniform(-5, 10), 2)
        if fund_type == '股票型':
            predicted_growth = round(random.uniform(-2, 15), 2)  # 股票型波动更大
        elif fund_type == '债券型':
            predicted_growth = round(random.uniform(-1, 5), 2)   # 债券型相对稳定
        
        fund_type_predictions[fund_type] = {
            'predicted_growth': predicted_growth,
            'confidence': random.randint(60, 90)
        }
    
    # 预测表现最佳的基金
    top_funds = []
    sorted_funds = sorted(funds, key=lambda x: random.uniform(-5, 20), reverse=True)
    for i in range(min(10, len(sorted_funds))):
        fund = sorted_funds[i]
        top_funds.append({
            'fund_code': fund['fund_code'],
            'fund_name': fund['fund_name'],
            'predicted_growth': round(random.uniform(5, 20), 2),
            'confidence': random.randint(65, 90)
        })
    
    # 预测置信度分布
    confidence_ranges = ['0-50%', '51-60%', '61-70%', '71-80%', '81-90%', '91-100%']
    confidence_distribution = {}
    for confidence_range in confidence_ranges:
        if confidence_range == '0-50%':
            confidence_distribution[confidence_range] = random.randint(5, 20)
        elif confidence_range == '51-60%':
            confidence_distribution[confidence_range] = random.randint(10, 30)
        elif confidence_range == '61-70%':
            confidence_distribution[confidence_range] = random.randint(20, 50)
        elif confidence_range == '71-80%':
            confidence_distribution[confidence_range] = random.randint(40, 80)
        elif confidence_range == '81-90%':
            confidence_distribution[confidence_range] = random.randint(30, 60)
        else:
            confidence_distribution[confidence_range] = random.randint(5, 25)
    
    # 预测时间线
    timeline_prediction = []
    baseline = predicted_values[0]
    
    # 根据预测时间范围调整乐观/悲观预测的波动幅度
    if prediction_range <= 3:
        optimistic_factor = (0.01, 0.03)
        pessimistic_factor = (0.01, 0.02)
    elif prediction_range <= 7:
        optimistic_factor = (0.01, 0.04)
        pessimistic_factor = (0.01, 0.03)
    elif prediction_range <= 30:
        optimistic_factor = (0.01, 0.05)
        pessimistic_factor = (0.01, 0.04)
    else:
        optimistic_factor = (0.02, 0.08)
        pessimistic_factor = (0.02, 0.06)
    
    for i in range(prediction_range):
        optimistic = round(predicted_values[i] * (1 + random.uniform(optimistic_factor[0], optimistic_factor[1])), 2)
        pessimistic = round(predicted_values[i] * (1 - random.uniform(pessimistic_factor[0], pessimistic_factor[1])), 2)
        
        timeline_prediction.append({
            'date': future_dates[i],
            'baseline': predicted_values[i],
            'optimistic': optimistic,
            'pessimistic': pessimistic
        })
    
    # 推荐基金
    recommendations = []
    risk_levels = ['低风险', '中低风险', '中风险', '中高风险', '高风险']
    recommendation_reasons = [
        '历史表现稳定，预期收益良好',
        '所属行业前景看好，增长潜力大',
        '基金经理管理能力强，历史业绩优秀',
        '投资策略稳健，风险控制良好',
        '市场调整中表现出较强抗跌性',
        '配置合理，分散风险效果好',
        '受益于政策利好，行业景气度高',
        '估值处于历史低位，具有较高安全边际'
    ]
    
    for i in range(min(9, len(funds))):
        fund = random.choice(funds)
        predicted_growth = round(random.uniform(3, 15), 2)
        prediction_type = 'positive' if predicted_growth > 5 else 'neutral' if predicted_growth > 0 else 'negative'
        
        recommendations.append({
            'fund_code': fund['fund_code'],
            'fund_name': fund['fund_name'],
            'predicted_growth': predicted_growth,
            'confidence': random.randint(70, 95),
            'prediction_type': prediction_type,
            'recommendation_reason': random.choice(recommendation_reasons),
            'risk_level': random.choice(risk_levels)
        })
    
    return {
        'marketTrend': market_trend,
        'fundTypePredictions': fund_type_predictions,
        'topFunds': top_funds,
        'confidenceDistribution': confidence_distribution,
        'timelinePrediction': timeline_prediction,
        'recommendations': recommendations
    }

# 在文件顶部添加以下导入语句
from app import app
from datetime import datetime, timedelta
import random
from app.models import Fund
from flask import render_template, jsonify

# 然后添加新的路由
# 修改这里，使用main_bp而不是app
@main_bp.route('/dashboard')
def dashboard():
    """可视化大屏页面"""
    now = datetime.now()
    return render_template('dashboard.html', now=now)

@main_bp.route('/api/dashboard-data')
def get_dashboard_data():
    """获取可视化大屏数据"""
    try:
        # 使用pymysql直接查询数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = "SELECT * FROM funds"
        cursor.execute(sql)
        funds = cursor.fetchall()
        
        if not funds:
            return jsonify({'error': '没有找到基金数据'})
        
        # 计算汇总数据
        total_funds = len(funds)
        # 修改这里：将Decimal转换为float
        net_values = [float(fund['latest_net_value']) for fund in funds if fund['latest_net_value']]
        growth_rates = [float(fund['daily_growth_rate']) for fund in funds if fund['daily_growth_rate'] is not None]
        
        avg_net_value = sum(net_values) / len(net_values) if net_values else 0
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        up_count = sum(1 for rate in growth_rates if rate > 0)
        up_ratio = (up_count / len(growth_rates) * 100) if growth_rates else 0
        
        # 假设前一天数据（实际应从数据库获取）
        prev_avg_net_value = avg_net_value * 0.99  # 模拟数据
        prev_avg_growth_rate = avg_growth_rate * 0.9  # 模拟数据
        
        summary = {
            'total_funds': total_funds,
            'avg_net_value': avg_net_value,
            'avg_growth_rate': avg_growth_rate,
            'up_ratio': up_ratio,
            'avg_net_value_change': avg_net_value - prev_avg_net_value,
            'avg_growth_rate_change': avg_growth_rate - prev_avg_growth_rate
        }
        
        # 模拟趋势数据（实际应从数据库获取历史数据）
        dates = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(14, -1, -1)]
        trend_data = {
            'dates': dates,
            'avg_net_values': [avg_net_value * (1 + random.uniform(-0.02, 0.02)) for _ in range(15)],
            'avg_growth_rates': [avg_growth_rate * (1 + random.uniform(-0.5, 0.5)) for _ in range(15)]
        }
        
        # 基金类型分布
        fund_types = ['股票型', '混合型', '债券型', '指数型', 'QDII', '货币型']
        type_values = [30, 25, 20, 15, 5, 5]  # 模拟数据
        
        type_distribution = {
            'labels': fund_types,
            'values': type_values
        }
        
        # 表现最佳基金 - 修改这里：使用字典访问方式
        top_funds = sorted(funds, key=lambda x: x['daily_growth_rate'] if x['daily_growth_rate'] is not None else -float('inf'), reverse=True)[:8]
        top_performers = {
            'names': [fund['fund_name'] for fund in top_funds],
            'codes': [fund['fund_code'] for fund in top_funds],
            'rates': [fund['daily_growth_rate'] for fund in top_funds]
        }
        
        # 增长率分布
        min_rate = min(growth_rates) if growth_rates else 0
        max_rate = max(growth_rates) if growth_rates else 0
        bin_size = (max_rate - min_rate) / 10 if max_rate > min_rate else 1
        
        bins = [0] * 10
        bin_labels = []
        
        for i in range(10):
            bin_start = min_rate + i * bin_size
            bin_end = min_rate + (i + 1) * bin_size
            bin_labels.append(f"{bin_start:.2f} - {bin_end:.2f}")
        
        for rate in growth_rates:
            for i in range(10):
                bin_start = min_rate + i * bin_size
                bin_end = min_rate + (i + 1) * bin_size
                if rate >= bin_start and (rate < bin_end or (i == 9 and rate == bin_end)):
                    bins[i] += 1
                    break
        
        growth_distribution = {
            'labels': bin_labels,
            'values': bins
        }
        
        # 市场概览数据
        market_datasets = [
            {
                'label': '沪深300',
                'data': [random.uniform(-2, 2) for _ in range(15)],
                'borderColor': '#ff6b6b',
                'backgroundColor': 'rgba(255, 107, 107, 0.1)',
                'fill': False,
                'tension': 0.4
            },
            {
                'label': '股票型基金平均',
                'data': [random.uniform(-1.5, 1.5) for _ in range(15)],
                'borderColor': '#4ecdc4',
                'backgroundColor': 'rgba(78, 205, 196, 0.1)',
                'fill': False,
                'tension': 0.4
            },
            {
                'label': '混合型基金平均',
                'data': [random.uniform(-1, 1) for _ in range(15)],
                'borderColor': '#ffbe76',
                'backgroundColor': 'rgba(255, 190, 118, 0.1)',
                'fill': False,
                'tension': 0.4
            }
        ]
        
        market_overview = {
            'dates': dates,
            'datasets': market_datasets
        }
        
        return jsonify({
            'summary': summary,
            'trend_data': trend_data,
            'type_distribution': type_distribution,
            'top_performers': top_performers,
            'growth_distribution': growth_distribution,
            'market_overview': market_overview
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

# 添加新基金
@main_bp.route('/api/funds', methods=['POST'])
def add_fund():
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['fund_code', 'fund_name', 'latest_net_value', 'latest_total_value', 
                          'daily_growth_value', 'daily_growth_rate', 'latest_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查基金代码是否已存在
        cursor.execute("SELECT COUNT(*) FROM funds WHERE fund_code = %s", (data['fund_code'],))
        if cursor.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': '该基金代码已存在'}), 400
        
        # 准备插入数据
        sql = """INSERT INTO funds (fund_code, fund_name, latest_net_value, latest_total_value,
                daily_growth_value, daily_growth_rate, latest_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(sql, (
            data['fund_code'],
            data['fund_name'],
            data['latest_net_value'],
            data['latest_total_value'],
            data['daily_growth_value'],
            data['daily_growth_rate'],
            data['latest_date']
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': '基金添加成功'})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({'success': False, 'message': f'添加基金失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# 更新基金信息
@main_bp.route('/api/funds/<fund_code>', methods=['PUT'])
def update_fund(fund_code):
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['fund_name', 'latest_net_value', 'latest_total_value', 
                          'daily_growth_value', 'daily_growth_rate', 'latest_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查基金是否存在
        cursor.execute("SELECT COUNT(*) FROM funds WHERE fund_code = %s", (fund_code,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'success': False, 'message': '未找到该基金'}), 404
        
        # 准备更新数据
        sql = """UPDATE funds SET 
                fund_name = %s,
                latest_net_value = %s,
                latest_total_value = %s,
                daily_growth_value = %s,
                daily_growth_rate = %s,
                latest_date = %s
                WHERE fund_code = %s"""
        
        cursor.execute(sql, (
            data['fund_name'],
            data['latest_net_value'],
            data['latest_total_value'],
            data['daily_growth_value'],
            data['daily_growth_rate'],
            data['latest_date'],
            fund_code
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': '基金更新成功'})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({'success': False, 'message': f'更新基金失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# 删除基金
@main_bp.route('/api/funds/<fund_code>', methods=['DELETE'])
def delete_fund(fund_code):
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查基金是否存在
        cursor.execute("SELECT COUNT(*) FROM funds WHERE fund_code = %s", (fund_code,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'success': False, 'message': '未找到该基金'}), 404
        
        # 删除基金
        sql = "DELETE FROM funds WHERE fund_code = %s"
        cursor.execute(sql, (fund_code,))
        
        conn.commit()
        return jsonify({'success': True, 'message': '基金删除成功'})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({'success': False, 'message': f'删除基金失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# 获取单个基金详情
@main_bp.route('/api/funds/<fund_code>')
def get_fund_detail(fund_code):
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = "SELECT * FROM funds WHERE fund_code = %s"
        cursor.execute(sql, (fund_code,))
        fund = cursor.fetchone()
        
        if not fund:
            return jsonify({'success': False, 'message': '未找到该基金'}), 404
        
        # 处理日期格式，确保可以被JSON序列化
        if 'latest_date' in fund and fund['latest_date']:
            fund['latest_date'] = fund['latest_date'].strftime('%Y-%m-%d')
            
        return jsonify({'success': True, 'fund': fund})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 用户认证相关路由
@main_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (data['username'],))
        if cursor.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': '该用户名已被注册'}), 400
        
        # 检查邮箱是否已存在
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': '该邮箱已被注册'}), 400
        
        # 密码加密
        import hashlib
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # 生成token
        import uuid
        token = str(uuid.uuid4())
        
        # 插入用户数据
        sql = """INSERT INTO users (username, email, password_hash, token, created_at)
                VALUES (%s, %s, %s, %s, NOW())"""
        
        cursor.execute(sql, (
            data['username'],
            data['email'],
            password_hash,
            token
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': '注册成功', 'token': token})
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@main_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 密码加密
        import hashlib
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # 查询用户
        sql = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
        cursor.execute(sql, (data['username'], password_hash))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 生成新token
        import uuid
        token = str(uuid.uuid4())
        
        # 更新token
        update_sql = "UPDATE users SET token = %s, last_login = NOW() WHERE id = %s"
        cursor.execute(update_sql, (token, user['id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': '登录成功', 'token': token})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@main_bp.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        # 获取Authorization头
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '无效的Authorization头'}), 401
        
        token = auth_header.split(' ')[1]
        
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询token
        sql = "SELECT * FROM users WHERE token = %s"
        cursor.execute(sql, (token,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': '无效的token'}), 401
        
        return jsonify({'success': True, 'message': 'token有效'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# 在routes.py文件中添加批量删除API接口
@main_bp.route('/api/funds/batch-delete', methods=['POST'])
def batch_delete_funds():
    try:
        data = request.get_json()
        
        if not data or 'fund_codes' not in data or not data['fund_codes']:
            return jsonify({'success': False, 'message': '未提供要删除的基金代码'}), 400
            
        fund_codes = data['fund_codes']
        
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 构建IN查询的参数
        placeholders = ', '.join(['%s'] * len(fund_codes))
        sql = f"DELETE FROM funds WHERE fund_code IN ({placeholders})"
        
        cursor.execute(sql, fund_codes)
        deleted_count = cursor.rowcount
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'成功删除 {deleted_count} 个基金',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@main_bp.route('/api/funds/export-csv')
def export_funds_csv():
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取所有基金数据
        sql = "SELECT * FROM funds ORDER BY fund_code"
        cursor.execute(sql)
        funds = cursor.fetchall()
        
        if not funds:
            return jsonify({'error': '没有可导出的数据'}), 404
        
        # 创建DataFrame
        df = pd.DataFrame(funds)
        
        # 创建临时文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'fund_data_{timestamp}.csv'
        export_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'exports')
        os.makedirs(export_path, exist_ok=True)
        filepath = os.path.join(export_path, filename)
        
        # 导出为CSV
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 返回文件
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 打印详细错误信息到控制台
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@main_bp.route('/api/funds/delete-all', methods=['DELETE'])
def delete_all_funds():
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 先获取记录数量
        count_sql = "SELECT COUNT(*) FROM funds"
        cursor.execute(count_sql)
        count = cursor.fetchone()[0]
        
        # 执行删除操作
        sql = "DELETE FROM funds"
        cursor.execute(sql)
        conn.commit()
        
        return jsonify({'success': True, 'message': '所有基金数据已删除', 'count': count})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()