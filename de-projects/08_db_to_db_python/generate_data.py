import csv
import random
from datetime import datetime, timedelta

# Define a function to generate a random date within a given range
def random_date(start, end):
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime('%Y-%m-%d')

# Define the headers of the CSV file
headers = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Customer Name",
    "Segment", "Country", "City", "State", "Postal Code", "Region", "Product ID", "Category",
    "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit"
]

# Sample data to use for generating the rows
ship_modes = ["Second Class", "Standard Class", "First Class", "Same Day"]
segments = ["Consumer", "Corporate", "Home Office"]
countries = ["United States"]
regions = ["South", "West", "Central", "East"]
categories = ["Furniture", "Office Supplies", "Technology"]
sub_categories = ["Bookcases", "Chairs", "Tables", "Phones", "Storage", "Appliances", "Paper"]
product_names = ["Product A", "Product B", "Product C", "Product D"]

# Function to generate a single row of random data
def generate_row(row_id):
    order_id = f"CA-2024-{random.randint(10000, 99999)}"
    order_date = random_date(datetime(2024, 1, 1), datetime(2024, 12, 31))
    ship_date = random_date(datetime.strptime(order_date, '%Y-%m-%d'), datetime(2025, 12, 31))
    ship_mode = random.choice(ship_modes)
    customer_id = f"CG-{random.randint(10000, 99999)}"
    customer_name = f"Customer {row_id}"
    segment = random.choice(segments)
    country = random.choice(countries)
    city = "City " + str(row_id)
    state = "State " + str(row_id)
    postal_code = random.randint(10000, 99999)
    region = random.choice(regions)
    category = random.choice(categories)
    sub_category = random.choice(sub_categories)
    product_name = random.choice(product_names)
    sales = round(random.uniform(10, 1000), 2)
    quantity = random.randint(1, 10)
    discount = round(random.uniform(0, 0.3), 2)
    profit = round(sales * quantity * (1 - discount), 2)
    
    return [
        row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name,
        segment, country, city, state, postal_code, region, f"{category[:3]}-PROD-{random.randint(1000000, 9999999)}",
        category, sub_category, product_name, sales, quantity, discount, profit
    ]

# Path to the CSV file
csv_file_path = './docker/source-data/sales_data.csv'

# Generate 3 million rows of data and write to the CSV file
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    
    for i in range(1, 3000001):  # 3 million rows
        row = generate_row(i)
        writer.writerow(row)
        # Print progress for every 100,000 rows
        if i % 100000 == 0:
            print(f"{i} rows generated")

print(f"CSV file generated: {csv_file_path}")