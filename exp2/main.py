import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

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

def save(fig, name):
    os.makedirs("../output/exp2", exist_ok=True)
    fig.tight_layout()
    fig.savefig(f"../output/exp2/fig{name}.png",dpi=120)
    plt.close(fig)

def draw_fig1(df):
    pass

def draw_fig2(df):
    pass

def draw_fig3(df):
    pass

def draw_fig4(df):
    pass

def draw_fig5(df):
    pass

def answers(df):
    pass

def main():
    use_chinese_font()
    orders = pd.read_csv("../data/orders.csv", encoding="utf-8-sig")
    draw_fig1(orders)
    draw_fig2(orders)
    draw_fig3(orders)
    draw_fig4(orders)
    draw_fig5(orders)

if __name__ == "__main__":
    main()









