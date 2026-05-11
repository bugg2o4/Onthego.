from flask import Flask, render_template, request, jsonify, session, redirect
import json
import os
import random
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.secret_key = "dev-secret-key"

def get_db():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="cs320",
        port="5432"
    )

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/checkout")
def checkout_page():
    return render_template("checkout.html")


@app.route("/products")
def products():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM products")
    data = cur.fetchall()

    db.close()

    for p in data:
        p["price"] = float(p["price"])

    return jsonify(data)


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    db = get_db()
    cur = db.cursor()

    try:
        cur.execute("""
    INSERT INTO users (name, email, password, role, business_name)
    VALUES (%s, %s, %s, %s, %s)
    """, (
        data["name"],
        data["email"],
        data["password"],
        data.get("role", "customer"),
        data.get("business_name")
        ))

        db.commit()

        session["user_email"] = data["email"]
        session["user_name"] = data["name"]

        return jsonify({"success": True})

    except psycopg2.IntegrityError:
        db.rollback()
        return jsonify({"success": False, "message": "Email already exists"})

    finally:
        db.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT id, name, email, role, business_name
        FROM users
        WHERE email=%s AND password=%s
    """, (data["email"], data["password"]))

    user = cur.fetchone()
    db.close()

    if not user:
        return jsonify({"success": False})

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["role"] = user["role"]
    session["business_name"] = user["business_name"]

    return jsonify({"success": True})

@app.route("/me")
def me():
    if "user_id" in session:
        return jsonify({
            "logged_in": True,
            "name": session.get("user_name"),
            "role": session.get("role")
        })

    return jsonify({"logged_in": False})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})

#Wishlist
@app.route("/wishlist/add", methods=["POST"])
def add_to_wishlist():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.json
    product_id = data["product_id"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO wishlist (user_email, product_id)
        VALUES (%s, %s)
        ON CONFLICT (user_email, product_id) DO NOTHING
    """, (session["user_email"], product_id))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/wishlist")
def get_wishlist():
    if "user_email" not in session:
        return jsonify([])

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.price, p.image
        FROM wishlist w
        JOIN products p ON w.product_id = p.id
        WHERE w.user_email = %s
    """, (session["user_email"],))

    items = cur.fetchall()
    db.close()

    return jsonify([
        {
            "id": i[0],
            "name": i[1],
            "price": float(i[2]),
            "image": i[3]
        }
        for i in items
    ])

@app.route("/wishlist/toggle", methods=["POST"])
def wishlist_toggle():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    product_id = request.json["product_id"]
    email = session["user_email"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT 1 FROM wishlist
        WHERE user_email = %s AND product_id = %s
    """, (email, product_id))

    exists = cur.fetchone()

    if exists:
        cur.execute("""
            DELETE FROM wishlist
            WHERE user_email = %s AND product_id = %s
        """, (email, product_id))
        action = "removed"
    else:
        cur.execute("""
            INSERT INTO wishlist (user_email, product_id)
            VALUES (%s, %s)
        """, (email, product_id))
        action = "added"

    db.commit()
    db.close()

    return jsonify({"success": True, "action": action})

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.json

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    INSERT INTO cart (user_email, product_id, quantity)
    VALUES (%s, %s, 1)
    ON CONFLICT (user_email, product_id)
    DO UPDATE SET quantity = cart.quantity + 1
""", (session["user_email"], data["product_id"]))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    if "user_email" not in session:
        return jsonify({"success": False})

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM cart WHERE user_email=%s", (session["user_email"],))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/cart/update", methods=["POST"])
def update_cart():
    if "user_email" not in session:
        return jsonify({"success": False})

    data = request.json
    product_id = data["product_id"]
    change = data["change"]

    db = get_db()
    cur = db.cursor()


    cur.execute("""
        UPDATE cart
        SET quantity = quantity + %s
        WHERE user_email = %s AND product_id = %s
        RETURNING quantity
    """, (change, session["user_email"], product_id))

    result = cur.fetchone()

    if result and result[0] <= 0:
        cur.execute("""
            DELETE FROM cart
            WHERE user_email = %s AND product_id = %s
        """, (session["user_email"], product_id))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    if "user_email" not in session:
        return jsonify({"success": False})

    data = request.json
    product_id = data["product_id"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        DELETE FROM cart
        WHERE user_email = %s AND product_id = %s
    """, (session["user_email"], product_id))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/cart")
