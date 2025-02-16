import sqlite3
import bcrypt

class UserModel:
    def __init__(self):
        self.conn = sqlite3.connect("database.db", check_same_thread=False)
        self.create_user_table()

    def create_user_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def create_user(self, email, password, role="staff"):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        query = "INSERT INTO users (email, password, role) VALUES (?, ?, ?)"
        self.conn.execute(query, (email, hashed_password, role))
        self.conn.commit()

    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        return cursor.fetchone()

    def authenticate_user(self, email, password):
        query = "SELECT * FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
            return {"email": user[1], "role": user[3]}
        return None

    def update_user(self, email, password=None, role=None):
        updates = []
        params = []

        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            updates.append("password = ?")
            params.append(hashed_password)
        if role:
            updates.append("role = ?")
            params.append(role)

        params.append(email)
        query = f"UPDATE users SET {', '.join(updates)} WHERE email = ?"
        self.conn.execute(query, params)
        self.conn.commit()

    def delete_user(self, email):
        query = "DELETE FROM users WHERE email = ?"
        self.conn.execute(query, (email,))
        self.conn.commit()

    def get_all_users(self):
        query = "SELECT id, email, role FROM users"
        cursor = self.conn.execute(query)
        return [{"id": row[0], "email": row[1], "role": row[2]} for row in cursor.fetchall()]

    def get_users_by_role(self, role):
        query = "SELECT id, email FROM users WHERE role = ?"
        cursor = self.conn.execute(query, (role,))
        return [{"id": row[0], "email": row[1]} for row in cursor.fetchall()]

    def does_email_exist(self, email):
        query = "SELECT 1 FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        return cursor.fetchone() is not None

    def is_admin(self, email):
        query = "SELECT role FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        user = cursor.fetchone()
        return user and user[0] == "admin"

    def is_staff(self, email):
        query = "SELECT role FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        user = cursor.fetchone()
        return user and user[0] == "staff"

    def reset_password(self, email, new_password):
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        query = "UPDATE users SET password = ? WHERE email = ?"
        self.conn.execute(query, (hashed_password, email))
        self.conn.commit()

    def set_role(self, email, role):
        query = "UPDATE users SET role = ? WHERE email = ?"
        self.conn.execute(query, (role, email))
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ----------------------------------------------------
    #           THÊM MỚI: CÁC HÀM HỖ TRỢ USER MGMT
    # ----------------------------------------------------

    def get_user_dict_by_email(self, email):
        """
        Lấy thông tin user (id, email, password, role)
        dạng dict, tiện cho việc hiển thị template.
        """
        query = "SELECT id, email, password, role FROM users WHERE email = ?"
        cursor = self.conn.execute(query, (email,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "email": row[1],
                "password": row[2],
                "role": row[3]
            }
        return None

    def update_user_role(self, email, new_role):
        """
        Chỉ cập nhật role cho user dựa trên email.
        (khác hàm update_user phía trên để dùng riêng)
        """
        query = "UPDATE users SET role = ? WHERE email = ?"
        self.conn.execute(query, (new_role, email))
        self.conn.commit()
