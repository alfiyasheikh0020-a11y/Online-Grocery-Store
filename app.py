from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        ssl_disabled=False
    )


@app.route("/")
def home():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")

    product_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        product_count=product_count
    )


@app.route("/products")
def products():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT product_name, price, stock
        FROM products
    """)

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "products.html",
        products=products
    )

@app.route("/categories")
def categories():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT category_id, category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "categories.html",
        categories=categories
    )

@app.route("/category/<int:category_id>")
def category_products(category_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT product_name, price, stock
        FROM products
        WHERE category_id = %s
        ORDER BY product_name
    """, (category_id,))

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "products.html",
        products=products
    )

@app.route("/profile")
def profile():

    connection = get_db_connection()
    cursor = connection.cursor()

    customer_email = request.args.get("email")

    if customer_email:

        cursor.execute("""
            SELECT
                customer_id,
                name,
                email,
                phone,
                address
            FROM customers
            WHERE email = %s
        """, (customer_email,))

    else:

        cursor.execute("""
            SELECT
                customer_id,
                name,
                email,
                phone,
                address
            FROM customers
            LIMIT 0
        """)

    customer = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "profile.html",
        customer=customer
    )

    customer = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "profile.html",
        customer=customer
    )

@app.route("/orders")
def orders():
    connection = get_db_connection()
    cursor = connection.cursor()

    customer_email = request.args.get("email")

    if customer_email:
        cursor.execute("""
            SELECT
                o.order_id,
                o.order_date,
                o.total_amount,
                o.status
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE c.email = %s
            ORDER BY o.order_id DESC
        """, (customer_email,))
    else:
        cursor.execute("""
            SELECT
                order_id,
                order_date,
                total_amount,
                status
            FROM orders
            ORDER BY order_id DESC
        """)

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "orders.html",
        orders=orders
    )

@app.route("/order_details/<int:order_id>")
def order_details(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            p.product_name,
            od.price,
            od.quantity,
            (od.price * od.quantity) AS subtotal
        FROM order_details od
        JOIN products p
            ON od.product_id = p.product_id
        WHERE od.order_id = %s
    """, (order_id,))

    items = cursor.fetchall()

    cursor.execute("""
        SELECT total_amount
        FROM orders
        WHERE order_id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    connection.close()

    total = order[0] if order else 0

    return render_template(
        "order_details.html",
        order_id=order_id,
        items=items,
        total=total
    )


@app.route("/cart")
def cart():

    return render_template("cart.html")


@app.route("/checkout")
def checkout():

    return render_template("checkout.html")

@app.route("/order_success")
def order_success():

    return render_template("order_success.html")


@app.route("/place_order", methods=["POST"])
def place_order():

    connection = None
    cursor = None

    try:

        data = request.get_json()

        customer_name = data["customer_name"]
        customer_email = data["customer_email"]
        customer_phone = data["customer_phone"]
        customer_address = data["customer_address"]
        payment_method = data["payment_method"]
        cart = data["cart"]

        if not cart:
            return jsonify({
                "success": False,
                "message": "Cart is empty!"
            })

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if customer already exists
        cursor.execute(
            "SELECT customer_id FROM customers WHERE email = %s",
            (customer_email,)
        )

        customer = cursor.fetchone()

        if customer:

            customer_id = customer[0]

            cursor.execute("""
                UPDATE customers
                SET name = %s,
                    phone = %s,
                    address = %s
                WHERE customer_id = %s
            """, (
                customer_name,
                customer_phone,
                customer_address,
                customer_id
            ))

        else:

            cursor.execute("""
                INSERT INTO customers
                (name, email, phone, address)
                VALUES (%s, %s, %s, %s)
            """, (
                customer_name,
                customer_email,
                customer_phone,
                customer_address
            ))

            customer_id = cursor.lastrowid


        # Calculate total from database prices
        total_amount = 0
        order_items = []

        for item in cart:

            product_name = item["name"]
            quantity = int(item["quantity"])

            cursor.execute("""
                SELECT product_id, price, stock
                FROM products
                WHERE product_name = %s
            """, (product_name,))

            product = cursor.fetchone()

            if not product:
                raise Exception(
                    f"Product '{product_name}' not found."
                )

            product_id = product[0]
            price = float(product[1])
            stock = product[2]

            if quantity > stock:
                raise Exception(
                    f"Not enough stock for {product_name}."
                )

            subtotal = price * quantity
            total_amount += subtotal

            order_items.append(
                (product_id, quantity, price)
            )


        # Create order
        cursor.execute("""
            INSERT INTO orders
            (customer_id, order_date, total_amount, status)
            VALUES (%s, %s, %s, %s)
        """, (
            customer_id,
            date.today(),
            total_amount,
            "Pending"
        ))

        order_id = cursor.lastrowid


        # Add order details and update stock
        for product_id, quantity, price in order_items:

            cursor.execute("""
                INSERT INTO order_details
                (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (
                order_id,
                product_id,
                quantity,
                price
            ))

            cursor.execute("""
                UPDATE products
                SET stock = stock - %s
                WHERE product_id = %s
            """, (
                quantity,
                product_id
            ))


        # Payment
        payment_status = "Pending"

        if payment_method != "Cash on Delivery":
            payment_status = "Paid"

        cursor.execute("""
            INSERT INTO payments
            (order_id, payment_date, amount,
             payment_method, payment_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            order_id,
            date.today(),
            total_amount,
            payment_method,
            payment_status
        ))


        connection.commit()

        return jsonify({
            "success": True,
            "order_id": order_id,
            "total": total_amount
        })


    except Exception as error:

        if connection:
            connection.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        })


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )