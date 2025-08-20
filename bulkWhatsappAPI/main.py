# whatsapp_bulk_app.py
# alias python=python3
# python3 -m venv path/to/venv     
# source path/to/venv/bin/activate
# pip install streamlit pandas requests
# streamlit run bulkWhatsappAPI/main.py
# pip install pyinstaller

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="WhatsApp Bulk Sender", layout="centered")

st.title("📲 WhatsApp Bulk Messaging App")

# Inputs for API setup
token = st.text_input("🔑 WhatsApp API Token", type="password")
phone_number_id = st.text_input("☎️ Phone Number ID")

# Message box
message = st.text_area("💬 Message to Send")

# CSV Upload
uploaded_file = st.file_uploader("📂 Upload CSV with contacts", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Detect possible name/phone columns
    name_col = None
    phone_col = None

    for col in df.columns:
        col_lower = col.lower()
        if "name" in col_lower:
            name_col = col
        if any(x in col_lower for x in ["phone", "mobile", "number"]):
            phone_col = col

    if not phone_col:
        st.error("❌ No phone number column found (expected column with Phone/Mobile/Number in name).")
    else:
        st.success(f"✅ Found phone column: {phone_col}")
        if name_col:
            st.info(f"ℹ️ Found name column: {name_col}")
        else:
            st.warning("⚠️ No name column found. Will send messages without personalization.")

        st.write("### Preview Contacts")
        st.dataframe(df[[c for c in [name_col, phone_col] if c]])

        if st.button("🚀 Send Messages"):
            if not token or not phone_number_id:
                st.error("Please enter both Token and Phone Number ID.")
            elif not message.strip():
                st.error("Please enter a message.")
            else:
                url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
                headers = {"Authorization": f"Bearer {token}"}
                results = []

                for _, row in df.iterrows():
                    phone = str(row[phone_col]).strip()
                    name = row[name_col] if name_col else ""
                    personalized_msg = message.replace("{name}", str(name))

                    payload = {
                        "messaging_product": "whatsapp",
                        "to": phone,
                        "type": "text",
                        "text": {"body": personalized_msg}
                    }
                    response = requests.post(url, json=payload, headers=headers)
                    results.append({"Phone": phone, "Status": response.status_code, "Response": response.json()})

                st.write("### Results")
                st.dataframe(pd.DataFrame(results))
                st.success("✅ Messages sent (check results table above).")
