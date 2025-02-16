import sqlite3
import logging

def add_image_column(db_path="database.db"):
    """
    Thêm cột 'image' vào bảng 'menus' (nếu bảng và cột chưa tồn tại).
    """
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("ALTER TABLE menus ADD COLUMN image TEXT")
        connection.commit()
        print("Added 'image' column to 'menus' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'image' already exists in 'menus' table.")
        else:
            print(f"Error adding 'image' column: {e}")
    finally:
        connection.close()

def create_orders_table(db_path="database.db"):
    """
    Tạo bảng 'orders' (nếu chưa có).
    """
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL,
                items TEXT,
                total_price REAL,
                note TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'Pending'
            );
        """)
        connection.commit()
        print("Table 'orders' has been created (if it didn't exist).")
    except sqlite3.OperationalError as e:
        print(f"OperationalError creating 'orders' table: {e}")
    except Exception as e:
        print(f"Error creating 'orders' table: {e}")
    finally:
        connection.close()

def seed_sample_data(db_path="database.db"):
    """
    Thêm dữ liệu mẫu vào bảng 'menus' và 'orders' (nếu chưa có dữ liệu).
    """
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # Thêm dữ liệu mẫu vào bảng 'menus'
        try:
            cursor.execute("SELECT COUNT(*) FROM menus")
            if cursor.fetchone()[0] == 0:
                cursor.executemany("""
                    INSERT INTO menus (name, description, price, image)
                    VALUES (?, ?, ?, ?)
                """, [
                    ("French Fries", "Crispy French Fries", 3.49, "french_fries.jpg"),
                    ("Grilled Chicken Sandwich", "Juicy grilled chicken sandwich", 5.99, "chicken_sandwich.jpg"),
                    ("Classic Cheeseburger", "Cheeseburger with fresh ingredients", 4.99, "cheeseburger.jpg"),
                ])
                print("Inserted sample data into 'menus' table.")
            else:
                print("Sample data already exists in 'menus' table.")
        except sqlite3.OperationalError as e:
            print(f"Error adding sample data to 'menus': {e}")

        # Thêm dữ liệu mẫu vào bảng 'orders'
        try:
            cursor.execute("SELECT COUNT(*) FROM orders")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO orders (order_code, items, total_price, note, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "ORD-1234", '{"1": {"name": "French Fries", "price": 3.49, "quantity": 2}}',
                    6.98, "Quick delivery, please", "2025-01-01 12:00:00", "Pending"
                ))
                print("Inserted sample data into 'orders' table.")
            else:
                print("Sample data already exists in 'orders' table.")
        except sqlite3.OperationalError as e:
            print(f"Error adding sample data to 'orders': {e}")

        connection.commit()
    except Exception as e:
        print(f"Error seeding sample data: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    # Logging setup (optional)
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    # Gọi các hàm bên trên
    try:
        add_image_column()
        create_orders_table()
        seed_sample_data()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
