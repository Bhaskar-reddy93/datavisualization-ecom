import pandas as pd
import random

products = ["Laptop", "Mobile", "Headphones", "Keyboard", "Monitor"]
regions = ["North", "South", "East", "West"]

data = []

for i in range(2000):
    product = random.choice(products)
    region = random.choice(regions)
    price = random.randint(100, 2000)
    quantity = random.randint(1, 5)

    data.append({
        "Product": product,
        "Region": region,
        "Price": price,
        "Quantity": quantity,
        "Sales": price * quantity
    })

df = pd.DataFrame(data)

df.to_csv("sales_data.csv", index=False)

print("Dataset generated successfully!")