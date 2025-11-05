import os
import time
import psycopg
from neo4j import GraphDatabase

# ==============================
# CONFIGURATION
# ==============================
DATABASE_URL = os.environ.get("DATABASE_URL")
NEO4J_URI = os.environ.get("NEO4J_URI")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")


# ==============================
# WAIT FUNCTIONS
# ==============================
def wait_for_postgres(timeout=30):
    print("⏳ Waiting for PostgreSQL…")
    start = time.time()
    while True:
        try:
            conn = psycopg.connect(DATABASE_URL)
            conn.close()
            print("✅ PostgreSQL is ready!")
            return
        except Exception as e:
            if time.time() - start > timeout:
                raise TimeoutError("⏰ Timeout waiting for PostgreSQL")
            print("🔄 Retrying PostgreSQL…", str(e))
            time.sleep(3)


def wait_for_neo4j(timeout=30):
    print("⏳ Waiting for Neo4j…")
    start = time.time()
    while True:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            print("✅ Neo4j is ready!")
            return
        except Exception as e:
            if time.time() - start > timeout:
                raise TimeoutError("⏰ Timeout waiting for Neo4j")
            print("🔄 Retrying Neo4j…", str(e))
            time.sleep(3)


# ==============================
# MAIN ETL FUNCTION
# ==============================
def etl():
    wait_for_postgres()
    wait_for_neo4j()

    print("🚀 Starting ETL process…")

    # Connect to PostgreSQL
    print("📥 Reading customers from PostgreSQL...")
    with psycopg.connect(DATABASE_URL) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT id, name, join_date FROM customers")
            customers = cur.fetchall()
            print(f"Found {len(customers)} customers.")

    print("📥 Reading orders from PostgreSQL...")
    with psycopg.connect(DATABASE_URL) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT id, customer_id, ts FROM orders")
            orders = cur.fetchall()
            print(f"Found {len(orders)} orders.")

    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        print("📤 Creating constraints…")
        session.run("""
        CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
        FOR (c:Customer)
        REQUIRE c.id IS UNIQUE
        """)
        session.run("""
        CREATE CONSTRAINT order_id_unique IF NOT EXISTS
        FOR (o:Order)
        REQUIRE o.id IS UNIQUE
        """)

        print("📤 Importing customers into Neo4j...")
        for cid, name, join_date in customers:
            session.run(
                "MERGE (c:Customer {id: $id}) "
                "SET c.name = $name, c.join_date = $join_date",
                id=cid, name=name, join_date=str(join_date)
            )

        print("📤 Importing orders into Neo4j...")
        for oid, customer_id, ts in orders:
            session.run(
                "MERGE (o:Order {id: $id}) "
                "SET o.timestamp = $ts "
                "WITH o "
                "MATCH (c:Customer {id: $customer_id}) "
                "MERGE (c)-[:PLACED]->(o)",
                id=oid, ts=str(ts), customer_id=customer_id
            )

    driver.close()
    print("✅ ETL completed.")


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    etl()
