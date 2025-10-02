import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pymysql
import os
from datetime import datetime
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
from config import Config

class FundAnalyzer:
    def __init__(self):
        self.db_config = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DB,
            'charset': 'utf8mb4'
        }
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'charts')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_fund_data(self, limit=100):
        """从数据库获取基金数据"""
        conn = None
        try:
            conn = pymysql.connect(**self.db_config)
            query = """
            SELECT fund_code, fund_name, latest_net_value, latest_total_value, 
                   daily_growth_rate, latest_date
            FROM funds
            WHERE latest_net_value > 0
            ORDER BY daily_growth_rate DESC
            LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(limit,))
            return df
        except Exception as e:
            print(f"获取基金数据失败: {str(e)}")
            return pd.DataFrame()
        finally:
            if conn:
                conn.close()
    
    def generate_top_funds_chart(self, top_n=20):
        """生成表现最好的前N只基金图表"""
        df = self.get_fund_data(limit=top_n)
        if df.empty:
            return None
            
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df['fund_name'], df['daily_growth_rate'], color='skyblue')
        plt.xlabel('日增长率 (%)')
        plt.ylabel('基金名称')
        plt.title(f'表现最好的{top_n}只基金 (日增长率)')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        # 添加数值标签
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                    f'{width:.2f}%', ha='left', va='center')
        
        plt.tight_layout()
        filename = f'top_{top_n}_funds_{datetime.now().strftime("%Y%m%d")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        return filename
    
    def generate_distribution_chart(self):
        """生成基金日增长率分布图"""
        df = self.get_fund_data(limit=1000)
        if df.empty:
            return None
            
        plt.figure(figsize=(10, 6))
        plt.hist(df['daily_growth_rate'], bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
        plt.xlabel('日增长率 (%)')
        plt.ylabel('基金数量')
        plt.title('基金日增长率分布')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 添加均值线
        mean_value = df['daily_growth_rate'].mean()
        plt.axvline(mean_value, color='red', linestyle='dashed', linewidth=1)
        plt.text(mean_value + 0.1, plt.ylim()[1] * 0.9, f'均值: {mean_value:.2f}%', 
                color='red', ha='left', va='center')
        
        plt.tight_layout()
        filename = f'growth_distribution_{datetime.now().strftime("%Y%m%d")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        return filename
    
    def generate_scatter_plot(self):
        """生成净值与增长率的散点图"""
        df = self.get_fund_data(limit=500)
        if df.empty:
            return None
            
        plt.figure(figsize=(10, 8))
        plt.scatter(df['latest_net_value'], df['daily_growth_rate'], 
                   alpha=0.6, c=df['daily_growth_rate'], cmap='viridis')
        
        plt.xlabel('最新净值')
        plt.ylabel('日增长率 (%)')
        plt.title('基金净值与日增长率关系')
        plt.colorbar(label='日增长率 (%)')
        plt.grid(linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        filename = f'value_growth_scatter_{datetime.now().strftime("%Y%m%d")}.png'
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath)
        plt.close()
        return filename
    
    def generate_all_charts(self):
        """生成所有分析图表"""
        results = {}
        results['top_funds'] = self.generate_top_funds_chart()
        results['distribution'] = self.generate_distribution_chart()
        results['scatter'] = self.generate_scatter_plot()
        return results