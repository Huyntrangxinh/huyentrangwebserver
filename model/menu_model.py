# model/menu_model.py
import sqlite3
import logging

class MenuModel:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path

    def store_menu(self, name, price, description, image_filename=None):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO menus (name, price, description, image)
            VALUES (?, ?, ?, ?)
        """, (name, price, description, image_filename))
        connection.commit()
        connection.close()

    def get_menu(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, price, description, image FROM menus")
        results = cursor.fetchall()
        connection.close()

        menu_items = []
        for row in results:
            item_id, name, price, description, image = row
            menu_items.append({
                "id": item_id,
                "name": name,
                "price": price,
                "description": description,
                "image": image
            })
        return menu_items

    def get_menu_by_id(self, item_id):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, name, price, description, image
            FROM menus WHERE id = ?
        """, (item_id,))
        result = cursor.fetchone()
        connection.close()

        if result:
            item_id, name, price, description, image = result
            return {
                "id": item_id,
                "name": name,
                "price": price,
                "description": description,
                "image": image
            }
        return None

    def update_menu(self, item_id, name, price, description, image_filename=None):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        if image_filename:
            cursor.execute("""
                UPDATE menus
                SET name=?, price=?, description=?, image=?
                WHERE id=?
            """, (name, price, description, image_filename, item_id))
        else:
            cursor.execute("""
                UPDATE menus
                SET name=?, price=?, description=?
                WHERE id=?
            """, (name, price, description, item_id))

        connection.commit()
        connection.close()

    def delete_menu(self, item_id):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM menus WHERE id=?", (item_id,))
        connection.commit()
        connection.close()
