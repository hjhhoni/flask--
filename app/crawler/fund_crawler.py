from DrissionPage import ChromiumPage
import pymysql
import re
import time
from datetime import datetime
import logging
from config import Config

class FundCrawler:
    def __init__(self):
        self.db_config = {
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DB,
            'charset': 'utf8mb4'
        }
        # 使用ChromiumPage替代WebPage
        self.page = ChromiumPage()
        self.max_items = 15000
        self.items_collected = 0
        
    def _convert_to_float(self, value):
        """将字符串转换为浮点数"""
        try:
            if not value or value == '--':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
            
    def _is_valid_date(self, date_str):
        """验证日期格式是否有效"""
        try:
            if not date_str or len(date_str) < 8:
                return False
            # 尝试解析日期
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
            
    def crawl_funds(self):
        try:
            # 设置超时时间，避免任务执行时间过长
            start_time = time.time()
            max_execution_time = 180  # 最大执行时间180秒
            
            url = 'https://fund.eastmoney.com/fund.html#os_0;isall_0;ft_;pt_1'
            self.page.get(url)
            
            # 简单等待页面加载
            time.sleep(2)
            
            funds_data = []
            
            # 循环翻页直到收集足够数据或超时
            max_pages = 80  # 设置最大翻页次数
            current_page = 1
            
            while current_page <= max_pages and self.items_collected < self.max_items:
                if time.time() - start_time > max_execution_time:
                    logging.warning(f"爬取任务执行时间过长，提前结束，当前页数: {current_page}")
                    break
                
                logging.info(f"正在爬取第 {current_page} 页数据")
                
                # 开启接口监听
                self.page.listen.start('/Data/Fund_JJJZ_Data.aspx')
                
                # 点击下一页按钮获取数据
                next_btn = self.page.ele('text:下一页')
                if not next_btn:
                    logging.warning("未找到'下一页'按钮，停止翻页")
                    break
                    
                next_btn.click()
                time.sleep(1)  # 等待数据返回
                
                # 获取接口返回的数据
                response_count = 0
                for item in self.page.listen.steps(1):  # 每页只获取一个响应
                    response_count += 1
                    response = item.response.body
                    logging.info(f"获取到响应数据长度: {len(response) if response else 0}")
                    
                    # 使用正则提取所有基金数据
                    obj = re.compile(r'\["(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)",.*?"(.*?)".*?\]', re.S)
                    results = obj.findall(response)
                    
                    logging.info(f"第 {current_page} 页提取到基金数据数量: {len(results)}")
                    
                    # 如果没有数据，尝试下一页
                    if not results:
                        logging.warning(f"第 {current_page} 页未能提取到基金数据")
                        continue
                    
                    # 处理数据
                    for i, fund in enumerate(results):
                        if self.items_collected >= self.max_items:
                            break
                        
                        # 检查数据长度是否足够
                        if len(fund) < 23:
                            logging.warning(f"基金数据格式不完整，跳过: 索引 {i}, 长度 {len(fund)}")
                            continue
                            
                        try:
                            fund_data = {
                                'fund_code': fund[0],
                                'fund_name': fund[1],
                                'latest_net_value': self._convert_to_float(fund[3]),
                                'latest_total_value': self._convert_to_float(fund[4]),
                                'history_net_value': self._convert_to_float(fund[5]),
                                'history_total_value': self._convert_to_float(fund[6]),
                                'daily_growth_value': self._convert_to_float(fund[7]),
                                'daily_growth_rate': self._convert_to_float(fund[8]),
                                'latest_date': datetime.now().strftime('%Y-%m-%d'),  # 默认使用当前日期
                                'history_date': datetime.now().strftime('%Y-%m-%d')  # 默认使用当前日期
                            }
                            
                            # 安全地获取日期字段
                            if len(fund) > 21 and self._is_valid_date(fund[21]):
                                fund_data['latest_date'] = fund[21]
                            if len(fund) > 22 and self._is_valid_date(fund[22]):
                                fund_data['history_date'] = fund[22]
                                
                            funds_data.append(fund_data)
                            self.items_collected += 1
                            
                            # 记录爬取进度
                            if self.items_collected % 100 == 0:
                                logging.info(f"已收集 {self.items_collected} 条数据")
                                
                        except Exception as e:
                            logging.error(f"处理基金数据时出错: {str(e)}")
                            continue
                
                # 停止当前页的监听
                self.page.listen.stop()
                
                if response_count == 0:
                    logging.warning(f"第 {current_page} 页未获取到响应数据")
                
                current_page += 1
                time.sleep(1)  # 页面间隔
            
            if not funds_data:
                logging.error("未获取到任何基金数据")
            else:
                logging.info(f"成功获取 {len(funds_data)} 条基金数据")
            
            return funds_data
            
        except Exception as e:
            logging.error(f"爬取过程出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return []
        finally:
            self.items_collected = 0
            try:
                if hasattr(self.page, 'listen'):
                    self.page.listen.stop()
            except:
                pass
            self.page.quit()

    def save_to_db(self, funds_data):
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            sql = """INSERT INTO funds (fund_code, fund_name, latest_net_value, latest_total_value,
                    history_net_value, history_total_value, daily_growth_value, daily_growth_rate,
                    latest_date, history_date)
                    VALUES (%(fund_code)s, %(fund_name)s, %(latest_net_value)s, %(latest_total_value)s,
                    %(history_net_value)s, %(history_total_value)s, %(daily_growth_value)s, 
                    %(daily_growth_rate)s, %(latest_date)s, %(history_date)s)
                    ON DUPLICATE KEY UPDATE
                    fund_name=VALUES(fund_name),
                    latest_net_value=VALUES(latest_net_value),
                    latest_total_value=VALUES(latest_total_value),
                    history_net_value=VALUES(history_net_value),
                    history_total_value=VALUES(history_total_value),
                    daily_growth_value=VALUES(daily_growth_value),
                    daily_growth_rate=VALUES(daily_growth_rate),
                    latest_date=VALUES(latest_date),
                    history_date=VALUES(history_date)"""
                    
            cursor.executemany(sql, funds_data)
            conn.commit()
            
        except Exception as e:
            logging.error(f"保存数据失败: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()