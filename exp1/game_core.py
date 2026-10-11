"""Core domain objects for the campus delivery simulator.

This module deliberately contains no file or GUI code.  Both ``main.py`` and
``gui.py`` use the same rules defined here.
"""


class Order:
    """A delivery order and its current delivery state."""

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
    """A rider who can carry at most three orders at the same time."""

    MAX_LOAD = 3

    def __init__(self, rider_id):
        self.rider_id = rider_id
        self.completed_count = 0
        self.overtime_count = 0
        self.holding = []

    def take(self, order):
        """Take an order, returning ``False`` without side effects if full."""
        if self.load >= Rider.MAX_LOAD:
            return False

        order.status = "delivering"
        self.holding.append(order)
        return True

    def complete(self, order_id, actual_min):
        """Complete a held order and return whether it was overtime.

        ``None`` is returned when the requested order is not currently held.
        An order taking exactly its promised time is considered on time.
        """
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
        """Return the number of orders currently being delivered."""
        return len(self.holding)

    @property
    def stats(self):
        """Return completed-order statistics with a four-decimal rate."""
        rate = 0.0
        if self.completed_count:
            rate = round(self.overtime_count / self.completed_count, 4)
        return {
            "total": self.completed_count,
            "overtime": self.overtime_count,
            "rate": rate,
        }
