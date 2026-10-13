import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sympy.printing.pretty.pretty_symbology import line_width


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
    os.makedirs("../output/exp2", exist_ok=True)
    fig.tight_layout()
    fig.savefig(f"../output/exp2/{name}",dpi=120)
    plt.close(fig)


def draw_fig1(df):
    rate = df.groupby("weather")["is_overtime"].mean() * 100
    index = ["晴", "多云", "阴", "小雨", "大雨"]
    rate = rate.reindex(index)

    fig, ax = plt.subplots(figsize=(7,4.5))
    ax.bar(rate.index, rate, color="#4A87B8", width=0.6)

    ax.set_title("各种天气下超时率对比")
    ax.set_xlabel("天气")
    ax.set_ylabel("超时率(%)")
    ax.grid(axis="y")

    for i, v in enumerate(rate):
        ax.text(i, v+1, "%.1f" % v, ha="center", va="bottom",fontsize=9)

    save(fig, "fig1.png")


def draw_fig2(df):
    rate = df.groupby(df["order_time"].dt.hour)["is_overtime"].mean() * 100
    index = rate.index

    fig, ax = plt.subplots(figsize=(7,4.5))
    ax.plot(rate.index, rate.values, color="#4A87B8", linewidth=2, linestyle="--", marker="o")
    ax.set_title("按下单小时统计的超时率变化")
    ax.set_xlabel("下单小时(h)")
    ax.set_ylabel("超时率(%)")
    ax.grid(axis="y")

    for i, v in enumerate(rate):
        ax.text(i+index[0], v+0.8, "%.1f" % v, ha="center", va="bottom",fontsize=9)

    save(fig, "fig2.png")


def draw_fig3(df):
    x = df["distance_km"]
    y = df["actual_min"]

    fig, ax = plt.subplots(figsize=(7,4.5))

    ax.scatter(x, y , s=4, alpha=0.4 ,color="#4A87B8")

    save(fig, "fig3.png")


def draw_fig4(df):
    cnt = df["shop_type"].value_counts()

    fig, ax = plt.subplots(figsize=(6,6))

    ax.pie(cnt.values, labels=cnt.index, autopct="%1.1f%%", shadow=False, startangle=90)
    ax.set_title("五类商家的订单量占比")

    save(fig, "fig4.png")



def draw_fig5(df):
    types = sorted(df["shop_type"].unique())

    data = [df[df["shop_type"] == t]["actual_min"]
            for t in types]

    fig, ax = plt.subplots(figsize=(7,4.5))

    ax.boxplot(data)
    ax.set_title("不同商家类别的实际送达时长分布")
    ax.set_xticklabels(types)
    ax.set_ylabel("实际送达时间(分钟)")

    save(fig, "fig5.png")


def answers(df):
    pass


def main():
    use_chinese_font()
    orders = pd.read_csv("../data/orders.csv", encoding="utf-8-sig")
    orders["order_time"] = pd.to_datetime(orders["order_time"]) #转化为pandas能识别的，便于后续分段提取
    draw_fig1(orders)
    draw_fig2(orders)
    draw_fig3(orders)
    draw_fig4(orders)
    draw_fig5(orders)

    #print_answer(answers(orders))

if __name__ == "__main__":
    main()









