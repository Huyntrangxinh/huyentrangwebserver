
import logging
import uuid
import json
from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    session, 
    flash, 
    jsonify
)
from controller.menu_controller import MenuController
from controller.order_controller import OrderController
from model.user_model import UserModel  # Giả sử bạn đã tạo model này để quản lý người dùng
from model.order_model import OrderModel
db = OrderModel()  # Đảm bảo khởi tạo đúng
app = Flask(__name__)
app.secret_key = "some-secret-key"  # Thay bằng chuỗi bí mật bất kỳ

# --------------------------------------------------------------
# ROUTE REGISTER
# --------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")  # admin hoặc staff

        user_model = UserModel()
        if user_model.get_user_by_email(email):
            user_model.close()
            return "Email đã tồn tại!", 400

        user_model.create_user(email, password, role)
        user_model.close()  # Đảm bảo đóng kết nối
        return redirect(url_for("login"))


# --------------------------------------------------------------
# ROUTE LOGIN/LOGOUT
# --------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    GET: Hiển thị form đăng nhập
    POST: Xử lý đăng nhập
    """
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")

        # Kiểm tra thông tin đăng nhập
        user_model = UserModel()
        user = user_model.authenticate_user(email, password)

        if user:
            session["user_role"] = user["role"]
            session["user_email"] = user["email"]
            if user["role"] == "admin":
                return redirect(url_for("show_menu_list"))
            else:
                return redirect(url_for("show_menu"))
        else:
            # Trả về trang lỗi login_error.html
            return render_template("login_error.html"), 401

        


@app.route("/logout")
def logout():
    session.pop("user_role", None)
    session.pop("user_email", None)
    return render_template("logout.html")


# --------------------------------------------------------------
# ROUTES CHO MENU (CHO FRONTEND VÀ ADMIN)
# --------------------------------------------------------------
@app.route("/")
def show_menu():
    controller = MenuController()
    return controller.request_menu()

@app.route("/menu/edit/<int:item_id>", methods=["GET"])
def edit_menu(item_id):
    controller = MenuController()
    return controller.edit_menu(item_id)

@app.route("/menu/update/<int:item_id>", methods=["POST"])
def update_menu(item_id):
    controller = MenuController()
    return controller.update_menu(item_id)

@app.route("/admin/menu/view")
def view_menu_page():
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = MenuController()
    return controller.list_menu()

@app.route("/admin/menu/manager")
def show_menu_list():
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = MenuController()
    return controller.list_menu()

@app.route("/admin/menu/create")
def create_menu():
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = MenuController()
    return controller.create_menu()

@app.route("/admin/menu/store", methods=["POST"])
def store_menu():
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = MenuController()
    return controller.store_menu()

@app.route("/menu/remove/<int:item_id>", methods=["GET"])
def remove_menu(item_id):
    """
    Xóa một món ăn khỏi menu (về mặt quản trị).
    """
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = MenuController()
    return controller.delete_menu(item_id)


# --------------------------------------------------------------
# ROUTES CHO GIỎ HÀNG (CART)
# --------------------------------------------------------------
@app.route("/cart")
def view_cart():
    """
    Hiển thị giỏ hàng với thông tin sản phẩm, bao gồm hình ảnh.
    """
    cart = session.get("cart", {})
    total_price = sum(item["price"] * item["quantity"] for item in cart.values())
    return render_template("cart.html", cart=cart, total_price=total_price)

@app.route("/cart/add/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    """
    Thêm sản phẩm vào giỏ hàng (hoặc tăng số lượng nếu sản phẩm đã có).
    """
    quantity = request.form.get("quantity", 1, type=int)
    cart = session.get("cart", {})

    if str(item_id) in cart:
        cart[str(item_id)]["quantity"] += quantity
    else:
        # Lấy thông tin sản phẩm từ MenuController
        menu_controller = MenuController()
        menu_item = menu_controller.model.get_menu_by_id(item_id)
        if not menu_item:
            return "Item not found", 404

        # Lưu thông tin sản phẩm, bao gồm hình ảnh
        cart[str(item_id)] = {
            "name": menu_item["name"],
            "price": menu_item["price"],
            "image": menu_item.get("image", None),  # Thông tin hình ảnh
            "quantity": quantity
        }

    session["cart"] = cart
    return redirect(url_for("view_cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    """
    Xóa hẳn một sản phẩm khỏi giỏ hàng.
    """
    cart = session.get("cart", {})
    if str(item_id) in cart:
        del cart[str(item_id)]
    session["cart"] = cart
    return redirect(url_for("view_cart"))

# ------ Thêm route cho nút cộng / trừ số lượng ------
@app.route("/cart/update/<int:item_id>", methods=["POST"])
def update_cart_item(item_id):
    """
    Cập nhật số lượng sản phẩm trong giỏ (tăng/giảm).
    - action = 'increment' => Tăng 1
    - action = 'decrement' => Giảm 1 (tối thiểu 1)
    """
    action = request.form.get("action")
    cart = session.get("cart", {})

    if str(item_id) in cart:
        if action == "increment":
            cart[str(item_id)]["quantity"] += 1
        elif action == "decrement":
            if cart[str(item_id)]["quantity"] > 1:
                cart[str(item_id)]["quantity"] -= 1

    session["cart"] = cart
    return redirect(url_for("view_cart"))
# -----------------------------------------------

@app.route("/cart/checkout", methods=["POST"])
def checkout():
    """
    Xử lý đặt hàng. Lưu thông tin order xuống DB, xóa giỏ hàng.
    """
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("view_cart"))

    note = request.form.get("note", "")
    total_price = sum(item["price"] * item["quantity"] for item in cart.values())
    order_code = "ORD-" + str(uuid.uuid4())[:8]
    items_json = json.dumps(cart)

    order_model = OrderModel()
    order_model.create_order(order_code, items_json, total_price, note)

    # Xóa giỏ hàng sau khi đặt xong
    session["cart"] = {}
    return render_template("order_success.html", order_code=order_code)


# --------------------------------------------------------------
# ROUTES CHO ORDER (ADMIN/STAFF)
# --------------------------------------------------------------
@app.route("/admin/manager/order", methods=["GET"])
def show_order_list():
    """
    Xem tất cả đơn hàng (Admin/Staff).
    """
    user_role = session.get("user_role")
    if user_role not in ["admin", "staff"]:
        return "Access denied", 403

    controller = OrderController()
    return controller.list_orders()

@app.route("/admin/manager/order/view/<int:order_id>", methods=["GET"])
def view_order_detail(order_id):
    if session.get("user_role") != "admin":
        return "Access denied", 403
    controller = OrderController()
    return controller.view_order(order_id)

def edit_order(order_id):
    controller = OrderController()
    return controller.edit_order(order_id)

# Xử lý cập nhật đơn hàng
@app.route("/admin/manager/order/update/<int:order_id>", methods=["POST"])
def update_order(order_id):
    controller = OrderController()
    return controller.update_order(order_id)

@app.route("/admin/manager/order/delete/<int:order_id>", methods=["POST"])
def remove_order(order_id):
    if session.get("user_role") not in ["admin", "staff"]:
        return "Access denied", 403
    controller = OrderController()
    return controller.delete_order(order_id)

@app.route("/admin/manager/order/edit/<int:order_id>", methods=["GET"])
def edit_order(order_id):
    controller = OrderController()
    return controller.edit_order(order_id)

@app.route("/admin/manager/order/status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    """
    Cập nhật trạng thái đơn hàng.
    - 0 = Chưa hoàn thành
    - 1 = Đang thực hiện
    - 2 = Đã hoàn thành
    """
    flash("Bạn không có quyền truy cập chức năng này.", "danger")
    user_role = session.get("user_role")
    if user_role not in ["admin", "staff"]:
        flash("Bạn không có quyền truy cập chức năng này.", "danger")
        return redirect(url_for("show_order_list"))
    
    new_status = request.form.get("status")
    logging.info(f"new_status: {new_status}")
    if new_status not in ["0", "1", "2"]:
        flash("Giá trị trạng thái không hợp lệ.", "warning")
        return redirect(url_for("show_order_list"))

    try:
        controller = OrderController()
        controller.update_order_status(order_id, int(new_status))
        flash("Trạng thái đơn hàng đã được cập nhật thành công.", "success")
    except Exception as e:
        flash(f"Có lỗi xảy ra khi cập nhật trạng thái đơn hàng: {e}", "danger")

    return redirect(url_for("show_order_list"))


# --------------------------------------------------------------
# ROUTES CHO USER MANAGEMENT (CHỈ ADMIN)
# --------------------------------------------------------------
@app.route("/admin/users", methods=["GET"])
def user_management():
    """
    Hiển thị danh sách tất cả user cho admin.
    """
    if session.get("user_role") != "admin":
        return "Access denied", 403
    
    user_model = UserModel()
    users = user_model.get_all_users()  # Hàm này bạn tự định nghĩa trong UserModel
    user_model.close()

    return render_template("user_management.html", users=users)

@app.route("/admin/users/edit/<email>", methods=["GET", "POST"])
def edit_user_role(email):
    """
    Sửa role của user: 
    - GET: Hiển thị form sửa
    - POST: Xử lý cập nhật role
    """
    if session.get("user_role") != "admin":
        return "Access denied", 403

    user_model = UserModel()
    if request.method == "GET":
        user = user_model.get_user_by_email(email)
        if not user:
            user_model.close()
            return "User không tồn tại", 404
        user_model.close()
        # user = (id, email, password, role, ...)
        return render_template("edit_user_role.html", user={"email": user[1], "role": user[3]})
    else:
        new_role = request.form.get("role")
        if new_role not in ["admin", "staff"]:
            user_model.close()
            return "Role không hợp lệ", 400
        user_model.update_user_role(email, new_role)
        user_model.close()

        flash("Role đã được cập nhật thành công!", "success")
        return redirect(url_for("user_management"))

@app.route("/admin/users/delete/<string:email>", methods=["POST"])
def delete_user(email):
    """
    Xóa user (CHỈ ADMIN).
    """
    if session.get("user_role") != "admin":
        return "Access denied", 403
    
    user_model = UserModel()
    user_model.delete_user(email)
    user_model.close()

    flash("Đã xóa user thành công!", "success")
    return redirect(url_for("user_management"))

@app.route("/api/revenue", methods=["GET"])
def get_revenue():
    """
    API lấy dữ liệu doanh thu theo ngày và tháng.
    """
    order_model = OrderModel()
    data = order_model.get_revenue_summary()
    return jsonify(data)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if session.get("user_role") != "admin":
        return "Access denied", 403

    controller = OrderController()
    stats = controller.dashboard()

    # Thêm dữ liệu món nước được gọi nhiều nhất
    stats["best_selling_drink"] = controller.get_best_selling_drink()

    return render_template("dashboard.html", stats=stats)


def format_currency(value):
    """Format số thành dạng tiền tệ đô la Mỹ ($1,234.56)"""
    try:
        return "${:,.2f}".format(float(value))  # Định dạng USD (có dấu phẩy, 2 chữ số thập phân)
    except (ValueError, TypeError):
        return value  # Nếu không thể chuyển đổi, trả về giá trị gốc

# Đăng ký filter với Jinja2
app.jinja_env.filters['currency'] = format_currency


# --------------------------------------------------------------
# CHẠY ỨNG DỤNG
# --------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
