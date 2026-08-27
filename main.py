import csv
import os
import tkinter as tk
from tkinter import filedialog
import mysql.connector
from mysql.connector import Error

def select_csv_file():
    """Opens a window to prompt the user for the CSV file."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Airbnb CSV File",
        filetypes=[("CSV files", "*.csv")]
    )
    root.destroy()
    return file_path

def connect_to_mysql():
    """Connects to the assignment database."""
import csv
import os
import tkinter as tk
from tkinter import filedialog
import mysql.connector
from mysql.connector import Error

def select_csv_file():
    """Opens a window to prompt the user for the CSV file."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Airbnb CSV File",
        filetypes=[("CSV files", "*.csv")]
    )
    root.destroy()
    return file_path

def connect_to_mysql():
    """Connects to the assignment database."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="airbnb_db"
    )

def import_csv_to_mysql(file_path):
    """Reads the CSV, cleans the data, and inserts it into MySQL."""
    if not file_path or not os.path.exists(file_path):
        print("Error: Invalid or no file selected.")
        return

    connection = None
    cursor = None
    imported_count = 0

    try:
        connection = connect_to_mysql()
        cursor = connection.cursor()

        insert_query = """
            INSERT IGNORE INTO airbnb_listings (
                id, name, host_id, host_identity_verified, host_name, 
                neighbourhood_group, neighbourhood, lat, `long`, country, 
                country_code, instant_bookable, cancellation_policy, room_type, 
                construction_year, price, service_fee, minimum_nights, 
                number_of_reviews, last_review, reviews_per_month, 
                review_rate_number, calculated_host_listings_count, 
                availability_365, house_rules
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            
            for row in reader:
                # Data Transformation: Clean the price and service fee columns
                raw_price = row.get("price", "0").replace("$", "").replace(",", "").strip()
                clean_price = float(raw_price) if raw_price else 0.00
                
                raw_fee = str(row.get("service_fee") or row.get("service fee") or "0").replace("$", "").replace(",", "").strip()
                clean_fee = float(raw_fee) if raw_fee else 0.00

                # Prepare the tuple for insertion (handle empty strings turning into None/NULL)
                validated_data = (
                    row["id"], 
                    row["NAME"], 
                    row["host id"], 
                    row["host_identity_verified"], 
                    row["host name"], 
                    row["neighbourhood group"], 
                    row["neighbourhood"], 
                    row["lat"] or None, 
                    row["long"] or None, 
                    row["country"], 
                    row["country code"], 
                    row["instant_bookable"], 
                    row["cancellation_policy"], 
                    row["room type"], 
                    row["Construction year"] or None, 
                    clean_price, 
                    clean_fee, 
                    row["minimum nights"] or None, 
                    row["number of reviews"] or None, 
                    row["last review"], 
                    row["reviews per month"] or None, 
                    row["review rate number"] or None, 
                    row["calculated host listings count"] or None, 
                    row["availability 365"] or None, 
                    row["house_rules"]
                )

                cursor.execute(insert_query, validated_data)
                imported_count += 1

        connection.commit()
        print(f"Import completed successfully. Processed {imported_count} rows.")

    except Error as e:
        if connection and connection.is_connected():
            connection.rollback()
        print("Database Import Failed:", e)

    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

if __name__ == "__main__":
    print("Initializing Airbnb Data Import...")
    path = select_csv_file()
    import_csv_to_mysql(path)


