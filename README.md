# RWOS - Restaurant WhatsApp Ordering System

A rule-based WhatsApp ordering bot for restaurants. Customers will scan a table QR code, place orders, and the kitchen gets notified via Whatsapp.

## Features

 **Table-based ordering** - Customer scans QR code with table number  
**Conversational flow** - Simple step-by-step ordering  
**Order parsing** - Format: "1x2, 3x1, 4x2" (2x Biryani, 1x Butter Chicken, 1x Dal Makhani)  
**Validation** - Catches invalid items and quantities  
 **Special instructions** - Allergies, preferences, etc.  
 **Kitchen notifications** - WhatsApp order alerts  
 **In-memory sessions** - No database needed  

## Tech Stack

- **Framework**: Flask
- **Messaging**: Meta WhatsApp Business Cloud API
- **Logging**: Google Sheets API
- **Language**: Python 3.9+

## Prerequisites

Before you start, you'll need:

1. **Meta WhatsApp Business Account**
   - WhatsApp Business API access token
   - Phone number ID
   - Verified business phone number

2. **Google Cloud Project**
   - Service account with Sheets API enabled
   - JSON key file for authentication

3. **Deployment Platform**
   - Railway account (or any platform supporting Python/Gunicorn)

## Local Setup

### 1. Clone and Install

```bash
git clone "https://github.com/develepo/RWOS"
cd rwos
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
WHATSAPP_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_id_here
VERIFY_TOKEN=your_random_verify_token
KITCHEN_WHATSAPP_NUMBER=919876543210
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_SHEET_ID=your_sheet_id
```

### 3. Run Locally

```bash
python app.py
```

The app will start on `http://localhost:5000`.

Test the health endpoint:
```bash
curl http://localhost:5000/
```

## Deployment to Railway

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial RWOS commit"
git push origin main
```

### 2. Connect to Railway

1. Go to [Railway.app](https://railway.app)
2. Click **"Create Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account and select this repository
5. Railway will auto-detect the `Procfile`

### 3. Set Environment Variables

In Railway dashboard:
1. Go to your project
2. Click **"Variables"**
3. Add all variables from `.env.example`:
   - `WHATSAPP_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `VERIFY_TOKEN`
   - `KITCHEN_WHATSAPP_NUMBER`
   - `GOOGLE_CREDENTIALS_JSON`
   - `GOOGLE_SHEET_ID`

### 4. Get Your Webhook URL

After deployment:
1. Railway assigns a public URL to your app (e.g., `https://rwos-prod.railway.app`)
2. Your webhook endpoint is: `https://rwos-prod.railway.app/webhook`

## Meta WhatsApp Setup

### 1. Create WhatsApp Business App

