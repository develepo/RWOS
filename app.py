import os
import json
from flask import Flask, request, jsonify
import logging
import requests
from google.oauth2.service_account import Credentials
import gspread
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

WhatsappToken = os.getenv("WHATSAPP_TOKEN")
WhatsappPhoneID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
Kitchen_Whatsapp= os.getenv("KITCHEN_WHATSAPP_NUMBER")
GSJ = os.getenv("GOOGLE_CREDENTIALS_JSON")
GoogleSheetID = os.getenv("GOOGLE_SHEET_ID")

req_vars = {
    "WHATSAPP_TOKEN": WhatsappToken,
    "WHATSAPP_PHONE_NUMBER_ID": WhatsappPhoneID,
    "VERIFY_TOKEN": VERIFY_TOKEN,
    "KITCHEN_WHATSAPP_NUMBER": Kitchen_Whatsapp,
    "GOOGLE_CREDENTIALS_JSON": GSJ,
    "GOOGLE_SHEET_ID": GoogleSheetID,
}

for name, value in req_vars.items():
    if not value:
        logger.warning(f"Missing {name}")

MENU = {
    1: {"name": "Biryani", "price": 200},
    2: {"name": "Butter Chicken", "price": 180},
    3: {"name": "Dal Makhani", "price": 150},
}

SESSION = {}

def get_session(phone):

    if phone not in SESSION:

        SESSION[phone] = {
    "state": None,
    "table_number": None,
    "customer_name": None,
    "order_items": {},
    "special_instructions": None,
}

    return SESSION[phone]

def clear_session(phone):

    if phone in SESSION:
        del SESSION[phone]

