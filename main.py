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

        with open(path, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            # Clean leading/trailing spaces from all CSV headers automatically
            reader.fieldnames = [
                f.strip() for f in reader.fieldnames if f is not None
            ]

            for row in reader:
                # Skip empty or broken rows at the end of the file
                if not row or not any(row.values()):
                    continue

                # Safely clean keys in the current row
                row_clean = {
                    k.strip(): v for k, v in row.items() if k is not None
                }

                # Data Transformation: Clean price and fee
                raw_price = (
                    row_clean.get("price", "0")
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
                clean_price = float(raw_price) if raw_price else 0.00

                raw_fee = (
                    row_clean.get("service_fee", "0")
                    .replace("$", "")
                    .replace(",", "")
                    .strip()
                )
                clean_fee = float(raw_fee) if raw_fee else 0.00

                # Safe extraction using .get() with fallback column names
                validated_data = (
                    row_clean.get("id"),
                    row_clean.get("NAME") or row_clean.get("name"),
                    row_clean.get("host id") or row_clean.get("host_id"),
                    row_clean.get("host_identity_verified"),
                    row_clean.get("host_name"),
                    row_clean.get("neighbourhood_group")
                    or row_clean.get("neighbourhood group"),
                    row_clean.get("neighbourhood"),
                    row_clean.get("lat") or None,
                    row_clean.get("long") or row_clean.get("long_") or None,
                    row_clean.get("country"),
                    row_clean.get("country_code"),
                    row_clean.get("instant_bookable"),
                    row_clean.get("cancellation_policy"),
                    row_clean.get("room_type"),
                    row_clean.get("construction_year") or None,
                    clean_price,
                    clean_fee,
                    row_clean.get("minimum_nights") or None,
                    row_clean.get("number_of_reviews") or None,
                    row_clean.get("last_review"),
                    row_clean.get("reviews_per_month") or None,
                    row_clean.get("review_rate_number") or None,
                    row_clean.get("calculated_host_listings_count") or None,
                    # Checks BOTH 'availability_365' and 'availability 365' safely:
                    row_clean.get("availability_365")
                    or row_clean.get("availability 365")
                    or None,
                    row_clean.get("house_rules"),
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
