import sqlite3
import logging
from datetime import datetime

class OrderModel:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        logging.basicConfig(level=logging.DEBUG)

    def _connect(self):
        """
        Kết nối tới cơ sở dữ liệu SQLite.
        """
        return sqlite3.connect(self.db_path)

    def _format_date(self, date_str):
        """
        Định dạng chuỗi ngày tháng (date_str) theo định dạng DD-MM-YYYY.
        Nếu không chuyển được, trả về chính chuỗi ban đầu.
        """
        try:
            # datetime.fromisoformat chấp nhận cả "YYYY-MM-DD HH:MM:SS" và "YYYY-MM-DDTHH:MM:SS"
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d-%m-%Y")
        except Exception as e:
            logging.error(f"Lỗi định dạng ngày: {e}")
            return date_str

    def get_revenue_summary(self):
        """
        Lấy tổng doanh thu theo ngày và tháng.
        """
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT DATE(created_at) AS order_date, SUM(total_price) AS total
                FROM orders
                GROUP BY DATE(created_at)
                ORDER BY order_date DESC
            """)
            daily_sales = cursor.fetchall()

            cursor.execute("""
                SELECT strftime('%Y-%m', created_at) AS order_month, SUM(total_price) AS total
                FROM orders
                GROUP BY order_month
                ORDER BY order_month DESC
            """)
            monthly_sales = cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy doanh thu: {e}")
            daily_sales, monthly_sales = [], []
        finally:
            connection.close()

        return {
            "daily_sales": [{"date": row[0], "total": row[1]} for row in daily_sales],
            "monthly_sales": [{"month": row[0], "total": row[1]} for row in monthly_sales]
        }

    def create_order(self, order_code, items, total_price, note, status="Pending"):
        """
        Tạo một đơn hàng mới và lưu vào bảng orders.
        """
        logging.debug(f"Tạo order: {order_code}, tổng tiền={total_price}, trạng thái={status}")
        connection = self._connect()
        cursor = connection.cursor()

        created_at = datetime.now().isoformat()
        try:
            cursor.execute("""
                INSERT INTO orders (order_code, items, total_price, note, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_code, items, total_price, note, created_at, status))
            connection.commit()
            logging.info(f"Order {order_code} tạo thành công.")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi tạo order: {e}")
        finally:
            connection.close()

    def get_all_orders(self):
        """
        Lấy tất cả các đơn hàng từ bảng orders, trả về danh sách dict.
        Thêm trường 'display_date' (định dạng DD-MM-YYYY) được tính từ created_at.
        """
        logging.debug("Đang lấy tất cả các đơn hàng.")
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT id, order_code, items, total_price, note, created_at, status
                FROM orders
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy đơn hàng: {e}")
            rows = []
        finally:
            connection.close()

        orders = []
        for row in rows:
            # Tạo trường display_date dựa trên created_at
            display_date = self._format_date(row[5])
            order_dict = {
                "id": row[0],
                "order_code": row[1],
                "items": row[2],
                "total_price": row[3],
                "note": row[4],
                "created_at": row[5],
                "status": row[6],
            "created_at": datetime.strptime(row[5], "%Y-%m-%dT%H:%M:%S.%f").strftime("%Y-%m-%d"),  # Chỉ lấy ngày
            }
            orders.append(order_dict)
        return orders

    def get_order_by_id(self, order_id):
        """
        Lấy thông tin 1 đơn hàng theo ID, kèm theo trường display_date.
        """
        logging.debug(f"Đang lấy order với ID={order_id}.")
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT id, order_code, items, total_price, note, created_at, status
                FROM orders
                WHERE id = ?
            """, (order_id,))
            row = cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi lấy order ID={order_id}: {e}")
            row = None
        finally:
            connection.close()

        if row:
            display_date = self._format_date(row[5])
            return {
                "id": row[0],
                "order_code": row[1],
                "items": row[2],
                "total_price": row[3],
                "note": row[4],
                "created_at": row[5],
                "status": row[6],
                "display_date": display_date
            }
        return None

    def update_order(self, order_id, order_code, items, total_price, note, status):
        """
        Cập nhật thông tin của đơn hàng.
        """
        logging.debug(f"Cập nhật order ID={order_id}, code={order_code}, tổng tiền={total_price}, trạng thái={status}.")
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                UPDATE orders
                SET order_code = ?,
                    items = ?,
                    total_price = ?,
                    note = ?,
                    status = ?
                WHERE id = ?
            """, (order_code, items, total_price, note, status, order_id))
            connection.commit()
            logging.info(f"Order ID={order_id} cập nhật thành công.")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi cập nhật order ID={order_id}: {e}")
        finally:
            connection.close()

    def update_order_status(self, order_id, status):
        """
        Cập nhật trạng thái của đơn hàng.
        """
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                UPDATE orders
                SET status = ?
                WHERE id = ?
            """, (status, order_id))
            rows_affected = cursor.rowcount
            logging.info(f"Số dòng được cập nhật: {rows_affected}")
            connection.commit()
            logging.info(f"Order ID={order_id} đã cập nhật trạng thái thành {status}.")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi cập nhật trạng thái order ID={order_id}: {e}")
        finally:
            connection.close()

    def delete_order(self, order_id):
        """
        Xóa 1 đơn hàng theo ID.
        """
        logging.debug(f"Đang xóa order ID={order_id}.")
        connection = self._connect()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            connection.commit()
            logging.info(f"Order ID={order_id} đã được xóa thành công.")
        except sqlite3.Error as e:
            logging.error(f"Lỗi khi xóa order ID={order_id}: {e}")
        finally:
            connection.close()

    def add_order_date_column(self, db_path="database.db"):
        """
        Thêm cột 'order_date' vào bảng 'orders' để lưu ngày tháng năm.
        """
        try:
            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()
            cursor.execute("ALTER TABLE orders ADD COLUMN order_date TEXT")
            connection.commit()
            print("Added 'order_date' column to 'orders' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'order_date' already exists in 'orders' table.")
            else:
                print(f"Error adding 'order_date' column: {e}")
        finally:
            connection.close()
            
