import os
import pandas as pd

def print_answer(answers):
    """answers 是一个字典，例如 {'Q1': 1234, 'Q2': 0.5678}"""
    print("===ANSWER===")
    for key in sorted(answers, key=lambda k: int(k[1:])):
        value = answers[key]
        if isinstance(value, float):
            value = round(value, 4)
        print(f"{key}={value}")
    print("===END===")


def check(df):
    print("原始数据", df.shape)
    print("重复数据", df.duplicated().sum())
    print("斜杠格式的时间", df["order_time"].str.contains("/").sum())
    print("带空格的商家类别", df["shop_type"].str.contains(" ").sum())
    print("距离大于50", (df["distance_km"] > 50).sum())
    print("金额小于0", (df["order_amount"] < 0).sum())
    print("时长大于300", (df["actual_min"] > 300).sum())
    print("气温缺失", df["temperature"].isna().sum())
    print("天气缺失", df["weather"].isna().sum())

#删除重复行
def step1(df):
    df = df.drop_duplicates(keep="first")
    print("步骤1 去重：剩", len(df), "行，重复的还剩", df.duplicated().sum())
    return df

#把两种格式统一转化成时间类型
def step2(df):
   fmt1, fmt2 = "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"
   t1 = pd.to_datetime(df["order_time"], format=fmt1, errors="coerce")
   t2 = pd.to_datetime(df["order_time"], format=fmt2, errors="coerce")
   df["order_time"] = t1.fillna(t2)
   print("步骤2 解析时间：剩", len(df), "行，没解析出来的还剩", df["order_time"].isna().sum())
   return df

#去掉首尾空格
def step3(df):
    df["shop_type"] = df["shop_type"].str.strip()
    print("步骤3 去空格：剩", len(df), "行，带空格的还剩", df["shop_type"].str.contains(" ").sum())
    return df

#大于 50 的是米，除以 1000，保留 2 位小数
def step4(df):
    big = df["distance_km"] > 50
    df.loc[big, "distance_km"] = (df.loc[big, "distance_km"] / 1000).round(2)
    print("步骤4 改单位：剩", len(df), "行，大于50的还剩", (df["distance_km"] > 50).sum())
    return df

#小于 0 的是退款单，删除整行
def step5(df):
    df = df[df["order_amount"] > 0]
    print("步骤5 删退款单：剩", len(df), "行，负金额还剩", (df["order_amount"] < 0).sum())

    return df

#大于 300 的是系统故障，删除整行
def step6(df):
    df = df[df["actual_min"] <= 300]
    print("步骤6 删故障单：剩", len(df), "行，超过300的还剩", (df["actual_min"] > 300).sum())
    return df

#缺失值用「这一单所在月份」的中位数填
def step7(df):
    month = df["order_time"].dt.month
    df["temperature"] = df.groupby(month)["temperature"].transform(lambda s: s.fillna(s.median()))
    print("步骤7 填气温：剩", len(df), "行，气温缺失还剩", df["temperature"].isna().sum())
    return df

#缺失值用整列的众数填
def step8(df):
    df["weather"] = df["weather"].fillna(df["weather"].mode()[0])
    print("步骤8 填天气：剩", len(df), "行，天气缺失还剩", df["weather"].isna().sum())
    return df

def answer(df):
    pass

def main():
    order_raw = pd.read_csv("../data/orders_raw.csv")
    check(order_raw)

    order_raw = step1(order_raw)
    order_raw = step2(order_raw)
    order_raw = step3(order_raw)
    order_raw = step4(order_raw)
    order_raw = step5(order_raw)
    order_raw = step6(order_raw)
    order_raw = step7(order_raw)
    order_raw = step8(order_raw)

    os.makedirs("output/exp3", exist_ok=True)

    order_raw.to_csv("../output/exp3/orders_clean.csv", index=False)

    #print_answer(answer(order_raw))

if __name__ == "__main__":
    main()