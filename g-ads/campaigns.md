# Campaign Building Guide (`campaigns.md`)

This guide outlines the standard operating procedures and technical blueprint for building high-converting Google Ads Search campaigns (SKAG / STAG methodology) via Claude Code and the Google Ads API.

---

## 1. Core Principles & Safety Rules

1. **Always Create as PAUSED**:
   - All newly created campaigns, ad groups, keywords, and ads must have their status explicitly set to `PAUSED` (`status = CampaignStatusEnum.CampaignStatus.PAUSED`).
   - Never set a campaign to `ENABLED` automatically. The user must review and manually enable it.
2. **Search Network Only**:
   - Disable Google Display Network (`target_content_network = False`) on Search campaigns to prevent wasted spend on non-search inventory.
3. **Strict Location Presence**:
   - Use `PRESENCE` targeting ("People in or regularly in your targeted locations") rather than the default `PRESENCE_OR_INTEREST`.
4. **Website Alignment**:
   - Extract USP (Unique Selling Propositions), service offerings, pricing, trust badges, and phone numbers directly from the target website/landing page to ensure ad copy relevancy.

---

## 2. Campaign Structure & Blueprint

### A. Campaign Naming Convention
Format: `[Channel] - [Core Service/Product] - [Location/Geo]`
* Example: `Search - Emergency Plumber - Toronto`
* Example: `Search - Drain Cleaning - Downtown Toronto`

### B. Campaign Settings Specification

| Setting | Value / Recommendation | Google Ads API Field |
| :--- | :--- | :--- |
| **Channel Type** | Search | `advertising_channel_type = AdvertisingChannelType.SEARCH` |
| **Status** | `PAUSED` | `status = CampaignStatus.PAUSED` |
| **Google Search** | Enabled | `network_settings.target_google_search = True` |
| **Search Network Partners** | Optional (default False) | `network_settings.target_search_network = False` |
| **Display Network** | **Disabled** | `network_settings.target_content_network = False` |
| **Location Target Type** | Presence Only | `geo_target_type_setting.positive_geo_target_type = PositiveGeoTargetType.PRESENCE` |
| **Bidding Strategy** | Manual CPC / Maximize Clicks with Bid Cap | `manual_cpc` or `maximize_clicks` |
| **Budget Delivery** | Standard | `delivery_method = BudgetDeliveryMethod.STANDARD` |

---

## 3. Ad Group & SKAG Architecture

Single Keyword Ad Groups (SKAGs) or tightly focused Single Theme Ad Groups (STAGs) maximize Quality Score, CTR, and conversion rate by ensuring ad copy perfectly reflects user search intent.

### A. Ad Group Structure
* **Ad Group Name**: `[Core Keyword / Theme]` (e.g. `Emergency Plumber Toronto - Exact & Phrase`)
* **Status**: `PAUSED` (`status = AdGroupStatus.PAUSED`)
* **Default Max CPC**: Set conservative bid cap according to target CPA / budget (e.g., \$2.50–\$5.00 depending on industry).

### B. Keyword Pairing
For each ad group, add the core target term in both match types:
1. **Exact Match `[term]`**:
   - `match_type = KeywordMatchTypeEnum.KeywordMatchType.EXACT`
   - Example: `[emergency plumber toronto]`
2. **Phrase Match `"term"`**:
   - `match_type = KeywordMatchTypeEnum.KeywordMatchType.PHRASE`
   - Example: `"emergency plumber toronto"`

---

## 4. Google Ads API Implementation Template

When creating a campaign programmatically via Python and the Google Ads API:

```python
import os
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from dotenv import load_dotenv

load_dotenv()

def create_search_campaign(
    customer_id: str,
    campaign_name: str,
    daily_budget_micros: int = 20_000_000, # $20.00 / day
    geo_target_constant_id: str = "1002473" # e.g. Toronto
):
    client = GoogleAdsClient.load_from_storage(path=None) # reads from env / credentials
    campaign_service = client.get_service("CampaignService")
    budget_service = client.get_service("CampaignBudgetService")
    
    # 1. Create Campaign Budget
    budget_operation = client.get_type("CampaignBudgetOperation")
    budget = budget_operation.create
    budget.name = f"{campaign_name} Budget"
    budget.amount_micros = daily_budget_micros
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.BudgetDeliveryMethod.STANDARD
    budget.explicitly_shared = False
    
    budget_response = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_operation]
    )
    budget_resource_name = budget_response.results[0].resource_name

    # 2. Create Search Campaign
    campaign_operation = client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = campaign_name
    campaign.advertising_channel_type = (
        client.enums.AdvertisingChannelTypeEnum.AdvertisingChannelType.SEARCH
    )
    # ALWAYS set status to PAUSED
    campaign.status = client.enums.CampaignStatusEnum.CampaignStatus.PAUSED
    campaign.campaign_budget = budget_resource_name
    
    # Network Settings: Search only, disable Display Expansion
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = False
    campaign.network_settings.target_content_network = False
    campaign.network_settings.target_partner_search_network = False
    
    # Location Presence targeting
    campaign.geo_target_type_setting.positive_geo_target_type = (
        client.enums.PositiveGeoTargetTypeEnum.PositiveGeoTargetType.PRESENCE
    )
    
    # Bidding: Manual CPC (or Maximize Clicks)
    campaign.manual_cpc.enhanced_cpc_enabled = False
    
    campaign_response = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_operation]
    )
    campaign_resource_name = campaign_response.results[0].resource_name
    print(f"Created Campaign: {campaign_resource_name} (PAUSED)")
    return campaign_resource_name
```

---

## 5. Negative Keywords Integration

To protect ad spend and prevent keyword cannibalization:
1. Attach the universal negative keyword list (excluding `free`, `job`, `salary`, `diy`, `course`, `tutorial`, `reddit`, etc.).
2. Cross-negative exact match terms between broader and specialized ad groups.

---

## 6. Pre-Launch Verification Checklist

Before requesting the user to activate any campaign, verify:
- [ ] Campaign is in `PAUSED` state.
- [ ] Display Network expansion is set to `False`.
- [ ] Positive Geo Target Type is set to `PRESENCE`.
- [ ] Daily budget and max CPC bids are within the user's allocated limits.
- [ ] Landing page URLs match the intent of the keyword theme and include UTM parameters.
- [ ] Universal Negative Keyword List is attached.
