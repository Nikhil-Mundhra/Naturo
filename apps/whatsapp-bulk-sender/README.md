# WhatsApp Bulk Sender

A Streamlit web application to send personalized bulk WhatsApp messages via Meta Graph API.

## Features
- CSV contact upload with auto-detection of name and phone number columns.
- Message templating with `{name}` dynamic replacement.
- Direct integration with Meta Cloud API.
- Real-time delivery status and response logging.

## Quick Start

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Application
```bash
streamlit run app.py
```

### 3. Packaging as Desktop App
```bash
pyinstaller packaging/main.spec
```
