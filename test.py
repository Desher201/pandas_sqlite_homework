import sqlite3 as sql

import pandas as pd


connect = sql.connect("data/shop.sqlite")
df_1 = pd.read_sql("select * from products", connect)
df_2 = pd.read_sql("select * from sales", connect)

connection = sql.connect("output/shop_analysis.sqlite")
connection.execute("CREATE TABLE if not exists product_statistics (name TEXT, category TEXT, sold INTEGER, sum FLOAT)")

for i in range(1, len(df_1) + 1):
    df_product_statistics = pd.read_sql(f"SELECT * FROM sales WHERE product_id = ?", connect,params=(i,))
    df_quantity = df_product_statistics["quantity"].sum()
    df_product_info = pd.read_sql(f"SELECT * FROM products WHERE id = ?", connect,params=(i,))
    df_price = df_product_info["price"].iloc[0]
    df_category = df_product_info["category"].iloc[0]
    df_product_name = df_product_info["name"].iloc[0]
    df_price_final = df_price * df_quantity
    connection.execute(
        """
        INSERT INTO product_statistics (name, category, sold, sum)
        VALUES (?, ?, ?, ?)
        """,
        (df_product_name, df_category, int(df_quantity), float(df_price_final))
    )
connection.commit()



connection.execute("CREATE TABLE if not exists category_statistics(category TEXT, count_operations INTEGER,sales INTEGER, sum FLOAT, avg FLOAT) ")
category = set(pd.read_sql("select * from products", connect)["category"] )


df = pd.merge(df_1, df_2, left_on="id", right_on="product_id",suffixes=("_product", "_sale"))
# print(df)
df["total_sale"] = df["quantity"]*df["price"]
category_statistics = df.groupby("category").agg(
    count_operations = ("id_sale", "count"),
    sales = ("quantity", "sum"),
    suma = ("total_sale", "sum"),
    avg = ("total_sale", "mean"),
)
print(category_statistics)
connection.commit()

connection.execute("CREATE TABLE if not exists top_products(name TEXT, category TEXT, quantity_sold INTEGER, total_sales FLOAT)")
group = df.groupby("product_id").agg(
    quantity_sold=("quantity", "sum"),
    total_sales = ("product_id", "count"),
    category = ("category","first")
)
group.to_csv("output/top_products.csv")
group.sort_values(by="quantity_sold", ascending=False, inplace=True)
group = pd.merge(
    group,
    df_1[["id", "name"]],
    left_on="product_id",
    right_on="id"
)
group = group[["id", "name","category","quantity_sold","total_sales"]]
group = group.head(5)
print(group)
group.to_sql("top_products", connection, if_exists="replace", index=False)