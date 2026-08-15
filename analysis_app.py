"""
UECS3203 Advanced Database Systems - Assignment 1
Section 3: Data Analysis
analysis_app.py - interactive console app that runs the 6 analysis
queries, the stored procedure (sp_borough_market_report) and the 2
functions (fn_price_tier, fn_estimated_revenue) defined in analysis.sql,
and prints them as formatted tables.

Requires: pip install mysql-connector-python
"""

import sys
import mysql.connector
from mysql.connector import Error

# Allow the summary (which contains box-drawing chars) to print on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # change to your MySQL username
    "password": "root",      # change to your MySQL password
    "database": "airbnb_db"  # change to your schema name
}


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database connection failed: {e}")
        return None


def print_table(rows, cols, title):
    """Pretty-print query results as a simple aligned table."""
    print(f"\n=== {title} ===")
    if not rows:
        print("  (no rows returned)")
        return
    widths = [
        max(len(str(c)), max((len(str(r[i])) for r in rows), default=0))
        for i, c in enumerate(cols)
    ]
    header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
    print("  " + header)
    print("  " + "-" * len(header))
    for row in rows:
        line = " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row))
        print("  " + line)


def run(conn, sql, title):
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        print_table(rows, cols, title)
    except Error as e:
        print(f"\n=== {title} ===\n  ERROR: {e}")
    finally:
        cur.close()


# ---------------------------------------------------------------------
# Query 1-6 : the exact SELECTs from analysis.sql
# ---------------------------------------------------------------------
def q1_expensive(conn):
    run(conn, """
        SELECT id, name, neighbourhood, room_type, price
        FROM airbnb_listings
        ORDER BY price DESC
        LIMIT 10""",
        "Query 1: Top 10 most expensive listings")


def q2_most_reviewed(conn):
    run(conn, """
        SELECT id, name, neighbourhood, number_of_reviews, review_rate_number
        FROM airbnb_listings
        ORDER BY number_of_reviews DESC
        LIMIT 10""",
        "Query 2: Most frequently reviewed listings")


def q3_best_value(conn):
    run(conn, """
        SELECT name, neighbourhood_group, room_type, price,
               number_of_reviews, review_rate_number
        FROM airbnb_listings
        WHERE price < 150
          AND number_of_reviews > 50
          AND review_rate_number > 4.7
        ORDER BY review_rate_number DESC, price ASC
        LIMIT 15""",
        "Query 3: Affordable, popular & well-rated listings (<150, >50 reviews, >4.7)")


def q4_borough_stats(conn):
    run(conn, """
        SELECT neighbourhood_group AS borough,
               COUNT(*) AS total_listings,
               ROUND(AVG(price), 2) AS avg_price,
               ROUND(MIN(price), 2) AS min_price,
               ROUND(MAX(price), 2) AS max_price,
               ROUND(AVG(availability_365), 0) AS avg_availability_days
        FROM airbnb_listings
        WHERE price > 0 AND price < 10000
        GROUP BY neighbourhood_group
        ORDER BY avg_price DESC""",
        "Query 4: Borough market overview")


def q5_demand(conn):
    run(conn, """
        SELECT CASE
                 WHEN availability_365 = 0 THEN 'Fully Booked'
                 WHEN availability_365 BETWEEN 1 AND 90 THEN 'Very High Demand'
                 WHEN availability_365 BETWEEN 91 AND 200 THEN 'High Demand'
                 WHEN availability_365 BETWEEN 201 AND 300 THEN 'Moderate Demand'
                 ELSE 'Low Demand'
               END AS demand_category,
               COUNT(*) AS listings,
               ROUND(AVG(price), 2) AS avg_price,
               ROUND(AVG(number_of_reviews), 0) AS avg_reviews,
               ROUND(MIN(price), 2) AS min_price,
               ROUND(MAX(price), 2) AS max_price
        FROM airbnb_listings
        WHERE price > 0
        GROUP BY demand_category
        ORDER BY avg_price DESC""",
        "Query 5: Demand category analysis")


def q6_monthly(conn):
    run(conn, """
        SELECT DATE_FORMAT(STR_TO_DATE(last_review, '%m/%d/%Y'), '%Y-%m')
                 AS review_month,
               COUNT(*) AS listings_reviewed,
               ROUND(AVG(price), 2) AS avg_price,
               ROUND(AVG(review_rate_number), 1) AS avg_rating
        FROM airbnb_listings
        WHERE last_review IS NOT NULL
          AND last_review != ''
          AND STR_TO_DATE(last_review, '%m/%d/%Y') IS NOT NULL
        GROUP BY review_month
        ORDER BY review_month DESC
        LIMIT 12""",
        "Query 6: Monthly review trends (last 12 months)")


# ---------------------------------------------------------------------
# Procedure: sp_borough_market_report(borough, OUT summary)
# ---------------------------------------------------------------------
def proc_borough_report(conn):
    print("\n--- Borough Market Report (stored procedure) ---")
    borough = input("Borough name (e.g. Manhattan): ").strip() or "Manhattan"

    cur = conn.cursor()
    try:
        # CALL the procedure; OUT summary goes into @s
        cur.execute("CALL sp_borough_market_report(%s, @s)", (borough,))

        # 1) first result set = room-type breakdown for the borough
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        print_table(rows, cols, f"Room-type breakdown for {borough}")

        # 2) move to the next result and read the OUT summary
        cur.nextset()
        cur.execute("SELECT @s")
        summary = cur.fetchone()[0]
        print("\n" + str(summary))
    except Error as e:
        print(f"  ERROR: {e}")
    finally:
        cur.close()


# ---------------------------------------------------------------------
# Functions: fn_price_tier, fn_estimated_revenue
# ---------------------------------------------------------------------
def fn_price_tier_demo(conn):
    run(conn, """
        SELECT id, name, price,
               fn_price_tier(price) AS price_tier
        FROM airbnb_listings
        WHERE price > 0
        ORDER BY price DESC
        LIMIT 10""",
        "Function: fn_price_tier applied to top 10 listings")


def fn_revenue_demo(conn):
    run(conn, """
        SELECT id, name, price, availability_365,
               fn_estimated_revenue(price, availability_365) AS est_annual_revenue
        FROM airbnb_listings
        WHERE price > 0
        ORDER BY price DESC
        LIMIT 10""",
        "Function: fn_estimated_revenue (60% occupancy) applied to top 10")


MENU = """
=========================================
 Airbnb Listings - Data Analysis App
=========================================
 1. Q1 - Top 10 most expensive
 2. Q2 - Most frequently reviewed
 3. Q3 - Affordable, popular & well-rated
 4. Q4 - Borough market overview
 5. Q5 - Demand category analysis
 6. Q6 - Monthly review trends
 7. Procedure - Borough market report
 8. Function  - Price tier
 9. Function  - Estimated revenue
 0. Exit
-----------------------------------------
"""


def main():
    conn = get_connection()
    if conn is None:
        return

    actions = {
        "1": q1_expensive,
        "2": q2_most_reviewed,
        "3": q3_best_value,
        "4": q4_borough_stats,
        "5": q5_demand,
        "6": q6_monthly,
        "7": proc_borough_report,
        "8": fn_price_tier_demo,
        "9": fn_revenue_demo,
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
