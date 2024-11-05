import pyodbc  # Use pyodbc instead of mysql.connector for Azure SQL Database
import qrcode
from PIL import Image
from io import BytesIO
import time
import stripe

# Azure SQL Database configuration
db_config = {
    'server': 'tharidu.database.windows.net',
    'database': 'Tharidu',
    'username': 'tharidu',
    'password': 'PaskaL530@PMCmis',
}

# Stripe configuration
stripe.api_key = "sk_test_51PX3AWRo7edOoAU9mTe3shOEl3v9hEERW07fvXs4HieusRJ8xg597wsTBic9UYU5zB2ezg7tGOxFrZEfaKAAuHF900ZNiz5E16"
LOCAL_DOMAIN = "http://localhost:4242"

# Function to retrieve ticket information based on bus ID
def fetch_ticket_info(bus_id):
    try:
        # Connect to Azure SQL Database
        connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_config['server']};DATABASE={db_config['database']};UID={db_config['username']};PWD={db_config['password']}"
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        query = "SELECT Bus_ID, Bus_Number, Ticket_Price FROM Bus_Information_Table WHERE Bus_ID = ?"
        cursor.execute(query, (bus_id,))
        row = cursor.fetchone()

        # Check if row exists, then map it to a dictionary
        bus_info = {
            'Bus_ID': row.Bus_ID,
            'Bus_Number': row.Bus_Number,
            'Ticket_Price': row.Ticket_Price
        } if row else None

        cursor.close()
        connection.close()
        return bus_info

    except Exception as e:
        print(f"Error fetching ticket info: {e}")
        return None

# Generate Stripe Checkout session and return the session URL
def create_checkout_session(bus_info):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Bus Ticket for {bus_info['Bus_Number']}",
                    },
                    "unit_amount": int(bus_info['Ticket_Price']) * 100,  # Convert to cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=LOCAL_DOMAIN + "/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=LOCAL_DOMAIN + "/payment/cancel",
        )
        return session.url
    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        return None

# Generate QR code and display it in a popup window
def display_qr_code(bus_info):
    if not bus_info:
        print("No bus information found.")
        return

    # Create the Checkout session and get the URL
    session_url = create_checkout_session(bus_info)
    if not session_url:
        print("Failed to create Stripe session.")
        return

    # Create the QR code content
    qr = qrcode.make(session_url)

    # Display the QR code image without saving
    img_buffer = BytesIO()
    qr.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    img = Image.open(img_buffer)
    img.show()  # This should pop up the image in the default viewer

# Main function to run the Raspberry Pi script
def run_raspberry_pi_display(bus_id):
    while True:
        bus_info = fetch_ticket_info(bus_id)
        if bus_info:
            display_qr_code(bus_info)
        else:
            print(f"No information found for Bus ID {bus_id}. Retrying in 30 seconds...")
        time.sleep(3000)  # Refresh QR code every 30 seconds (adjust as needed)

# Example usage with a specified bus ID
if __name__ == "__main__":
    bus_id = "6"  # Set this to the unique ID for each bus
    run_raspberry_pi_display(bus_id)
