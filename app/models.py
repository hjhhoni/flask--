class Fund:
    """基金模型类"""
    def __init__(self, code=None, name=None, net_value=None, growth_rate=None):
        self.code = code
        self.name = name
        self.net_value = net_value
        self.growth_rate = growth_rate

# 添加一个简单的查询函数，避免在routes.py中直接使用ORM
def query_all_funds():
    """模拟查询所有基金"""
    # 这里可以添加实际的数据库查询代码
    # 现在返回一些模拟数据
    return [
        Fund(code="000001", name="示例基金1", net_value=1.2345, growth_rate=1.23),
        Fund(code="000002", name="示例基金2", net_value=2.3456, growth_rate=-0.45),
        Fund(code="000003", name="示例基金3", net_value=3.4567, growth_rate=0.67)
    ]