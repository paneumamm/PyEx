"""校园外卖骑手模拟器的核心对象。

本模块不处理文件或图形界面；main.py 和 gui.py 共用这里的规则。
"""


class Order:
    """外卖订单及其当前配送状态。"""

    def __init__(
        self,
        order_id,
        shop_type,
        distance_km,
        amount,
        item_count,
        promise_min,
    ):
        self.order_id = order_id
        self.shop_type = shop_type
        self.distance_km = distance_km
        self.amount = amount
        self.item_count = item_count
        self.promise_min = promise_min
        self.status = "waiting"
        self.actual_min = None


class Rider:
    """骑手，同一时间最多携带三单。"""

    MAX_LOAD = 3                      # 同时最多带 3 单，类属性

    def __init__(self, rider_id):
        self.rider_id = rider_id
        self.completed_count = 0
        self.overtime_count = 0
        self.holding = []

    def take(self, order):
        """接单。成功返回 True 并把订单状态改为 'delivering'；
           在手单数已达 MAX_LOAD 时返回 False，且不改变任何状态。"""
        if self.load >= Rider.MAX_LOAD:
            return False

        order.status = "delivering"
        self.holding.append(order)
        return True

    def complete(self, order_id, actual_min):
        """完成订单。把订单状态改为 'done'，记录 actual_min，
           从在手列表移除，并更新统计。
           返回 True 表示这一单超时了，False 表示准时。
           如果 order_id 不在在手列表里，返回 None。"""
        order = next(
            (item for item in self.holding if item.order_id == order_id), None
        )
        if order is None:
            return None

        order.actual_min = actual_min
        order.status = "done"
        self.holding.remove(order)

        is_overtime = actual_min > order.promise_min
        self.completed_count += 1
        if is_overtime:
            self.overtime_count += 1
        return is_overtime

    @property
    def load(self):
        """当前在手订单数量"""
        return len(self.holding)

    @property
    def stats(self):
        """返回统计字典，键固定为这三个：
           {"total": 已完成单数, "overtime": 超时单数, "rate": 超时率}
           rate 保留 4 位小数；一单都没完成时 rate 为 0.0"""
        rate = 0.0
        if self.completed_count:
            rate = round(self.overtime_count / self.completed_count, 4)
        return {
            "total": self.completed_count,
            "overtime": self.overtime_count,
            "rate": rate,
        }