1. Go to [Meta App Dashboard](https://developers.facebook.com)
2. Create a new app → Business
3. Add **WhatsApp** product
4. Get your **Access Token** and **Phone Number ID**

### 2. Configure Webhook

In Meta App Dashboard → WhatsApp → Configuration:

1. **Webhook URL**: `https://your-railway-url.railway.app/webhook`
2. **Verify Token**: Use the same token from your `.env` `VERIFY_TOKEN`
3. **Subscribe to**: `messages`, `message_status`

### 3. Create QR Code Link

Format:
```
https://wa.me/YOUR_PHONE_NUMBER?text=ORDER%20TABLE%205
```

Example (for phone number +91-9876-543210):
```
https://wa.me/919876543210?text=ORDER%20TABLE%205
```

Generate different links for each table:
- Table 1: `https://wa.me/919876543210?text=ORDER%20TABLE%201`
- Table 2: `https://wa.me/919876543210?text=ORDER%20TABLE%202`
- Table 5: `https://wa.me/919876543210?text=ORDER%20TABLE%205`

Use a QR code generator to convert these links to QR codes and print them for each table.

## Google Sheets Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Sheets API**

### 2. Create Service Account

1. Go to **Service Accounts** → **Create Service Account**
2. Fill in details (e.g., name: "rwos-bot")
3. Grant **Editor** role
4. Create a **JSON key** → Download it

### 3. Create Google Sheet

1. Create a new Google Sheet
2. Share it with the service account email (found in JSON key file)
3. Get the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```

### 4. Set Up Sheet Structure

Create a header row in your Google Sheet:

| Timestamp | Phone | Name | Table | Items | Special Instructions | Total |
|-----------|-------|------|-------|-------|----------------------|-------|
| 2024-01-15 14:30:00 | 919876543210 | Farhan | 5 | 2x Biryani, 1x Butter Chicken | No onions | 580 |

The app will append rows automatically.

### 5. Add to Environment

Copy the entire JSON key file content to `GOOGLE_CREDENTIALS_JSON`:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  ...
}
```

## Usage Flow

### Customer Side

1. **Scan table QR code** → WhatsApp opens with "ORDER TABLE 5"
2. **Bot asks for name** → Customer replies "Farhan"
3. **Bot sends menu** → Numbered list of items with prices
4. **Customer sends order** → "1x2, 3x1, 4x2"
5. **Bot asks for special instructions** → "No onions, extra butter"
6. **Bot shows order summary** → Total price and items
7. **Customer confirms** → Replies "YES" or "NO"
8. **Order confirmed** → Notification sent to kitchen

### Kitchen Side

1. **Receives WhatsApp notification** → New order alert with:
   - Table number
   - Customer name & phone
   - Items and quantities
   - Special instructions
   - Order total
   - Time of order

### Manager Side

1. **Open Google Sheet** → All orders logged in real-time
2. **Track volume** → See daily/hourly order patterns
3. **Analyze revenue** → Total price column tracks sales

## Menu Customization

Edit the `MENU` dictionary in `app.py`:

```python
MENU = {
    1: {"name": "Biryani", "price": 200},
    2: {"name": "Butter Chicken", "price": 180},
    3: {"name": "Dal Makhani", "price": 150},
    # Add more items...
}
```

Then redeploy:

```bash
git add .
git commit -m "Updated menu"
git push origin main
```

Railway will auto-redeploy.

## Logging

The app logs all events to console:

```
2024-01-15 14:30:00 - app - INFO - Message from 919876543210: ORDER TABLE 5 | State: None
2024-01-15 14:30:05 - app - INFO - Table 5 detected for 919876543210
2024-01-15 14:30:08 - app - INFO - Customer name set: Farhan for 919876543210
2024-01-15 14:30:15 - app - INFO - Order parsed for 919876543210: {1: 2, 3: 1, 4: 2}
2024-01-15 14:30:20 - app - INFO - ✓ Message sent to 919876543210
2024-01-15 14:30:45 - app - INFO - Kitchen notified for order from 919876543210
2024-01-15 14:30:45 - app - INFO - Order saved to Google Sheets
```

In Railway, view logs in the **Logs** tab of your project.

## Conversation States

The bot uses an in-memory state machine:

```
None (Initial)
  ↓
ask_name (Waiting for customer name)
  ↓
send_menu (Show menu)
  ↓
ask_order (Parse order format)
  ↓
ask_special_instructions (Optional custom notes)
  ↓
confirm_order (YES/NO confirmation)
  ↓
done (Order complete)
```

Sessions are stored in a Python dictionary (`SESSIONS`) and cleared when the order is completed or cancelled.

## Order Parser

Accepts format: `ItemID x Quantity, ItemID x Quantity`

Examples:
- ✅ `1x2, 3x1` → 2x Biryani, 1x Dal Makhani
- ✅ `5x3` → 3x Garlic Naan
- ❌ `1 2` → Invalid format
- ❌ `10x2` → Item 10 doesn't exist
- ❌ `1x0` → Quantity must be > 0
- ❌ `1x15` → Quantity capped at 10

## Validation

The bot validates:

1. **Table number** → Must be detected from QR code
2. **Customer name** → Any non-empty text
3. **Order format** → `ItemID x Quantity` pattern
4. **Item IDs** → Must exist in menu
5. **Quantities** → Must be 1-10
6. **Confirmation** → Must be YES or NO

## Error Handling

The app gracefully handles:

- Missing environment variables (warns in logs)
- Invalid JSON from webhook (logs and continues)
- Failed WhatsApp message sends (logs error, continues)
- Google Sheets API failures (logs error, order still confirmed to customer)
- Malformed order format (asks customer to retry)

All errors are logged but don't crash the app.

## Scaling Notes

**In-memory sessions**: Sessions are stored in RAM. If the app restarts or scales to multiple workers, sessions are lost. For production with high volume:

1. Use Railway's single-worker setup (as configured)
2. Or implement Redis for distributed sessions
3. Or use a lightweight database (SQLite, PostgreSQL)

Current setup handles ~100-500 concurrent conversations per minute without issues.

## Troubleshooting

### Webhook not receiving messages

1. Check webhook URL is correct in Meta dashboard
2. Check VERIFY_TOKEN matches in both places
3. Check app is deployed and accessible (curl the URL)
4. Check logs in Railway for errors

### Messages not sending to WhatsApp

1. Verify `WHATSAPP_TOKEN` is valid (tokens expire)
2. Verify `WHATSAPP_PHONE_NUMBER_ID` is correct
3. Check phone number format (country code + number, no +)
4. Check logs for API errors

### Orders not saving to Google Sheets

1. Verify service account email is shared on the sheet
2. Verify `GOOGLE_SHEET_ID` is correct
3. Verify `GOOGLE_CREDENTIALS_JSON` is properly formatted
4. Check logs for authentication errors

### Orders not reaching kitchen

1. Verify `KITCHEN_WHATSAPP_NUMBER` is correct and formatted properly
2. Add kitchen number as a contact in the WhatsApp Business Account
3. Check logs to confirm kitchen message is being sent

## File Structure

```
rwos/
├── app.py                 # Main Flask app (single file)
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── Procfile              # Railway deployment config
├── README.md             # This file
└── .gitignore            # (Recommended: ignore .env, venv/)
```

## Recommended .gitignore

```
.env
venv/
__pycache__/
*.pyc
.DS_Store
.idea/
.vscode/
instance/
*.log
```

## Future Enhancements

Ideas for extending RWOS:

-  Dashboard for order analytics
-  Payment integration (Razorpay, Stripe)
-  SMS fallback for delivery updates
-  Mobile app for kitchen staff
-  AI for popular item recommendations
-  Delivery radius calculator
-  Customer ratings and feedback

## License

MIT - Feel free to fork and modify!

## Support

For questions or issues:

1. Check the **Troubleshooting** section
2. Review logs in Railway dashboard
3. Verify all environment variables are set
4. Test webhook URL with `curl` command

# Contact

Discod - @develepo

---

**Built with ❤️ by Tapaiz for restaurants that want to scale.**
