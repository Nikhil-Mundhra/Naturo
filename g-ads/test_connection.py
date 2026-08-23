"""Verify Google Ads credentials and list accounts visible to the login user."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing {name}; fill it in .env first.")
    return value


def main() -> None:
    client = GoogleAdsClient.load_from_dict(
        {
            "developer_token": required("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": required("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": required("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": required("GOOGLE_ADS_REFRESH_TOKEN"),
            "login_customer_id": required("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "use_proto_plus": True,
        }
    )

    customer_service = client.get_service("CustomerService")
    login_customer_id = os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
    resource_names = customer_service.list_accessible_customers(
        login_customer_id=login_customer_id
    )

    print("Accessible customer accounts:")
    for resource_name in resource_names.resource_names:
        print(f"- {resource_name.rsplit('/', 1)[-1]}")


if __name__ == "__main__":
    try:
        main()
    except GoogleAdsException as error:
        raise SystemExit(f"Google Ads API error: {error.failure.errors[0].message}")