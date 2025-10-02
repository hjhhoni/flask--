# 基金数据分析系统

## 项目简介

基金数据分析系统是一个基于Flask的Web应用，旨在提供基金数据的收集、分析和可视化功能。系统支持用户注册登录，查看基金列表，分析基金数据，并提供趋势预测功能，帮助投资者做出更明智的投资决策。

## 主要功能

1. **用户管理**
   - 用户注册与登录
   - 基于Token的身份验证
   - ![登陆界面](https://img.alicdn.com/bao/uploaded/i4/O1CN01bnNuUt1GEj7fOjECk_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)

2. **基金数据管理**
   - 基金数据的添加、更新和删除
   - 基金列表展示与搜索
   - ![数据管理](https://img.alicdn.com/bao/uploaded/i3/O1CN01PJXNG01GEjAS217ev_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)

3. **数据分析与可视化**
   - 基金净值走势图
   - 收益率分析
   - 基金对比分析
   - ![数据可视化](https://img.alicdn.com/bao/uploaded/i3/O1CN01GfvtrX1GEj7iglbm6_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)
   - ![数据可视化](https://img.alicdn.com/bao/uploaded/i4/O1CN01fidt0Z1GEj7gGyGrZ_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)

4. **趋势预测**
   - 基于历史数据的趋势预测
   - AI算法辅助决策
   - ![预测](https://img.alicdn.com/bao/uploaded/i3/O1CN01GfvtrX1GEj7iglbm6_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)
   - ![预测](https://img.alicdn.com/bao/uploaded/i4/O1CN01m5ha931GEj7gVnTvm_!!4611686018427383567-53-fleamarket.heic_Q90.jpg_.webp)

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML, CSS, JavaScript, Bootstrap 5
- **数据库**: MySQL80
- **数据可视化**: Chart.js

## 安装与部署

### 环境要求

- Python 3.8+（3.8.8）
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
CREATE DATABASE flask;
USE flask;

CREATE TABLE `users` (
    `id` int NOT NULL AUTO_INCREMENT,
    `username` varchar(50) NOT NULL,
    `email` varchar(100) NOT NULL,
    `password_hash` varchar(64) NOT NULL,
    `token` varchar(36) DEFAULT NULL,
    `created_at` datetime NOT NULL,
    `last_login` datetime DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `username` (`username`),
    UNIQUE KEY `email` (`email`),
    KEY `username_2` (`username`),
    KEY `email_2` (`email`),
    KEY `token` (`token`)
) ENGINE = InnoDB AUTO_INCREMENT = 2 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci

CREATE TABLE `funds` (
    `fund_code` varchar(10) NOT NULL,
    `fund_name` varchar(100) NOT NULL,
    `latest_net_value` decimal(10, 4) DEFAULT NULL,
    `latest_total_value` decimal(10, 4) DEFAULT NULL,
    `history_net_value` decimal(10, 4) DEFAULT NULL,
    `history_total_value` decimal(10, 4) DEFAULT NULL,
    `daily_growth_value` decimal(10, 4) DEFAULT NULL,
    `daily_growth_rate` decimal(10, 2) DEFAULT NULL,
    `latest_date` date DEFAULT NULL,
    `history_date` date DEFAULT NULL,
    `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`fund_code`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci
```
6. **运行项目**
```bash
python run.py
```
应用将在 http://127.0.0.1:5000/ 运行。
