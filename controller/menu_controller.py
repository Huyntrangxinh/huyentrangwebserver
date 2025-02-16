import os
import time
import logging
import requests
from flask import request, redirect, url_for, current_app, render_template, flash
from model.menu_model import MenuModel

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

class MenuController:
    def __init__(self):
        self.model = MenuModel()

    def list_menu(self):
        """
        Hiển thị danh sách menu (dành cho admin).
        """
        menu_items = self.model.get_menu()
        if not menu_items:
            flash("No menu items available.", "info")
        return render_template("list_menu.html", items=menu_items)

    def request_menu(self):
        """
        Lấy danh sách menu và hiển thị trên trang menu (dành cho khách hàng).
        """
        menu_items = self.model.get_menu()
        return render_template("menu.html", items=menu_items)

    def create_menu(self):
        """
        Hiển thị form tạo món ăn mới.
        """
        return render_template("menu_form.html")
    
    def delete_menu(self, item_id):
        """
        Xóa một món ăn khỏi database.
        """
        try:
            # Xóa món ăn bằng model
            deleted = self.model.delete_menu(item_id)
            if deleted:
                flash("Menu item deleted successfully!", "success")
            else:
                flash("Failed to delete menu item. It may not exist.", "warning")
        except Exception as e:
            logging.error(f"Error deleting menu item: {e}")
            flash("An error occurred while deleting the menu item.", "danger")

        # Chuyển hướng về danh sách menu
        return redirect(url_for("show_menu_list"))

    def handle_upload_image(self, image_file=None, image_url=None):
        """
        Xử lý việc upload hình ảnh hoặc lấy hình ảnh từ URL.
        """
        if image_url:  # Nếu có URL ảnh
            logging.debug(f"Using image from URL: {image_url}")
            try:
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    ext = image_url.rsplit(".", 1)[-1].lower()
                    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
                    if ext in allowed_extensions:
                        image_filename = f"{int(time.time())}_{os.path.basename(image_url)}"
                        upload_path = os.path.join(
                            current_app.root_path, "static", "uploads", image_filename
                        )
                        with open(upload_path, "wb") as out_file:
                            for chunk in response.iter_content(chunk_size=1024):
                                out_file.write(chunk)
                        logging.debug(f"Image downloaded and saved to: {upload_path}")
                        return image_filename
                    else:
                        logging.warning("Unsupported file extension for URL.")
                        flash("Unsupported file extension for URL. Allowed: jpg, jpeg, png, gif.", "warning")
                        return None
                else:
                    logging.error("Failed to download image from URL.")
                    flash("Failed to download image from URL. Please check the link.", "danger")
                    return None
            except Exception as e:
                logging.error(f"Error downloading image from URL: {e}")
                flash("An error occurred while processing the image URL.", "danger")
                return None

        if image_file and image_file.filename != "":  # Xử lý file upload
            allowed_extensions = {"jpg", "jpeg", "png", "gif"}
            ext = image_file.filename.rsplit(".", 1)[-1].lower()
            if ext in allowed_extensions:
                image_filename = f"{int(time.time())}_{image_file.filename}"
                upload_path = os.path.join(
                    current_app.root_path, "static", "uploads", image_filename
                )
                try:
                    image_file.save(upload_path)
                    logging.debug(f"Image saved to: {upload_path}")
                    return image_filename
                except Exception as e:
                    logging.error(f"Failed to save image: {e}")
                    flash("Failed to upload image. Please try again.", "danger")
                    return None
            else:
                logging.warning("Unsupported file extension.")
                flash("Unsupported file extension. Allowed: jpg, jpeg, png, gif.", "warning")
                return None

        logging.info("No image file or URL provided.")
        return None

    def store_menu(self):
        """
        Lưu món ăn mới vào database.
        """
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image_url = request.form.get("image_url")  # Nhận URL ảnh từ form

        # Chuyển đổi giá trị price
        try:
            price = float(price) if price else 0.0
        except ValueError:
            flash("Invalid price value.", "warning")
            return redirect(url_for("create_menu"))

        # Xử lý upload hình ảnh
        image_file = request.files.get("image")
        image_filename = self.handle_upload_image(image_file=image_file, image_url=image_url)

        # Lưu món ăn vào database
        self.model.store_menu(name, price, description, image_filename)

        # Chuyển hướng về danh sách menu
        flash("Menu item created successfully!", "success")
        return redirect(url_for("show_menu_list"))

    def edit_menu(self, item_id):
        """
        Hiển thị form chỉnh sửa món ăn.
        """
        menu_item = self.model.get_menu_by_id(item_id)
        if not menu_item:
            flash("Menu item not found.", "danger")
            return redirect(url_for("show_menu_list"))
        return render_template("edit_menu.html", item=menu_item)

    def update_menu(self, item_id):
        """
        Cập nhật thông tin món ăn.
        """
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image_url = request.form.get("image_url")  # Nhận URL ảnh từ form

        # Chuyển đổi giá trị price
        try:
            price = float(price) if price else 0.0
        except ValueError:
            flash("Invalid price value.", "warning")
            return redirect(url_for("edit_menu", item_id=item_id))

        # Xử lý upload hình ảnh
        image_file = request.files.get("image")
        image_filename = self.handle_upload_image(image_file=image_file, image_url=image_url)

        # Cập nhật database
        self.model.update_menu(item_id, name, price, description, image_filename)

        # Chuyển hướng về danh sách menu
        flash("Menu item updated successfully!", "success")
        return redirect(url_for("show_menu_list"))
