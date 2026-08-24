from flask import Flask, flash, redirect, render_template, request, url_for
from dotenv import load_dotenv
import pyodbc
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DRIVER = os.getenv("DB_DRIVER")


def get_db_connection():
    conn = pyodbc.connect(
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return conn


def init_database():
    """Create the application's starter table when it does not exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('dbo.products', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.products (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(150) NOT NULL,
                    price DECIMAL(12,2) NOT NULL CHECK (price >= 0),
                    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
                    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
                )
            END
            """
        )
        conn.commit()
    finally:
        conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if search:
            products = cursor.execute(
                "SELECT id, name, price, quantity, created_at FROM dbo.products "
                "WHERE name LIKE ? ORDER BY id DESC",
                f"%{search}%",
            ).fetchall()
        else:
            products = cursor.execute(
                "SELECT id, name, price, quantity, created_at "
                "FROM dbo.products ORDER BY id DESC"
            ).fetchall()
        return render_template("index.html", products=products, search=search)
    finally:
        conn.close()


@app.post("/products")
def add_product():
    name = request.form.get("name", "").strip()
    try:
        price = float(request.form.get("price", ""))
        quantity = int(request.form.get("quantity", ""))
        if not name or price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        flash("กรุณากรอกชื่อ ราคา และจำนวนให้ถูกต้อง", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        conn.cursor().execute(
            "INSERT INTO dbo.products (name, price, quantity) VALUES (?, ?, ?)",
            name,
            price,
            quantity,
        )
        conn.commit()
    finally:
        conn.close()
    flash("เพิ่มสินค้าเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


@app.post("/products/<int:product_id>/edit")
def edit_product(product_id):
    name = request.form.get("name", "").strip()
    try:
        price = float(request.form.get("price", ""))
        quantity = int(request.form.get("quantity", ""))
        if not name or price < 0 or quantity < 0:
            raise ValueError
    except ValueError:
        flash("ข้อมูลสินค้าไม่ถูกต้อง", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        conn.cursor().execute(
            "UPDATE dbo.products SET name = ?, price = ?, quantity = ? WHERE id = ?",
            name,
            price,
            quantity,
            product_id,
        )
        conn.commit()
    finally:
        conn.close()
    flash("แก้ไขสินค้าเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


@app.post("/products/<int:product_id>/delete")
def delete_product(product_id):
    conn = get_db_connection()
    try:
        conn.cursor().execute("DELETE FROM dbo.products WHERE id = ?", product_id)
        conn.commit()
    finally:
        conn.close()
    flash("ลบสินค้าเรียบร้อยแล้ว", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