def send_whatsapp_message(recipient_phone, message_txt):
    try:
        url = f"https://graph.facebook.com/v20.0/{WhatsappPhoneID}/messages"
        headers = {
            "Authorization": f"Bearer {WhatsappToken}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"preview_url": False, "body": message_txt},
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        logger.info(f"Message sent to {recipient_phone}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f" Failed to send message to {recipient_phone}: {e}")
        return False
def format_menu():
    menu_text = " *MENU*\n\n"
    for item_id, item in MENU.items():
        menu_text += f"{item_id}. {item['name']} - ₹{item['price']}\n"
    menu_text += "\n *Send your order like this:*\n1x2, 3x1\n(means: 2x Biryani, 1x Butter Chicken)"
    return menu_text
def parse_order(message_txt):
    parsed_items = {}
    errors = []
    
    message_txt = message_txt.replace(" ", "").upper()
    
    items = message_txt.split(",")
    
    for item in items:
        try:
            if 'X' not in item:
                errors.append(f"Invalid format: {item}. Use format: ItemNumberxQuantity")
                continue
                
            item_id_str, qty_str = item.split('X')
            item_id = int(item_id_str)
            quantity = int(qty_str)
            if item_id not in MENU:
                errors.append(f"Item {item_id} not in menu")
                continue
                

            if quantity <= 0:
                errors.append(f"Quantity for item {item_id} must be positive")
                continue
                
            parsed_items[item_id] = parsed_items.get(item_id, 0) + quantity
            
        except ValueError:
            errors.append(f"Invalid format: {item}. Use numbers only")
            
    if not parsed_items and not errors:
        errors.append("No valid items found. Please try again.")
        
    return parsed_items, errors
def format_order_summary(order_items, special_instructions=None):
    total_price = 0
    summary = " *ORDER SUMMARY*\n\n"
    
    for item_id, quantity in order_items.items():
        item = MENU[item_id]
        item_total = item['price'] * quantity
        total_price += item_total
        summary += f"• {quantity}x {item['name']} - ₹{item_total}\n"
    
    summary += f"\n *Total: ₹{total_price}*"
    
    if special_instructions:
        summary += f"\n *Special Instructions:* {special_instructions}"
    
    summary += "\n\nConfirm your order? Reply *YES* or *NO*"
    
    return summary, total_price
def format_kitchen_message(table_number, customer_name, customer_phone, order_items, special_instructions, total_price):
    kitchen_msg = "🔔 *NEW ORDER ALERT!*\n\n"
    kitchen_msg += f" *Table:* {table_number}\n"
    kitchen_msg += f"*Customer:* {customer_name}\n"
    kitchen_msg += f" *Phone:* {customer_phone}\n\n"
    kitchen_msg += "*ORDER DETAILS:*\n"
    
    for item_id, quantity in order_items.items():
        item = MENU[item_id]
        kitchen_msg += f"• {quantity}x {item['name']}\n"
    
    if special_instructions:
        kitchen_msg += f"\n*Special Instructions:* {special_instructions}"
    
    kitchen_msg += f"\n*Total: ₹{total_price}*"
    kitchen_msg += "\n *Please prepare ASAP!*"
    
    return kitchen_msg

def append_order_to_sheets(order_data):
    """
    Append order to Google Sheets for record keeping
    """
    try:
        credentials_dict = json.loads(GSJ)
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(GoogleSheetID).sheet1
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row_data = [
            timestamp,
            order_data.get("customer_name", "Unknown"),
            order_data.get("customer_phone", "Unknown"),
            order_data.get("table_number", "Unknown"),
            order_data.get("order_items_text", "None"),
            order_data.get("special_instructions", "None"),
            order_data.get("total_price", 0)
        ]
        
        # Append to sheet
        sheet.append_row(row_data)
        logger.info(f"Order appended to Google Sheets successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to append to Google Sheets: {e}")
        return False
    

def message_handler(phone, message_txt):
    session = get_session(phone)
    message_txt = message_txt.strip()
    logger.info(f"Message from {phone}: {message_txt} | State: {session['state']}")
    if session["state"] is None:
        if message_txt.upper().startswith("ORDER TABLE"):
            try:
                table_number = int(message_txt.split()[-1])
                session["table_number"] = table_number
                session["state"] = "ask_name"

                response = f" Welcome to Table {table_number}!\n\nWhat's your name?"
                send_whatsapp_message(phone, response)
                logger.info(f"Table {table_number} detected for {phone}")
            except (ValueError, IndexError):
                response = " Could not detect table number. Please scan the QR code again"
                send_whatsapp_message(phone, response)
        else:
            response = " Welcome! Please scan the table QR code"
            send_whatsapp_message(phone, response)
    elif session["state"] == "ask_name":
     session["customer_name"] = message_txt
     session["state"] = "ask_order" 
     send_whatsapp_message(phone, format_menu())
     logger.info(f"Customer name set: {message_txt} for {phone}")  
    elif session["state"] == "ask_order":
        parsed_items, errors = parse_order(message_txt)

        if errors:
            error_response = " *ORDER ERROR*\n\n" + "\n".join(errors)
            error_response += "\n\nPlease try again. Format: 1x2, 3x1, 4x2"
            send_whatsapp_message(phone, error_response)
            logger.warning(f"Order parsing errors for {phone}: {errors}")
            return
        if not parsed_items:
         send_whatsapp_message(phone, "Please enter at least one valid item to order.\n\nFormat: 1x2, 3x1, 2x1")
         return

        session["order_items"] = parsed_items
        session["state"] = "ask_special_instructions"

        response = "👍 Order received!\n\nAny special instructions? (allergies, extra salt, no onions, etc.)\n\nOr reply *NONE* to skip."
        send_whatsapp_message(phone, response)
        logger.info(f"Order parsed for {phone}: {parsed_items}")

    elif session["state"] == "ask_special_instructions":
        if message_txt.upper() == "NONE":
            session["special_instructions"] = None
        else:
            session["special_instructions"] = message_txt

        session["state"] = "confirm_order"
        
        summary, total_price = format_order_summary(
            session["order_items"],
            session["special_instructions"]
        )
        send_whatsapp_message(phone, summary)
        logger.info(f"Special instructions set for {phone}: {session['special_instructions']}")  

    elif session["state"] == "confirm_order":
        response_upper = message_txt.upper()

        if response_upper == "YES":
        
            _, total_price = format_order_summary(
                session["order_items"],
                session["special_instructions"]
            )
            kitchen_message = format_kitchen_message(
                session["table_number"],
                session["customer_name"],
                phone,
                session["order_items"],
                session["special_instructions"],
                total_price,
            )
            send_whatsapp_message(Kitchen_Whatsapp, kitchen_message)
            logger.info(f"Kitchen notified for order from {phone}")

            order_data = {
                "customer_phone": phone,
                "customer_name": session["customer_name"],
                "table_number": session["table_number"],
                "order_items_text": ", ".join(
                    [f"{session['order_items'][i]}x {MENU[i]['name']}" for i in session["order_items"]]
                ),
                "special_instructions": session["special_instructions"] or "None",
                "total_price": total_price,
            }
            append_order_to_sheets(order_data)

            # Confirm to customer
            confirmation = f" *ORDER CONFIRMED!*\n\n Your order is being prepared.\n Total: ₹{total_price}\n\n Thank you! Order will be ready soon."
            send_whatsapp_message(phone, confirmation)

            session["state"] = "done"
            logger.info(f"Order confirmed and saved for {phone}")

        elif response_upper == "NO":

            response = "Order cancelled. Thank you for visiting!"
            send_whatsapp_message(phone, response)

            clear_session(phone)
            logger.info(f"Order cancelled for {phone}")

        else:
            response = "Please reply *YES* to confirm or *NO* to cancel."
            send_whatsapp_message(phone, response)

    elif session["state"] == "done":
        response = "Your order has already been confirmed. Enjoy your meal!"
        send_whatsapp_message(phone, response)    
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status":"ok",
        "message":"RWOS is running"
    })

@app.route("/webhook", methods=["GET"])
def webhook_VERIFY_TOKEN():
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge, 200
    else:
        logger.warning(" Webhook VERIFY_TOKEN failed")
        return "Forbidden", 403
    

@app.route("/webhook", methods=["POST"])    
def webhook_recieve():
    try:
        data = request.get_json()
        logger.debug(f"Webhook received: {json.dumps(data, indent=2)}")
        if 'entry' in data:
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if 'value' in change and 'messages' in change['value']:
                            for message in change['value']['messages']:
                                # Only process text messages
                                if message.get('type') == 'text':
                                    phone = message.get('from')
                                    message_txt = message.get('text', {}).get('body', '').strip()
                                    if phone and message_txt:
                                        logger.info(f"Incoming message from {phone}: {message_txt}")
                                        message_handler(phone, message_txt)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    logger.info(" Starting RWOS (Restaurant WhatsApp Ordering System)")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)