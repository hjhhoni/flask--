# 基金数据分析系统

## 项目简介

基金数据分析系统是一个基于Flask的Web应用，旨在提供基金数据的收集、分析和可视化功能。系统支持用户注册登录，查看基金列表，分析基金数据，并提供趋势预测功能，帮助投资者做出更明智的投资决策。

## 主要功能

1. **用户管理**
   - 用户注册与登录
   - 基于Token的身份验证

2. **基金数据管理**
   - 基金数据的添加、更新和删除
   - 基金列表展示与搜索

3. **数据分析与可视化**
   - 基金净值走势图
   - 收益率分析
   - 基金对比分析

4. **趋势预测**
   - 基于历史数据的趋势预测
   - AI算法辅助决策

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML, CSS, JavaScript, Bootstrap 5
- **数据库**: MySQL
- **数据可视化**: Chart.js

## 安装与部署

### 环境要求

- Python 3.7+
- MySQL 5.7+
- pip (Python包管理工具)

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/hjhhoni/fund-project.git
cd fund-project
```
2. **创建并激活虚拟环境**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置数据库**
创建MySQL数据库并修改 config.py 文件中的数据库连接信息：
```python
class Config:
    SECRET_KEY = 'your-secret-key'
    # 数据库配置
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your-password'
    MYSQL_DB = 'fund_db'
    MYSQL_PORT = 3306

```

5.**初始化数据库**
```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,
    token VARCHAR(36),
    created_at DATETIME NOT NULL,
    last_login DATETIME,
    INDEX (username),
    INDEX (email),
    INDEX (token)
);

CREATE TABLE IF NOT EXISTS funds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(10) NOT NULL UNIQUE,
    fund_name VARCHAR(100) NOT NULL,
    latest_net_value DECIMAL(10,4) NOT NULL,
    latest_total_value DECIMAL(10,4),
    daily_growth_value DECIMAL(10,4),
    daily_growth_rate DECIMAL(10,4),
    latest_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (fund_code)
);
```
6. **运行项目**
```bash
python run.py
```
应用将在 http://127.0.0.1:5000/ 运行。
