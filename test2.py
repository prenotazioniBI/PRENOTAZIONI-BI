import pandas as pd


df = pd.read_parquet("soggetti.parquet")


print(df.head(100))


