from app.crawler.fund_crawler import FundCrawler
import logging
from datetime import datetime

def update_fund_data():
    """每日更新基金数据"""
    # 检查是否为交易日和交易时间
    now = datetime.now()
    if now.weekday() in [5, 6]:  # 周末不更新
        return
    
    if not (9 <= now.hour < 15):  # 只在交易时间更新
        return
        
    try:
        crawler = FundCrawler()
        funds_data = crawler.crawl_funds()
        if funds_data:
            crawler.save_to_db(funds_data)
            logging.info(f"成功更新{len(funds_data)}条基金数据")
    except Exception as e:
        logging.error(f"更新基金数据失败: {str(e)}")