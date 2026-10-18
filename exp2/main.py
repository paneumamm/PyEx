from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "orders.csv"
OUTPUT_DIR = PROJECT_ROOT / "output" / "exp2"


def use_chinese_font():
    """自动挑一个系统里装了的中文字体，返回字体名；找不到返回 None"""
    preferred = ["SimHei", "Microsoft YaHei", "PingFang SC", "Heiti SC",
                 "Songti SC", "Noto Sans CJK SC", "Source Han Sans SC",
                 "WenQuanYi Zen Hei", "Arial Unicode MS"]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    for name in sorted(installed):
        if any(k in name for k in ("CJK", "Han", "Hei", "Song", "YaHei")):
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    return None


def print_answer(answers):
    """answers 是一个字典，例如 {'Q1': 1234, 'Q2': 0.5678}"""
    print("===ANSWER===")
    for key in sorted(answers, key=lambda k: int(k[1:])):
        value = answers[key]
        if isinstance(value, float):
            value = round(value, 4)
        print(f"{key}={value}")
    print("===END===")


def save(fig, name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / name, dpi=120)
    plt.close(fig)


def draw_fig1(df):
    rate = df.groupby("weather")["is_overtime"].mean() * 100
    index = ["晴", "多云", "阴", "小雨", "大雨"]
    rate = rate.reindex(index)

    fig, ax = plt.subplots(figsize=(7,4.5))
    ax.bar(rate.index, rate.values, color="#4A87B8", width=0.6)

    ax.set_title("各种天气下超时率对比")
    ax.set_xlabel("天气")
    ax.set_ylabel("超时率(%)")
    ax.set_ylim(0, max(rate.max() * 1.15, 1))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    for i, v in enumerate(rate):
        ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)

    save(fig, "fig1.png")


def draw_fig2(df):
    rate = df.groupby(df["order_time"].dt.hour)["is_overtime"].mean() * 100
    fig, ax = plt.subplots(figsize=(7,4.5))
    ax.plot(rate.index, rate.values, color="#4A87B8", linewidth=2, marker="o")
    ax.set_title("按下单小时统计的超时率变化")
    ax.set_xlabel("下单小时(h)")
    ax.set_ylabel("超时率(%)")
    ax.set_xticks(rate.index)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    save(fig, "fig2.png")


def draw_fig3(df):
    x = df["distance_km"]
    y = df["actual_min"]

    fig, ax = plt.subplots(figsize=(7,4.5))

    ax.scatter(x, y, s=7, alpha=0.35, color="#4A87B8", edgecolors="none")
    ax.set_title("配送距离与实际送达时长的关系")
    ax.set_xlabel("配送距离（公里）")
    ax.set_ylabel("实际送达时长（分钟）")
    ax.grid(alpha=0.2)

    save(fig, "fig3.png")