def get_cart():
    if "user_email" not in session:
        return jsonify([])

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT p.id, p.name, p.price, p.image, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_email = %s
    """, (session["user_email"],))

    items = cur.fetchall()

    db.close()

    cart = []
    for item in items:
        cart.append({
            "id": item[0],
            "name": item[1],
            "price": float(item[2]),
            "image": item[3],
            "quantity": item[4]
        })

    return jsonify(cart)

@app.route("/check-session")
def check_session():
    if "user_email" in session:
        return jsonify({
            "logged_in": True,
            "name": session.get("user_name")
        })
    return jsonify({"logged_in": False})



@app.route("/checkout", methods=["POST"])
def checkout_post():
    email = session.get("user_email")

    if not email:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.json

    order_number = "ON-" + str(random.randint(100000, 999999))
    tracking_number = "TRK-" + str(random.randint(100000, 999999))

    order_time = datetime.now()

    eta_start = order_time + timedelta(days=3)
    eta_end = order_time + timedelta(days=5)

    estimated_delivery = eta_end

    db = get_db()
    cur = db.cursor()

    cur.execute("""
    INSERT INTO orders
    (user_email, items, total, order_number, tracking_number, status, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (
    email,
    json.dumps(data["items"]),
    data["total"],
    order_number,
    tracking_number,
    "Pending",
    datetime.now()
))

    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "order_number": order_number,
        "tracking_number": tracking_number,
        "order_time": order_time.strftime("%Y-%m-%d %H:%M"),
        "eta": f"{eta_start.strftime('%b %d')} - {eta_end.strftime('%b %d')}",
        "estimated_delivery": estimated_delivery.strftime("%Y-%m-%d")
    })

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()

    db.close()

    return render_template("product.html", product=product)

#ADMIN
@app.route("/admin")
def admin():
    if not session.get("user_id"):
        return redirect("/login")

    if session.get("role") not in ["admin", "business"]:
        return "Unauthorized", 403

    return render_template("admin.html")

import json

@app.route("/admin/products")
def admin_products():
    if not session.get("user_id"):
        return jsonify([])

    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    business = session.get("business_name")

    cur.execute("""
        SELECT id, name, price, image, category
        FROM products
        WHERE business_name = %s
        ORDER BY id DESC
    """, (business,))

    products = cur.fetchall()
    db.close()

    return jsonify(products)
@app.route("/admin/data")
def admin_data():
    if not session.get("user_id"):
        return jsonify({"error": "not logged in"})

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT order_number, user_email, total, items,
               tracking_number, status, created_at
        FROM orders
        ORDER BY id DESC
    """)

    orders_raw = cur.fetchall()

    orders = []
    total_earnings = 0

    pending = shipped = delivered = 0

    for o in orders_raw:
        order_number, user_email, total, items, tracking_number, status, created_at = o

        try:
            items_list = json.loads(items)
        except:
            items_list = []

        orders.append({
            "order_number": order_number,
            "tracking_number": tracking_number,
            "user": user_email,
            "total": float(total),
            "items": items_list,
            "status": status,
            "created_at": str(created_at)
        })

        total_earnings += float(total)

        if status == "Pending":
            pending += 1
        elif status == "Shipped":
            shipped += 1
        elif status == "Delivered":
            delivered += 1

    db.close()

    return jsonify({
        "earnings": total_earnings,
        "orders": orders,
        "analytics": {
            "total_orders": len(orders),
            "pending": pending,
            "shipped": shipped,
            "delivered": delivered,
            "avg_order": (total_earnings / len(orders)) if orders else 0
        }
    })

@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if session.get("role") not in ["admin", "business"]:
        return jsonify({"success": False, "message": "Unauthorized"})

    data = request.json

    try:
        db = get_db()
        cur = db.cursor()

        cur.execute("""
            INSERT INTO products (name, description, price, image, category, business_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get("name"),
            data.get("description"),
            float(data.get("price", 0)),
            data.get("image"),
            data.get("category"),
            session.get("business_name")
        ))

        db.commit()
        db.close()

        return jsonify({"success": True})

    except Exception as e:
        print("ADD PRODUCT ERROR:", e)
        return jsonify({"success": False, "message": str(e)})

