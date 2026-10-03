let savedCart = JSON.parse(localStorage.getItem("cart")) || [];
let cart = Array.isArray(savedCart) ? savedCart : [];


function addToCart(name, price, stock) {

    const existingProduct = cart.find(function(item) {
        return item.name === name;
    });


    if (existingProduct) {

        if (existingProduct.quantity < stock) {
            existingProduct.quantity++;
        }

        else {
            alert("Sorry, stock limit reached!");
            return;
        }

    }

    else {

        cart.push({
            name: name,
            price: Number(price),
            quantity: 1,
            stock: Number(stock)
        });

    }


    localStorage.setItem("cart", JSON.stringify(cart));

    alert(name + " added to cart! 🛒");
}



function displayCart() {

    const cartItems = document.getElementById("cart-items");

    const cartTotal = document.getElementById("cart-total");


    if (!cartItems || !cartTotal) {
        return;
    }


    if (cart.length === 0) {

        cartItems.innerHTML =
            "<p>Your cart is empty. 🛒</p>";

        cartTotal.innerText =
            "Total: ₹0";

        return;
    }


    let total = 0;

    cartItems.innerHTML = "";


    cart.forEach(function(item, index) {

        const itemTotal =
            item.price * item.quantity;

        total += itemTotal;


        const cartItem =
            document.createElement("div");

        cartItem.className =
            "cart-item";


        cartItem.innerHTML =

            "<h3>" +
            item.name +
            "</h3>" +

            "<p>Price: ₹" +
            item.price +
            "</p>" +

            "<div>" +

            "<button onclick=\"decreaseQuantity(" +
            index +
            ")\">−</button>" +

            "<span> " +
            item.quantity +
            " " +
            "</span>" +

            "<button onclick=\"increaseQuantity(" +
            index +
            ")\">+</button>" +

            "</div>" +

            "<p>Subtotal: ₹" +
            itemTotal +
            "</p>" +

            "<button onclick=\"removeFromCart(" +
            index +
            ")\">Remove</button>";


        cartItems.appendChild(cartItem);

    });


    cartTotal.innerText =
        "Total: ₹" + total;
}



function increaseQuantity(index) {

    const item = cart[index];


    if (item.quantity < item.stock) {

        item.quantity++;

        localStorage.setItem(
            "cart",
            JSON.stringify(cart)
        );

        displayCart();

        displayCheckoutTotal();

    }

    else {

        alert("Sorry, stock limit reached!");

    }

}



function decreaseQuantity(index) {

    const item = cart[index];


    if (item.quantity > 1) {

        item.quantity--;

    }

    else {

        cart.splice(index, 1);

    }


    localStorage.setItem(
        "cart",
        JSON.stringify(cart)
    );


    displayCart();

    displayCheckoutTotal();

}



function removeFromCart(index) {

    cart.splice(index, 1);


    localStorage.setItem(
        "cart",
        JSON.stringify(cart)
    );


    displayCart();

    displayCheckoutTotal();

}



function displayCheckoutTotal() {

    const checkoutTotal =
        document.getElementById("checkout-total");


    if (!checkoutTotal) {
        return;
    }


    let total = 0;


    cart.forEach(function(item) {

        total +=
            item.price * item.quantity;

    });


    checkoutTotal.innerText =
        "Total: ₹" + total;

}



function checkout() {

    if (cart.length === 0) {

        alert("Your cart is empty!");

        return;
    }


    window.location.href =
        "/checkout";

}



async function placeOrder(event) {

    event.preventDefault();


    if (cart.length === 0) {

        alert("Your cart is empty!");

        return;
    }


    const customerName =
        document.getElementById(
            "customer-name"
        ).value;


    const customerEmail =
        document.getElementById(
            "customer-email"
        ).value;


    const customerPhone =
        document.getElementById(
            "customer-phone"
        ).value;


    const customerAddress =
        document.getElementById(
            "customer-address"
        ).value;


    const selectedPayment =
        document.querySelector(
            'input[name="payment_method"]:checked'
        );


    if (!selectedPayment) {

        alert(
            "Please select a payment method."
        );

        return;
    }


    let paymentMethod =
        selectedPayment.value;


    if (paymentMethod === "UPI") {

        const selectedUPI =
            document.querySelector(
                'input[name="upi-app"]:checked'
            );


        if (!selectedUPI) {

            alert(
                "Please select a UPI app."
            );

            return;
        }


        paymentMethod =
            selectedUPI.value;

    }


    const orderData = {

        customer_name:
            customerName,

        customer_email:
            customerEmail,

        customer_phone:
            customerPhone,

        customer_address:
            customerAddress,

        payment_method:
            paymentMethod,

        cart:
            cart

    };


    try {

        const response =
            await fetch(
                "/place_order",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(orderData)
                }
            );


        const result =
            await response.json();


        if (result.success) {

    localStorage.setItem(
        "customerEmail",
        customerEmail
    );

    localStorage.setItem(
        "lastOrderId",
        result.order_id
    );

    localStorage.setItem(
        "lastOrderTotal",
        result.total
    );

    localStorage.setItem(
        "lastPaymentMethod",
        paymentMethod
    );

    cart = [];

    localStorage.removeItem(
        "cart"
    );

    window.location.href =
        "/order_success";
    }

        else {

            alert(
                "Order failed ❌\n\n" +
                result.message
            );

        }

    }


    catch (error) {

        alert(
            "Something went wrong while placing the order."
        );

        console.error(error);

    }

}



displayCart();

displayCheckoutTotal();