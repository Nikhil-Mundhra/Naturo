"""
Generate a vCard QR code + .vcf for:
Naturo Surfaces — Harish Mundhra (Director of Sales & Marketing)

How to use:
1) pip install qrcode[pil]
2) python make_vcard_qr.py
Outputs:
  - harish_mundhra.vcf
  - harish_mundhra_qr.png
"""

from textwrap import dedent
import qrcode

def esc(s: str) -> str:
    """
    vCard 3.0 escaping rules:
    - Backslash -> \\
    - Semicolon -> \;
    - Comma -> \,
    - Newline -> \n
    """
    return (
        s.replace("\\", "\\\\")
         .replace(";", r"\;")
         .replace(",", r"\,")
         .replace("\n", r"\n")
    )

org = "Naturo Surfaces"
full_name = "Harish Mundhra"
last_name, first_name = "Mundhra", "Harish"
title = "Director of Sales & Marketing"
website = "https://www.naturoindustries.com"
customer_care = "+919711604243"  # Customer Care
work_phone = "+919717246783"  # Work phone
personal_phone = "+919312064243"  # Personal phone


# Addresses (street, city/locality, region/state, postal, country, label)
head_office = (
    "79, Ground Floor, West Mukherjee Nagar",
    "New Delhi",
    "Delhi",
    "110009",
    "India",
    "Head Office\n79, Ground Floor, West Mukherjee Nagar, New Delhi, Delhi, 110009."
)
marketing_office = (
    "S3061, Akshar Business Park, Sector No. 25, Vashi",
    "Navi Mumbai",
    "Maharashtra",
    "400703",
    "India",
    "Marketing Office\nS3061, Akshar Business Park, Sector No. 25, Vashi, Navi Mumbai, Maharashtra 400703."
)
experience_center = (
    "Plot No. 1, Basement Floor, Desh Bandhu Gupta Rd, Bazar Sangatrashan, Chuna Mandi, Paharganj",
    "New Delhi",
    "Delhi",
    "110055",
    "India",
    "Experience Center\nPlot No. 1, Basement Floor, Desh Bandhu Gupta Rd, Bazar Sangatrashan, Chuna Mandi, Paharganj, New Delhi, Delhi 110055."
)

manufacturing_setups = [
    "Sonipat, Haryana",
    "Yamuna Nagar, Haryana",
    "Barelli, Uttar Pradesh",  # kept exactly as provided
]

# Build vCard 3.0 (widely supported by iOS/Android)
vcard = dedent(f"""\
    BEGIN:VCARD
    VERSION:3.0
    N:{esc(last_name)};{esc(first_name)};;;
    FN:{esc(full_name)}
    ORG:{esc(org)}
    TITLE:{esc(title)}
    TEL;TYPE=Customer Care,VOICE:{esc(customer_care)}
    TEL;TYPE=WORK,VOICE:{esc(work_phone)}
    TEL;TYPE=Personal,VOICE:{esc(personal_phone)}
    URL:{esc(website)}
    ADR;TYPE=Head Office;LABEL={esc(head_office[5])}:;;{esc(head_office[0])};{esc(head_office[1])};{esc(head_office[2])};{esc(head_office[3])};{esc(head_office[4])}
    ADR;TYPE=Marketing Office;LABEL={esc(marketing_office[5])}:;;{esc(marketing_office[0])};{esc(marketing_office[1])};{esc(marketing_office[2])};{esc(marketing_office[3])};{esc(marketing_office[4])}
    ADR;TYPE=Experience Center;LABEL={esc(experience_center[5])}:;;{esc(experience_center[0])};{esc(experience_center[1])};{esc(experience_center[2])};{esc(experience_center[3])};{esc(experience_center[4])}
    NOTE:{esc("Manufacturing Setups: \n" + ";\n".join(manufacturing_setups))}
    END:VCARD
""").strip()

# --- Write .vcf file (nice to share as a digital card) ---
vcf_path = "Harish_Mundhra.vcf"
with open(vcf_path, "w", encoding="utf-8") as f:
    f.write(vcard)

# --- Create QR code PNG from the vCard text ---
qr_img = qrcode.make(vcard)
qr_path = "/Users/nikhil/Downloads/Naturo Experience Center Paharganj/NS_VCard.png"
qr_img.save(qr_path)

print("Saved:", vcf_path, "and", qr_path)
