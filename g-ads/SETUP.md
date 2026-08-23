# Google Ads API setup

This folder contains the credentials template and small scripts needed to connect
to Google Ads. Keep `.env` and OAuth JSON files local; never paste their values
into `PROMPTS.md` or commit them.

## 1. Create or choose a manager account

Create a Google Ads manager account (MCC) at <https://ads.google.com/home/tools/manager-accounts/>.
Put its 10-digit customer ID, without dashes, in
`GOOGLE_ADS_LOGIN_CUSTOMER_ID`.

## 2. Choose the ads account

Put the customer ID of the account that will run ads in
`GOOGLE_ADS_CUSTOMER_ID`. Remove dashes from both IDs, for example
`1234567890`.

## 3. Request a developer token

From the manager account, open **Tools and settings > Setup > API Center** and
request a developer token. Add the token to `GOOGLE_ADS_DEVELOPER_TOKEN`.
Test accounts can use a test token while access is being reviewed. Production
access may remain limited until Google approves the application.

## 4. Create a Google Cloud project

1. Open <https://console.cloud.google.com/> and create or select a project.
2. Enable the **Google Ads API**.
3. Configure the OAuth consent screen. Add yourself as a test user if the app is
   still in testing.

## 5. Create OAuth credentials

Create an **OAuth client ID** for a **Desktop app** and download the JSON file.
Save it in this folder as `client_secret.json`. It is ignored by Git.

## 6. Install dependencies

From this directory, create a virtual environment and install the client:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install google-ads python-dotenv
```

## 7. Generate a refresh token

Run:

```sh
python get_refresh_token.py
```

Open the printed URL, authorize the Google account that has access to the
manager account, then paste the returned authorization code when prompted.
Copy the displayed refresh token into `GOOGLE_ADS_REFRESH_TOKEN` in `.env`.

## 8. Test the connection

Run:

```sh
python test_connection.py
```

A successful run prints the accessible customer accounts. If it fails, check
that IDs contain no dashes, the login customer is the manager account, and the
OAuth user has access to the target account.