def draw_fig4(df):
    cnt = df["shop_type"].value_counts()

    fig, ax = plt.subplots(figsize=(6,6))

    ax.pie(cnt.values, labels=cnt.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("五类商家的订单量占比")
    ax.set_aspect("equal")

    save(fig, "fig4.png")



def draw_fig5(df):
    types = sorted(df["shop_type"].unique())

    data = [df[df["shop_type"] == t]["actual_min"]
            for t in types]

    fig, ax = plt.subplots(figsize=(7,4.5))

    ax.boxplot(data)
    ax.set_xticks(range(1, len(types) + 1))
    ax.set_xticklabels(types)
    ax.set_title("不同商家类别的实际送达时长分布")
    ax.set_xlabel("商家类别")
    ax.set_ylabel("实际送达时间(分钟)")

    save(fig, "fig5.png")


def draw_anomaly_rider(df):
    """比较各骑手的超时率，找出明显偏离整体的骑手。"""
    summary = df.groupby("rider_id")["is_overtime"].agg(["sum", "size", "mean"])
    summary = summary.sort_values("mean", ascending=False)
    outlier_id = summary.index[0]
    rates = summary["mean"] * 100
    colors = ["#C44E52" if rider == outlier_id else "#4A87B8"
              for rider in rates.index]

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(rates.index, rates.values, color=colors)
    other_rate = df.loc[df["rider_id"] != outlier_id, "is_overtime"].mean() * 100
    ax.axhline(other_rate, color="#555555", linestyle="--", linewidth=1,
               label=f"其他骑手合计：{other_rate:.1f}%")
    ax.set_title(f"骑手超时率对比：{outlier_id} 显著偏高")
    ax.set_xlabel("骑手编号")
    ax.set_ylabel("超时率（%）")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    ax.legend()
    outlier = summary.loc[outlier_id]
    ax.annotate(f"{int(outlier['sum'])}/{int(outlier['size'])} 单超时",
                xy=(0, rates.iloc[0]), xytext=(8, 6), textcoords="offset points")
    save(fig, "anomaly_rider.png")


def draw_anomaly_daily_weather(df):
    """在对齐的时间轴上展示每日超时率和当天天气。"""
    dates = df["order_time"].dt.date
    daily = df.groupby(dates)["is_overtime"].agg(["sum", "size", "mean"])
    daily_weather = df.groupby(dates)["weather"].first()
    weather_order = ["晴", "多云", "阴", "小雨", "大雨"]
    weather_position = {weather: index for index, weather in enumerate(weather_order)}
    weather_colors = {
        "晴": "#E6AF2E", "多云": "#8297A6", "阴": "#536878",
        "小雨": "#5CA4A9", "大雨": "#345995",
    }
    peak_date = daily["mean"].idxmax()
    peak_rate = daily.loc[peak_date, "mean"] * 100

    fig, (ax_rate, ax_weather) = plt.subplots(
        2, 1, figsize=(11, 6), sharex=True,
        gridspec_kw={"height_ratios": [4, 1]},
    )
    ax_rate.plot(daily.index, daily["mean"] * 100, color="#4A87B8", linewidth=1.5)
    ax_rate.scatter([peak_date], [peak_rate], color="#C44E52", s=70, zorder=3)
    ax_rate.annotate(f"{peak_date:%m-%d}：{peak_rate:.1f}%（晴）",
                     xy=(peak_date, peak_rate), xytext=(-115, -29),
                     textcoords="offset points", color="#9F3035",
                     arrowprops={"arrowstyle": "->", "color": "#9F3035"})
    ax_rate.set_title("每日超时率与当天天气")
    ax_rate.set_ylabel("超时率（%）")
    ax_rate.set_ylim(0, 100)
    ax_rate.grid(alpha=0.2)

    ax_weather.scatter(
        daily_weather.index,
        [weather_position[weather] for weather in daily_weather],
        c=[weather_colors[weather] for weather in daily_weather],
        marker="s", s=35,
    )
    ax_weather.set_yticks(range(len(weather_order)))
    ax_weather.set_yticklabels(weather_order)
    ax_weather.set_ylabel("天气")
    ax_weather.set_xlabel("日期")
    ax_weather.set_ylim(-0.5, len(weather_order) - 0.5)
    ax_weather.grid(axis="x", alpha=0.2)
    save(fig, "anomaly_daily_weather.png")


def answers(df):
    q1 = len(df)
    q2 = round(df["is_overtime"].mean(), 4)
    over_time = df.groupby("weather")["is_overtime"].mean()
    q3 = round((over_time["大雨"] - over_time["晴"]) * 100, 2)
    q4 = df.groupby("shop_type")["actual_min"].mean().idxmax()
    q5 = df.groupby("rider_id")["is_overtime"].mean().idxmax()
    daily_rate = df.groupby(df["order_time"].dt.date)["is_overtime"].mean()
    q6 = daily_rate.idxmax().isoformat()
    return {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5, "Q6": q6}


def main():
    use_chinese_font()
    orders = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    orders["order_time"] = pd.to_datetime(orders["order_time"])
    draw_fig1(orders)
    draw_fig2(orders)
    draw_fig3(orders)
    draw_fig4(orders)
    draw_fig5(orders)
    draw_anomaly_rider(orders)
    draw_anomaly_daily_weather(orders)

    print_answer(answers(orders))

if __name__ == "__main__":
    main()
