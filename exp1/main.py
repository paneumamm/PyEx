"""运行实验一的确定性配送模拟。"""

import csv
import json
from pathlib import Path

from game_core import Order, Rider


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "orders_sample.csv"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "output" / "exp1" / "rider_stats.json"


def print_answer(answers):
    """answers 是一个字典，例如 {'Q1': 1234, 'Q2': 0.5678}"""
    print("===ANSWER===")
    for key in sorted(answers, key=lambda k: int(k[1:])):
        value = answers[key]
        if isinstance(value, float):
            value = round(value, 4)
        print(f"{key}={value}")
    print("===END===")


def actual_minutes(order):
    """计算确定性模拟所用的实际配送时长。"""
    return round(18 + order.distance_km * 5 + order.item_count * 2.5, 1)


def load_orders(path=DEFAULT_DATA_FILE):
    """读取样例 CSV，返回 Order 对象列表。"""
    orders = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            orders.append(
                Order(
                    row["order_id"],
                    row["shop_type"],
                    float(row["distance_km"]),
                    float(row["order_amount"]),
                    int(row["item_count"]),
                    int(row["promise_min"]),
                )
            )
    return orders


def _complete_all(riders):
    """按骑手顺序和接单顺序完成所有在手订单。"""
    for rider in riders:
        for order in list(rider.holding):
            rider.complete(order.order_id, actual_minutes(order))


def deliver_all(orders, riders=None):
    """轮流派单，每派满九单结算一次。"""
    if riders is None:
        riders = [Rider("R01"), Rider("R02"), Rider("R03")]

    for index, order in enumerate(orders):
        rider = riders[index % len(riders)]
        if not rider.take(order):
            raise RuntimeError(f"{rider.rider_id} cannot take {order.order_id}")
        if (index + 1) % 9 == 0:
            _complete_all(riders)

    _complete_all(riders)
    return riders


def build_answers(riders):
    """根据骑手的最终统计结果计算 Q1 至 Q5。"""
    total = sum(rider.stats["total"] for rider in riders)
    overtime = sum(rider.stats["overtime"] for rider in riders)
    overall_rate = round(overtime / total, 4) if total else 0.0
    highest = min(riders, key=lambda rider: (-rider.stats["rate"], rider.rider_id))
    return {
        "Q1": total,
        "Q2": overtime,
        "Q3": overall_rate,
        "Q4": highest.rider_id,
        "Q5": highest.stats["rate"],
    }


def save_stats(riders, path=DEFAULT_OUTPUT_FILE):
    """将骑手统计结果写入 UTF-8 编码的 JSON 文件。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = {rider.rider_id: rider.stats for rider in riders}
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    return result


def main():
    orders = load_orders()
    riders = deliver_all(orders)
    save_stats(riders)
    answers = build_answers(riders)
    print_answer(answers)
    return answers


if __name__ == "__main__":
    main()
