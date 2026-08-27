"""
UECS3203 Advanced Database Systems - Assignment 1
Section 3: Data Analysis
analysis_app.py - interactive console app that runs the 6 analysis
queries, the stored procedure (sp_borough_market_report) and the 2
functions (fn_price_tier, fn_estimated_revenue) defined in analysis.sql,
and prints them as formatted tables.

Requires: pip install mysql-connector-python
"""

import os
import sys
import mysql.connector
from mysql.connector import Error

# Allow the summary (which contains box-drawing chars) to print on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load_analysis_queries():
    """Read the 6 analysis SELECT queries from analysis.sql (not hardcoded)."""
    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis.sql")
    with open(sql_path, encoding="utf-8") as f:
        content = f.read()

    # Only the query section between USE and the first DROP statement
    start = content.find("USE airbnb_db;")
    end = content.find("DROP PROCEDURE")
    section = content[start:end]

    # Drop comment-only lines BEFORE splitting, so semicolons inside
    # comments (e.g. the Query 6 rationale) do not break the statements
    sql_lines = [
        ln for ln in section.splitlines()
        if ln.strip() and not ln.lstrip().startswith("--")
    ]

    queries = []
    for chunk in "\n".join(sql_lines).split(";"):
        sql = chunk.strip()
        if sql.upper().lstrip().startswith("SELECT"):
            queries.append(sql)
    return queries

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
# Query 1-6 : the exact SELECTs from analysis.sql (loaded, not hardcoded)
# ---------------------------------------------------------------------
ANALYSIS_QUERIES = _load_analysis_queries()
if len(ANALYSIS_QUERIES) < 6:
    raise SystemExit("analysis.sql: expected at least 6 SELECT queries, "
                     f"found {len(ANALYSIS_QUERIES)}")


def q1_expensive(conn):
    run(conn, ANALYSIS_QUERIES[0], "Query 1: Top 10 most expensive listings")


def q2_most_reviewed(conn):
    run(conn, ANALYSIS_QUERIES[1], "Query 2: Most frequently reviewed listings")


def q3_best_value(conn):
    run(conn, ANALYSIS_QUERIES[2],
        "Query 3: Affordable, popular & well-rated listings (<150, >50 reviews, >4.7)")


def q4_borough_stats(conn):
    run(conn, ANALYSIS_QUERIES[3], "Query 4: Borough market overview")


def q5_demand(conn):
    run(conn, ANALYSIS_QUERIES[4], "Query 5: Demand category analysis")


def q6_monthly(conn):
    run(conn, ANALYSIS_QUERIES[5], "Query 6: Monthly review trends (last 12 months)")

def q7_low_activity(conn):
    run(conn, ANALYSIS_QUERIES[6], "Query 7: Monthly review activity with low counts")
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
        SELECT 
            fn_price_tier(price) AS price_tier,
            COUNT(*) AS total_listings,
            ROUND(AVG(price), 2) AS avg_price,
            ROUND(MIN(price), 2) AS min_price,
            ROUND(MAX(price), 2) AS max_price,
            ROUND(AVG(review_rate_number), 2) AS avg_rating,
            ROUND(AVG(availability_365), 0) AS avg_availability
        FROM airbnb_listings
        WHERE price > 0
        GROUP BY price_tier
        ORDER BY FIELD(price_tier, 'Budget', 'Standard', 'Premium', 'Luxury')""",
        "Function: fn_price_tier - Price distribution with tier statistics")


def fn_revenue_demo(conn):
    run(conn, """
        SELECT 
            neighbourhood_group AS borough,
            COUNT(*) AS listings,
            ROUND(AVG(price), 2) AS avg_price,
            ROUND(AVG(availability_365), 0) AS avg_availability,
            ROUND(AVG(fn_estimated_revenue(price, availability_365)), 2) AS avg_annual_revenue,
            ROUND(SUM(fn_estimated_revenue(price, availability_365)), 2) AS total_annual_revenue
        FROM airbnb_listings
        WHERE price > 0 AND neighbourhood_group IS NOT NULL
        GROUP BY borough
        ORDER BY total_annual_revenue DESC""",
        "Function: fn_estimated_revenue - Revenue by borough")

def func_pricetier_revenue(conn):
    run(conn, """
        SELECT 
            fn_price_tier(price) AS price_tier,
            COUNT(*) AS listings,
            ROUND(AVG(price), 2) AS avg_price,
            ROUND(AVG(availability_365), 0) AS avg_availability,
            ROUND(AVG(fn_estimated_revenue(price, availability_365)), 2) AS avg_annual_revenue
        FROM airbnb_listings
        WHERE price > 0
        GROUP BY price_tier
        ORDER BY FIELD(price_tier, 'Budget', 'Standard', 'Premium', 'Luxury')""",
        "Function: fn_estimated_revenue - fn_estimated_revenue")

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
 7. Q7 - Monthly review activity with low counts
 8. Procedure - Borough market report
 9. Function  - Price tier
 10. Function  - Estimated revenue
 11. Function - Estimated revenue by price tier
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
        "7": q7_low_activity,
        "8": proc_borough_report,
        "9": fn_price_tier_demo,
        "10": fn_revenue_demo,
        "11": func_pricetier_revenue,
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
