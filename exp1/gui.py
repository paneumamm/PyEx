"""校园外卖派单游戏的 tkinter 图形界面。"""

import json
import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from game_core import Rider
from main import DEFAULT_DATA_FILE, PROJECT_ROOT, actual_minutes, load_orders


GAME_SECONDS = 180
ORDER_INTERVAL_MS = 3000
BEST_SCORE_FILE = PROJECT_ROOT / "output" / "exp1" / "best_score.json"

WEATHER_FACTORS = {"晴": 0.92, "阴": 1.00, "大雨": 1.08}
RIDER_FACTORS = {"R01": 0.94, "R02": 1.00, "R03": 1.06}
RIDER_LEVELS = {"R01": "老手", "R02": "熟练", "R03": "新手"}


class DispatchGame:
    """使用 game_core.py 中的规则实现交互式派单。"""

    def __init__(self, root):
        self.root = root
        self.root.title("校园外卖骑手模拟器")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)

        self.all_orders = load_orders(DEFAULT_DATA_FILE)
        self.pending_source = []
        self.waiting_orders = []
        self.riders = []
        self.assigned_at = {}
        self.weather = "阴"
        self.remaining_seconds = GAME_SECONDS
        self.running = False
        self.game_id = 0
        self.best_score = self._load_best_score()

        self._configure_style()
        self.build_ui()
        self.new_game()

    def _configure_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 22, "bold"))
        style.configure("Metric.TLabel", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Treeview", rowheight=28, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 11, "bold"))

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(18, 14, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text="校园外卖骑手模拟器", style="Title.TLabel").pack(side="left")

        metrics = ttk.Frame(header)
        metrics.pack(side="right")
        self.timer_var = tk.StringVar()
        self.weather_var = tk.StringVar()
        self.rate_var = tk.StringVar()
        self.score_var = tk.StringVar()
        for variable in (
            self.timer_var,
            self.weather_var,
            self.rate_var,
            self.score_var,
        ):
            ttk.Label(metrics, textvariable=variable, style="Metric.TLabel", padding=(10, 0)).pack(side="left")

        content = ttk.Panedwindow(self.root, orient="horizontal")
        content.pack(fill="both", expand=True, padx=18, pady=8)

        left = ttk.Labelframe(content, text="待派订单", padding=10)
        right = ttk.Frame(content)
        content.add(left, weight=3)
        content.add(right, weight=4)

        order_columns = ("id", "shop", "distance", "items", "promise")
        self.order_tree = ttk.Treeview(left, columns=order_columns, show="headings", selectmode="browse")
        order_headings = {
            "id": ("订单号", 105),
            "shop": ("商家类别", 85),
            "distance": ("距离/km", 72),
            "items": ("菜品数", 62),
            "promise": ("承诺/min", 75),
        }
        for name, (title, width) in order_headings.items():
            self.order_tree.heading(name, text=title)
            self.order_tree.column(name, width=width, anchor="center")
        order_scroll = ttk.Scrollbar(left, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scroll.set)
        self.order_tree.pack(side="left", fill="both", expand=True)
        order_scroll.pack(side="right", fill="y")

        rider_frame = ttk.Labelframe(right, text="骑手状态", padding=10)
        rider_frame.pack(fill="x")
        rider_columns = ("id", "level", "load", "done", "overtime", "rate")
        self.rider_tree = ttk.Treeview(rider_frame, columns=rider_columns, show="headings", height=4, selectmode="browse")
        rider_headings = {
            "id": ("骑手", 64),
            "level": ("等级", 64),
            "load": ("在手", 54),
            "done": ("完成", 54),
            "overtime": ("超时", 54),
            "rate": ("超时率", 76),
        }
        for name, (title, width) in rider_headings.items():
            self.rider_tree.heading(name, text=title)
            self.rider_tree.column(name, width=width, anchor="center")
        self.rider_tree.pack(fill="x")
        self.rider_tree.bind("<<TreeviewSelect>>", lambda _event: self.refresh_holding())

        holding_frame = ttk.Labelframe(right, text="所选骑手的在手订单", padding=10)
        holding_frame.pack(fill="both", expand=True, pady=(10, 0))
        holding_columns = ("id", "shop", "promise", "held")
        self.holding_tree = ttk.Treeview(holding_frame, columns=holding_columns, show="headings", selectmode="browse")
        holding_headings = {
            "id": ("订单号", 120),
            "shop": ("商家类别", 95),
            "promise": ("承诺/min", 80),
            "held": ("在手/s", 75),
        }
        for name, (title, width) in holding_headings.items():
            self.holding_tree.heading(name, text=title)
            self.holding_tree.column(name, width=width, anchor="center")
        self.holding_tree.pack(fill="both", expand=True)

        controls = ttk.Frame(self.root, padding=(18, 8, 18, 8))
        controls.pack(fill="x")
        ttk.Button(controls, text="派单", style="Accent.TButton", command=self.on_assign).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="送达", style="Accent.TButton", command=self.on_deliver).pack(side="left", padx=8)
        ttk.Button(controls, text="新游戏", command=self.new_game).pack(side="left", padx=8)
        ttk.Button(controls, text="全部结算", command=self.finish_game).pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="准备就绪")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding=(10, 5)).pack(fill="x", side="bottom")

    def new_game(self):
        self.game_id += 1
        game_id = self.game_id
        self.pending_source = [
            type(order)(
                order.order_id,
                order.shop_type,
                order.distance_km,
                order.amount,
                order.item_count,
                order.promise_min,
            )
            for order in self.all_orders
        ]
        random.shuffle(self.pending_source)
        self.waiting_orders = []
        self.riders = [Rider("R01"), Rider("R02"), Rider("R03")]
        self.assigned_at = {}
        self.remaining_seconds = GAME_SECONDS
        self.weather = random.choice(list(WEATHER_FACTORS))
        self.running = True
        self._add_next_order()
        self.refresh_all()
        self.status_var.set("新一局开始：订单将每 3 秒进入待派列表")
        self.root.after(1000, lambda: self.tick(game_id))
        self.root.after(ORDER_INTERVAL_MS, lambda: self._order_tick(game_id))

    def _order_tick(self, game_id):
        if not self.running or game_id != self.game_id:
            return
        self._add_next_order()
        self.refresh_orders()
        self.root.after(ORDER_INTERVAL_MS, lambda: self._order_tick(game_id))

    def _add_next_order(self):
        if self.pending_source:
            self.waiting_orders.append(self.pending_source.pop(0))

    def tick(self, game_id):
        if not self.running or game_id != self.game_id:
            return
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.finish_game()
            return
        if self.remaining_seconds % 20 == 0:
            self.weather = random.choice(list(WEATHER_FACTORS))
            self.status_var.set(f"天气变为{self.weather}，配送时间系数已更新")
        self.refresh_metrics()
        self.refresh_holding()
        self.root.after(1000, lambda: self.tick(game_id))

    def on_assign(self):
        order_selection = self.order_tree.selection()
        rider_selection = self.rider_tree.selection()
        if not order_selection or not rider_selection:
            messagebox.showinfo("请选择", "请同时选择一条待派订单和一名骑手。")
            return

        order_id = order_selection[0]
        rider_id = rider_selection[0]
        order = next(order for order in self.waiting_orders if order.order_id == order_id)
        rider = self._rider(rider_id)
        if not rider.take(order):
            messagebox.showwarning("派单失败", f"{rider_id} 已带满 {Rider.MAX_LOAD} 单。")
            return

        self.waiting_orders.remove(order)
        self.assigned_at[order.order_id] = time.monotonic()
        self.status_var.set(f"已将 {order.order_id} 派给 {rider_id}")
        self.refresh_all(select_rider=rider_id)

    def on_deliver(self):
        rider_selection = self.rider_tree.selection()
        order_selection = self.holding_tree.selection()
        if not rider_selection or not order_selection:
            messagebox.showinfo("请选择", "请先选择骑手，再选择该骑手的一条在手订单。")
            return

        rider = self._rider(rider_selection[0])
        order_id = order_selection[0]
        order = next(order for order in rider.holding if order.order_id == order_id)
        held_seconds = max(0, time.monotonic() - self.assigned_at.get(order_id, time.monotonic()))
        minutes = self._game_actual_minutes(order, rider.rider_id, held_seconds)
        overtime = rider.complete(order_id, minutes)
        self.assigned_at.pop(order_id, None)
        result = "超时" if overtime else "准时"
        self.status_var.set(f"{order_id} 已送达：{minutes:.1f} 分钟，{result}")
        self.refresh_all(select_rider=rider.rider_id)

    def _game_actual_minutes(self, order, rider_id, held_seconds):
        base = actual_minutes(order)
        adjusted = base * WEATHER_FACTORS[self.weather] * RIDER_FACTORS[rider_id]
        return round(adjusted + held_seconds * 0.15, 1)

    def finish_game(self):
        if not self.running:
            return
        self.running = False
        score = self.current_score()
        if score > self.best_score:
            self.best_score = score
            self._save_best_score(score)
        self.refresh_all()
        summary = (
            f"本局得分：{score}\n"
            f"完成订单：{sum(r.stats['total'] for r in self.riders)}\n"
            f"超时订单：{sum(r.stats['overtime'] for r in self.riders)}\n"
            f"历史最佳：{self.best_score}"
        )
        messagebox.showinfo("本局结算", summary)
        self.status_var.set("本局已结算，可点击“新游戏”重新开始")

    def current_score(self):
        completed = sum(rider.stats["total"] for rider in self.riders)
        overtime = sum(rider.stats["overtime"] for rider in self.riders)
        return max(0, completed * 100 - overtime * 40)

    def refresh_all(self, select_rider=None):
        self.refresh_orders()
        self.refresh_riders(select_rider)
        self.refresh_holding()
        self.refresh_metrics()

    def refresh_orders(self):
        self.order_tree.delete(*self.order_tree.get_children())
        for order in self.waiting_orders:
            self.order_tree.insert(
                "",
                "end",
                iid=order.order_id,
                values=(
                    order.order_id,
                    order.shop_type,
                    f"{order.distance_km:.2f}",
                    order.item_count,
                    order.promise_min,
                ),
            )

    def refresh_riders(self, select_rider=None):
        previous = select_rider
        if previous is None and self.rider_tree.selection():
            previous = self.rider_tree.selection()[0]
        self.rider_tree.delete(*self.rider_tree.get_children())
        for rider in self.riders:
            stats = rider.stats
            self.rider_tree.insert(
                "",
                "end",
                iid=rider.rider_id,
                values=(
                    rider.rider_id,
                    RIDER_LEVELS[rider.rider_id],
                    f"{rider.load}/{Rider.MAX_LOAD}",
                    stats["total"],
                    stats["overtime"],
                    f"{stats['rate']:.2%}",
                ),
            )
        target = previous if previous in {r.rider_id for r in self.riders} else "R01"
        self.rider_tree.selection_set(target)
        self.rider_tree.focus(target)

    def refresh_holding(self):
        self.holding_tree.delete(*self.holding_tree.get_children())
        selection = self.rider_tree.selection()
        if not selection:
            return
        rider = self._rider(selection[0])
        now = time.monotonic()
        for order in rider.holding:
            held = int(max(0, now - self.assigned_at.get(order.order_id, now)))
            self.holding_tree.insert(
                "",
                "end",
                iid=order.order_id,
                values=(order.order_id, order.shop_type, order.promise_min, held),
            )

    def refresh_metrics(self):
        minutes, seconds = divmod(max(0, self.remaining_seconds), 60)
        completed = sum(rider.stats["total"] for rider in self.riders)
        overtime = sum(rider.stats["overtime"] for rider in self.riders)
        rate = overtime / completed if completed else 0
        self.timer_var.set(f"剩余 {minutes:02d}:{seconds:02d}")
        self.weather_var.set(f"天气 {self.weather}")
        self.rate_var.set(f"总超时率 {rate:.2%}")
        self.score_var.set(f"得分 {self.current_score()}  最佳 {self.best_score}")

    def _rider(self, rider_id):
        return next(rider for rider in self.riders if rider.rider_id == rider_id)

    def _load_best_score(self):
        try:
            with BEST_SCORE_FILE.open("r", encoding="utf-8") as file:
                return int(json.load(file).get("best_score", 0))
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def _save_best_score(self, score):
        BEST_SCORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with BEST_SCORE_FILE.open("w", encoding="utf-8") as file:
            json.dump({"best_score": score}, file, ensure_ascii=False, indent=2)


def main():
    root = tk.Tk()
    DispatchGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
