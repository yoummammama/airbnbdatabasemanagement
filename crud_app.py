"""
UECS3203 Advanced Database Systems - Assignment 1
Section 4 & 5: CRUD Operations and Transaction Management
crud_app.py - interactive console app calling the stored procedures
defined in crud_procedures.sql

Requires: pip install mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",         # change to your MySQL username
    "password": "",         # change to your MySQL password
    "database": "airbnb_db" # change to your schema name
}


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database connection failed: {e}")
        return None


def to_decimal(prompt_text, allow_blank=True):
    """Read a float from the user; return None if left blank (means 'no change')."""
    raw = input(prompt_text).strip()
    if allow_blank and raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        print("  Invalid number, treating as blank/no change.")
        return None


def to_int(prompt_text, allow_blank=True):
    raw = input(prompt_text).strip()
    if allow_blank and raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        print("  Invalid integer, treating as blank/no change.")
        return None


# ---------------------------------------------------------------------
# 4a. CREATE
# ---------------------------------------------------------------------
def create_listing(conn):
    print("\n--- Create New Listing ---")
    try:
        p_id = int(input("Listing id: ").strip())
    except ValueError:
        print("id must be an integer.")
        return

    name = input("Name: ").strip()
    host_id_raw = input("Host id: ").strip()
    host_id = int(host_id_raw) if host_id_raw else None
    host_name = input("Host name: ").strip()
    neighbourhood_group = input("Neighbourhood group: ").strip()
    neighbourhood = input("Neighbourhood: ").strip()
    room_type = input("Room type: ").strip()
    price = to_decimal("Price: ", allow_blank=False)
    minimum_nights = to_int("Minimum nights: ")
    availability_365 = to_int("Availability (days/365): ")

    cursor = conn.cursor()
    try:
        cursor.callproc(
            "sp_create_listing",
            [p_id, name, host_id, host_name, neighbourhood_group,
             neighbourhood, room_type, price, minimum_nights,
             availability_365, ""]
        )
        for result in cursor.stored_results():
            pass
        # OUT parameter is retrieved via a follow-up SELECT of session vars
        cursor.execute("SELECT @_sp_create_listing_10")
        print(cursor.fetchone()[0])
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# 4b. RETRIEVE
# ---------------------------------------------------------------------
def retrieve_by_id(conn):
    print("\n--- Retrieve Listing by ID ---")
    try:
        p_id = int(input("Listing id: ").strip())
    except ValueError:
        print("id must be an integer.")
        return

    cursor = conn.cursor()
    try:
        cursor.callproc("sp_retrieve_by_id", [p_id])
        found = False
        for result in cursor.stored_results():
            rows = result.fetchall()
            cols = result.column_names
            if not rows:
                print("No listing found with that id.")
            for row in rows:
                found = True
                for col, val in zip(cols, row):
                    print(f"  {col}: {val}")
        if not found:
            print("No listing found with that id.")
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


def retrieve_by_criteria(conn):
    print("\n--- Retrieve Listings by Criteria (leave blank to skip a filter) ---")
    neighbourhood_group = input("Neighbourhood group: ").strip() or None
    room_type = input("Room type: ").strip() or None
    min_price = to_decimal("Min price: ")
    max_price = to_decimal("Max price: ")

    cursor = conn.cursor()
    try:
        cursor.callproc(
            "sp_retrieve_by_criteria",
            [neighbourhood_group, room_type, min_price, max_price]
        )
        for result in cursor.stored_results():
            rows = result.fetchall()
            cols = result.column_names
            if not rows:
                print("No matching listings.")
                continue
            print(" | ".join(cols))
            for row in rows:
                print(" | ".join(str(v) for v in row))
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# 4c. UPDATE
# ---------------------------------------------------------------------
def update_listing(conn):
    print("\n--- Update Listing (leave blank to keep current value) ---")
    try:
        p_id = int(input("Listing id to update: ").strip())
    except ValueError:
        print("id must be an integer.")
        return

    price = to_decimal("New price: ")
    minimum_nights = to_int("New minimum nights: ")
    availability_365 = to_int("New availability_365: ")

    cursor = conn.cursor()
    try:
        cursor.callproc(
            "sp_update_listing",
            [p_id, price, minimum_nights, availability_365, ""]
        )
        cursor.execute("SELECT @_sp_update_listing_4")
        print(cursor.fetchone()[0])
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# 4d. DELETE
# ---------------------------------------------------------------------
def delete_listing(conn):
    print("\n--- Delete Listing ---")
    try:
        p_id = int(input("Listing id to delete: ").strip())
    except ValueError:
        print("id must be an integer.")
        return

    confirm = input(f"Confirm delete listing {p_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    cursor = conn.cursor()
    try:
        cursor.callproc("sp_delete_listing", [p_id, ""])
        cursor.execute("SELECT @_sp_delete_listing_1")
        print(cursor.fetchone()[0])
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# 5. TRANSACTION MANAGEMENT demos
# ---------------------------------------------------------------------
def batch_price_update(conn):
    print("\n--- Batch Price Update (SAVEPOINT / ROLLBACK demo) ---")
    print("Enter two listings to update in a single transaction.")
    try:
        id1 = int(input("Listing 1 id: ").strip())
        price1 = float(input("Listing 1 new price: ").strip())
        id2 = int(input("Listing 2 id: ").strip())
        price2 = float(input("Listing 2 new price: ").strip())
    except ValueError:
        print("Invalid input.")
        return

    cursor = conn.cursor()
    try:
        cursor.callproc(
            "sp_batch_price_update",
            [id1, price1, id2, price2, ""]
        )
        cursor.execute("SELECT @_sp_batch_price_update_4")
        print(cursor.fetchone()[0])
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


def delete_host_listings_safe(conn):
    print("\n--- Delete All Listings For a Host (transactional, all-or-nothing) ---")
    try:
        host_id = int(input("Host id: ").strip())
    except ValueError:
        print("host_id must be an integer.")
        return

    cursor = conn.cursor()
    try:
        cursor.callproc("sp_delete_host_listings_safe", [host_id, ""])
        cursor.execute("SELECT @_sp_delete_host_listings_safe_1")
        print(cursor.fetchone()[0])
    except Error as e:
        print(f"Error: {e}")
    finally:
        cursor.close()


# ---------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------
MENU = """
=========================================
 Airbnb Listings - CRUD & Transaction App
=========================================
 1. Create a new listing
 2. Retrieve a listing by id
 3. Retrieve listings by criteria
 4. Update a listing
 5. Delete a listing
 6. Batch price update (transaction demo)
 7. Delete all listings for a host (transaction demo)
 0. Exit
-----------------------------------------
"""


def main():
    conn = get_connection()
    if conn is None:
        return

    actions = {
        "1": create_listing,
        "2": retrieve_by_id,
        "3": retrieve_by_criteria,
        "4": update_listing,
        "5": delete_listing,
        "6": batch_price_update,
        "7": delete_host_listings_safe,
    }

    try:
        while True:
            print(MENU)
            choice = input("Select an option: ").strip()
            if choice == "0":
                print("Goodbye.")
                break
            action = actions.get(choice)
            if action:
                action(conn)
            else:
                print("Invalid option, try again.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()