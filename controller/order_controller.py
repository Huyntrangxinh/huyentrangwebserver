import logging
import json
import sqlite3
from flask import render_template, request, redirect, url_for, flash
from model.order_model import OrderModel

class OrderController:
    def __init__(self):
        self.model = OrderModel()

    def list_orders(self):
        """
        Lấy danh sách tất cả đơn hàng từ model và hiển thị.
        """
        orders = self.model.get_all_orders()
        for o in orders:
            if o["items"]:
                o["items"] = json.loads(o["items"])
            else:
                o["items"] = {}
        return render_template("list_order.html", orders=orders)

    def edit_order(self, order_id):
        """
        Hiển thị form chỉnh sửa đơn hàng (theo ID).
        """
        order = self.model.get_order_by_id(order_id)
        if not order:
            return "Order not found", 404

        if order["items"]:
            order["items"] = json.loads(order["items"])
        else:
            order["items"] = {}

        return render_template("edit_order.html", order=order)

    def view_order(self, order_id):
        """
        Hiển thị chi tiết 1 đơn hàng (theo ID).
        """
        order = self.model.get_order_by_id(order_id)
        if not order:
            return "Order not found", 404

        if order["items"]:
            order["items"] = json.loads(order["items"])
        else:
            order["items"] = {}

        return render_template("view_order.html", order=order)

    def new_order(self):
        """
        Render form tạo đơn hàng (nếu cần tạo thủ công).
        """
        return render_template("order_form.html")

    def store_order(self):
        """
        Xử lý khi submit form tạo đơn hàng (nếu tạo thủ công).
        """
        order_code = request.form.get("order_code")
        items = request.form.get("items")
        total_price = request.form.get("total_price")
        note = request.form.get("note")

        if total_price:
            total_price = float(total_price)

        self.model.create_order(order_code, items, total_price, note, status="Pending")
        return redirect(url_for("show_order_list"))

    def update_order(self, order_id):
        """
        Cập nhật thông tin đơn hàng.
        """
        order_code = request.form.get("order_code")
        note = request.form.get("note")
        status = request.form.get("status")

        items = {}
        product_names = request.form.getlist('menu_id[]')
        prices = request.form.getlist('price[]')
        quantities = request.form.getlist('quantity[]')

        total_price = 0

        for i in range(len(product_names)):
            price = float(prices[i].replace(',', '.')) if prices[i] else 0
            quantity = int(quantities[i]) if quantities[i] else 0
            total_price += price * quantity

            items[i] = {
                'name': product_names[i],
                'price': price,
                'quantity': quantity
            }

        updated_order = {
            'order_code': order_code,
            'total_price': float(total_price),
            'note': note,
            'status': int(status),
            'items': json.dumps(items)
        }

        logging.info(f"Updated Order: {updated_order}")

        self.model.update_order(order_id, 
                                updated_order['order_code'], 
                                updated_order['items'], 
                                updated_order['total_price'], 
                                updated_order['note'], 
                                updated_order['status'])

        return redirect(url_for('show_order_list'))

    def delete_order(self, order_id):
        """
        Xoá đơn hàng.
        """
        self.model.delete_order(order_id)
        return redirect(url_for("show_order_list"))

    def update_order_status(self, order_id, new_status):
        """
        Cập nhật trạng thái đơn hàng.
        """
        self.model.update_order_status(order_id, new_status)
        return redirect(url_for("show_order_list"))
    
    def get_dashboard_stats(self):
        """
        Lấy thông tin thống kê cho dashboard (doanh thu và đơn hàng).
        """
        revenue_summary = self.model.get_revenue_summary()

        order_summary = {
            "total_orders": len(self.model.get_all_orders()),
            "pending_orders": len([order for order in self.model.get_all_orders() if order["status"] == "0"]),
            "completed_orders": len([order for order in self.model.get_all_orders() if order["status"] == "2"]),
        }

        return {
            "revenue_summary": revenue_summary,
            "order_summary": order_summary
        }

    def dashboard(self):
        """
        Hiển thị trang dashboard với thông tin thống kê doanh thu và đơn hàng.
        """
        stats = self.get_dashboard_stats()
        return stats
    
    def get_best_selling_drink(self):
        """
        Lấy món nước được gọi nhiều nhất từ đơn hàng.
        Trả về {'name': 'Tên món', 'quantity': số lượng}.
        """
        connection = self.model._connect()  # Đảm bảo kết nối DB chính xác
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT json_extract(items, '$.*.name') AS drink_names,
                       json_extract(items, '$.*.quantity') AS quantities
                FROM orders
            """)
            rows = cursor.fetchall()

            drink_counts = {}
            for row in rows:
                if row[0] and row[1]:  # Kiểm tra dữ liệu hợp lệ trước khi xử lý
                    drink_names = json.loads(row[0])
                    quantities = json.loads(row[1])

                    for i in range(len(drink_names)):
                        drink_name = drink_names[i]
                        quantity = int(quantities[i])
                        if drink_name in drink_counts:
                            drink_counts[drink_name] += quantity
                        else:
                            drink_counts[drink_name] = quantity

            if not drink_counts:
                return {"name": "Không có dữ liệu", "quantity": 0}

            best_selling_drink = max(drink_counts, key=drink_counts.get)
            return {"name": best_selling_drink, "quantity": drink_counts[best_selling_drink]}

        except sqlite3.Error as e:
            print(f"Lỗi khi lấy món nước được gọi nhiều nhất: {e}")
            return {"name": "Lỗi dữ liệu", "quantity": 0}

        finally:
            connection.close()
