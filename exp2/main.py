import pandas as pd
import matplotlib.pyplot as plt

order = pd.read_csv("../data/orders.csv")
order.describe()