@app.route("/admin/delete-product", methods=["POST"])
def delete_product():
    if session.get("role") not in ["admin", "business"]:
        return jsonify({"success": False})

    data = request.json
    business = session.get("business_name")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        DELETE FROM products
        WHERE id = %s AND business_name = %s
    """, (data["id"], business))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/admin/edit-product", methods=["POST"])
def edit_product():
    if session.get("role") not in ["admin", "business"]:
        return jsonify({"success": False})

    data = request.json
    business_name = session.get("business_name")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE products
        SET name = %s,
            description = %s,
            price = %s,
            image = %s
        WHERE id = %s AND business_name = %s
    """, (
        data["name"],
        data["description"],
        data["price"],
        data["image"],
        data["id"],
        business_name
    ))

    db.commit()
    db.close()

    return jsonify({"success": True})

@app.route("/admin/update-order-status", methods=["POST"])
def update_order_status():
    if session.get("role") not in ["admin", "business"]:
        return jsonify({"success": False})

    data = request.json

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE orders
        SET status = %s
        WHERE order_number = %s
    """, (data["status"], data["order_number"]))

    db.commit()
    db.close()

    return jsonify({"success": True})

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No file"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    return jsonify({
        "success": True,
        "url": f"/static/uploads/{filename}"
    })

@app.route("/orders")
def get_orders():
    if "user_email" not in session:
        return jsonify([])

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT order_number, total, tracking_number, status, created_at, items
        FROM orders
        WHERE user_email = %s
        ORDER BY id DESC
    """, (session["user_email"],))

    rows = cur.fetchall()
    db.close()

    orders = []

    for r in rows:

        raw_items = r[5]

        try:
            if isinstance(raw_items, str):
                items = json.loads(raw_items)
            else:
                items = raw_items or []
        except:
            items = []

        orders.append({
            "order_number": r[0],
            "total": float(r[1]),
            "tracking_number": r[2],
            "status": r[3],
            "created_at": str(r[4]),
            "items": items
        })

    return jsonify(orders)

@app.route("/order-history")
def order_history_page():
    return render_template("orders.html")

@app.route("/cancel-order", methods=["POST"])
def cancel_order():
    if "user_email" not in session:
        return jsonify({"success": False})

    data = request.json
    order_number = data["order_number"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE orders
        SET status = 'Cancelled'
        WHERE order_number = %s
        AND user_email = %s
        AND status != 'Delivered'
    """, (order_number, session["user_email"]))

    db.commit()
    db.close()

    return jsonify({"success": True})


@app.route("/reorder", methods=["POST"])
def reorder():
    if "user_email" not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.json
    order_number = data["order_number"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT items
        FROM orders
        WHERE order_number = %s
        AND user_email = %s
    """, (order_number, session["user_email"]))

    row = cur.fetchone()

    if not row:
        db.close()
        return jsonify({"success": False, "message": "Order not found"})

    items = json.loads(row[0]) if row[0] else []

    for item in items:
        cur.execute("""
            INSERT INTO cart (user_email, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_email, product_id)
            DO UPDATE SET quantity = cart.quantity + EXCLUDED.quantity
        """, (
            session["user_email"],
            item["id"],
            item.get("quantity", 1)
        ))

    db.commit()
    db.close()

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
