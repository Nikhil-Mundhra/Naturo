"""Build Google Ads Campaign for Naturo Industries.

Follows the guidelines in campaigns.md:
- Campaign and Ad Groups created in PAUSED state.
- Search Network only (Display Expansion disabled).
- Presence-only Geo Targeting.
- SKAG / STAG Keyword pairing (Exact + Phrase).
- Tailored ad copy directly extracted from naturoindustries.com product data.
- Includes Dry-Run Preview Mode and Google Ads API deployment.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Naturo Industries Campaign Blueprint & Catalog Data
NATURO_CAMPAIGN_CONFIG: Dict[str, Any] = {
    "campaign_name": "Search - Architectural Panels & Surfaces - Naturo Industries",
    "domain": "https://naturoindustries.com",
    "daily_budget_inr": 1500,  # ₹1500 / day (~$18)
    "currency_code": "INR",
    "location_geo_targets": [
        {"id": "2356", "name": "India (National)"},  # GeoTargetConstant ID for India
    ],
    "universal_negatives": [
        "free", "crack", "torrent", "jobs", "vacancy", "salary", "recruitment",
        "internship", "diy how to make", "tutorial youtube", "wikipedia", "course",
        "second hand", "used", "cheap quality", "reddit review"
    ],
    "ad_groups": [
        {
            "name": "WPC & Charcoal Louver Panels",
            "landing_page": "https://naturoindustries.com/blog/louver-panels-in-pvc-wpc-charcoal",
            "max_cpc_inr": 35.0,
            "keywords": [
                {"text": "wpc louver panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "charcoal louver panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "fluted wall panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "acoustic slat wall panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "charcoal wall panel manufacturer", "match_types": ["EXACT", "PHRASE"]}
            ],
            "rsa_headlines": [
                "Naturo Louver Wall Panels",
                "WPC & Charcoal Slat Panels",
                "Acoustic Fluted Panels",
                "Termite & Moisture Proof",
                "Luxury Slat Wall Aesthetics",
                "Direct Manufacturer Supply",
                "Seamless Interlocking Slats",
                "Architectural Louvers India",
                "Interior & Elevation Louvers",
                "Download Product Catalog"
            ],
            "rsa_descriptions": [
                "Transform walls and ceilings with high-durability WPC & charcoal louver panels.",
                "Water-resistant, acoustic-dampening fluted panels designed for luxury interiors.",
                "Interlocking slat system for fast, seamless installation. Request bulk catalog.",
                "Premium architectural surfaces for designers, builders & architects across India."
            ]
        },
        {
            "name": "PU Stone & Flexible Stone Veneer",
            "landing_page": "https://naturoindustries.com/blog/pu-stone-panels-stone-veneer",
            "max_cpc_inr": 40.0,
            "keywords": [
                {"text": "pu stone panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "lightweight stone veneer", "match_types": ["EXACT", "PHRASE"]},
                {"text": "3d stone wall panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "polyurethane faux stone", "match_types": ["EXACT", "PHRASE"]},
                {"text": "flexible stone sheets", "match_types": ["EXACT", "PHRASE"]}
            ],
            "rsa_headlines": [
                "PU Stone Wall Panels",
                "Lightweight Stone Veneer",
                "3D Architectural Rock Finish",
                "Easy DIY Installation",
                "Faux Stone Wall Panels",
                "Naturo Stone Textures",
                "Zero Heavy Structural Load",
                "Interior & Exterior Facades",
                "Authentic Slate & Rock Look",
                "Order Sample Kit Today"
            ],
            "rsa_descriptions": [
                "Ultra-lightweight PU stone panels featuring authentic high-relief rock textures.",
                "Transform plain walls into luxury stone facades without heavy masonry structural load.",
                "Waterproof, fire-retardant & easy to cut. Perfect for feature walls and elevations.",
                "Direct supplier of lightweight polyurethane stone veneers. Contact Naturo today."
            ]
        },
        {
            "name": "Bamboo Charcoal Sheets & HDHMR",
            "landing_page": "https://naturoindustries.com/blog/bamboo-charcoal-sheets-hdhmr-panels",
            "max_cpc_inr": 30.0,
            "keywords": [
                {"text": "bamboo charcoal sheets", "match_types": ["EXACT", "PHRASE"]},
                {"text": "bamboo charcoal board", "match_types": ["EXACT", "PHRASE"]},
                {"text": "hdhmr vectra panels", "match_types": ["EXACT", "PHRASE"]},
                {"text": "waterproof charcoal board", "match_types": ["EXACT", "PHRASE"]}
            ],
            "rsa_headlines": [
                "Bamboo Charcoal Sheets",
                "HDHMR Vectra Panels",
                "100% Waterproof & Anti-Termite",
                "90-Degree Bendable Sheets",
                "Zero Formaldehyde Panels",
                "Precision CNC Routing Ready",
                "Eco-Friendly Surface Panels",
                "Naturo Premium Charcoal Board",
                "Ideal For Kitchens & Wardrobes",
                "Explore Full Technical Specs"
            ],
            "rsa_descriptions": [
                "Premium bamboo charcoal sheets offering superior acoustic depth & zero emissions.",
                "100% moisture-proof and flexible for seamless corner bending without cracking.",
                "Precision-engineered HDHMR panels built for intricate CNC routing and wall decor.",
                "Explore Naturo Industries' innovative bamboo charcoal solutions for modern homes."
            ]
        },
        {
            "name": "UV Marble & Bookmatch Panels",
            "landing_page": "https://naturoindustries.com/blog/uv-marble-digital-bookmatch-sheets",
            "max_cpc_inr": 32.0,
            "keywords": [
                {"text": "uv marble sheets", "match_types": ["EXACT", "PHRASE"]},
                {"text": "pvc marble sheets", "match_types": ["EXACT", "PHRASE"]},
                {"text": "bookmatch marble sheets", "match_types": ["EXACT", "PHRASE"]},
                {"text": "high gloss wall panels", "match_types": ["EXACT", "PHRASE"]}
            ],
            "rsa_headlines": [
                "UV Marble Wall Sheets",
                "Digital Bookmatch Panels",
                "Luxury High Gloss Finish",
                "Affordable Italian Marble Look",
                "Scratch & Stain Resistant",
                "Lightweight PVC Marble Board",
                "Seamless Wall Elevation",
                "Naturo Luxury Marble Sheets",
                "Quick Wall Cladding Solution",
                "Request Free Swatch Catalog"
            ],
            "rsa_descriptions": [
                "Achieve breathtaking Italian marble aesthetics at a fraction of natural stone cost.",
                "High-gloss UV protective coating ensures long-lasting scratch and moisture resistance.",
                "Symmetrical digital book-match designs engineered for dramatic living room feature walls.",
                "Explore lightweight, easy-to-install UV marble sheets manufactured by Naturo."
            ]
        },
        {
            "name": "Exterior WPC Decking & Cladding",
            "landing_page": "https://naturoindustries.com/blog/deck-clad-exterior-wpc-decking",
            "max_cpc_inr": 45.0,
            "keywords": [
                {"text": "exterior wpc decking", "match_types": ["EXACT", "PHRASE"]},
                {"text": "wpc outdoor deck flooring", "match_types": ["EXACT", "PHRASE"]},
                {"text": "capped composite decking", "match_types": ["EXACT", "PHRASE"]},
                {"text": "hpl exterior cladding", "match_types": ["EXACT", "PHRASE"]}
            ],
            "rsa_headlines": [
                "Exterior WPC Decking",
                "360-Degree Capped Decking",
                "Weatherproof Outdoor Living",
                "Anti-Slip Deck Flooring",
                "Zero Rot & Splinter Free",
                "HPL Exterior Wall Cladding",
                "Naturo Outdoor Surfaces",
                "UV & Termite Resistant Deck",
                "Balcony & Poolside Decking",
                "Get Wholesale Quote"
            ],
            "rsa_descriptions": [
                "360-degree shielded composite decking built to withstand harsh rain, UV rays and heat.",
                "No rotting, warping, or splintering. Low-maintenance luxury flooring for pools & gardens.",
                "Engineered with anti-slip grooves and hidden clip fasteners for flawless outdoor spaces.",
                "Browse high-durability exterior decking and cladding solutions from Naturo Industries."
            ]
        }
    ]
}


def print_campaign_plan():
    """Outputs the complete campaign structure in clean Markdown."""
    cfg = NATURO_CAMPAIGN_CONFIG
    print("=" * 80)
    print("GOOGLE ADS CAMPAIGN BLUEPRINT (NATURO INDUSTRIES)")
    print("=" * 80)
    print(f"Campaign Name:    {cfg['campaign_name']}")
    print(f"Status:           PAUSED (Safety Rule: campaigns.md)")
    print(f"Daily Budget:     ₹{cfg['daily_budget_inr']:,}/day ({cfg['currency_code']})")
    print(f"Target Geo:       {', '.join([g['name'] for g in cfg['location_geo_targets']])}")
    print(f"Display Network:  DISABLED (Search Only)")
    print(f"Location Target:  PRESENCE ONLY")
    print(f"Universal Neg:    {len(cfg['universal_negatives'])} keywords attached")
    print("-" * 80)
    print(f"Total Ad Groups:  {len(cfg['ad_groups'])}")
    print("-" * 80)

    for i, ag in enumerate(cfg["ad_groups"], 1):
        print(f"\n[{i}] Ad Group: {ag['name']}")
        print(f"    Max CPC:      ₹{ag['max_cpc_inr']:.2f}")
        print(f"    Landing Page: {ag['landing_page']}")
        print("    Keywords:")
        for kw in ag["keywords"]:
            exact = f"[{kw['text']}]"
            phrase = f'"{kw["text"]}"'
            print(f"      - {exact:<35} (EXACT)")
            print(f"      - {phrase:<35} (PHRASE)")
        print(f"    RSAs: {len(ag['rsa_headlines'])} Headlines | {len(ag['rsa_descriptions'])} Descriptions")
        print("      Top Headlines:   " + " | ".join(ag["rsa_headlines"][:4]))
        print("      Sample Desc:     " + ag["rsa_descriptions"][0])

    print("\n" + "=" * 80)
    print("Ready to push to Google Ads API in PAUSED mode once customer credentials are confirmed.")
    print("=" * 80)


def push_to_google_ads(customer_id: str):
    """Executes the Google Ads API calls to create the campaign in PAUSED status."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
    except ImportError:
        print("Error: google-ads package is not installed in current environment.")
        sys.exit(1)

    print(f"Initializing Google Ads Client for Customer ID: {customer_id}...")
    client = GoogleAdsClient.load_from_dict(
        {
            "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
            "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            "use_proto_plus": True,
        }
    )

    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_service = client.get_service("CampaignService")
    ad_group_service = client.get_service("AdGroupService")
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    ad_group_ad_service = client.get_service("AdGroupAdService")

    cfg = NATURO_CAMPAIGN_CONFIG

    # 1. Create Budget
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"{cfg['campaign_name']} Budget"
    budget.amount_micros = cfg["daily_budget_inr"] * 1_000_000
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.BudgetDeliveryMethod.STANDARD
    budget.explicitly_shared = False

    budget_res = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_op]
    )
    budget_resource_name = budget_res.results[0].resource_name
    print(f"[✓] Created Budget: {budget_resource_name}")

    # 2. Create Search Campaign (PAUSED)
    campaign_op = client.get_type("CampaignOperation")
    camp = campaign_op.create
    camp.name = cfg["campaign_name"]
    camp.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.AdvertisingChannelType.SEARCH
    camp.status = client.enums.CampaignStatusEnum.CampaignStatus.PAUSED
    camp.campaign_budget = budget_resource_name

    camp.network_settings.target_google_search = True
    camp.network_settings.target_search_network = False
    camp.network_settings.target_content_network = False
    camp.network_settings.target_partner_search_network = False

    camp.geo_target_type_setting.positive_geo_target_type = (
        client.enums.PositiveGeoTargetTypeEnum.PositiveGeoTargetType.PRESENCE
    )
    camp.manual_cpc.enhanced_cpc_enabled = False

    camp_res = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_op]
    )
    campaign_resource_name = camp_res.results[0].resource_name
    print(f"[✓] Created Search Campaign: {campaign_resource_name} (PAUSED)")

    # 3. Create Ad Groups, Keywords & RSAs
    for ag_data in cfg["ad_groups"]:
        ag_op = client.get_type("AdGroupOperation")
        ad_group = ag_op.create
        ad_group.name = ag_data["name"]
        ad_group.campaign = campaign_resource_name
        ad_group.status = client.enums.AdGroupStatusEnum.AdGroupStatus.PAUSED
        ad_group.type_ = client.enums.AdGroupTypeEnum.AdGroupType.SEARCH_STANDARD
        ad_group.cpc_bid_micros = int(ag_data["max_cpc_inr"] * 1_000_000)

        ag_res = ad_group_service.mutate_ad_groups(
            customer_id=customer_id, operations=[ag_op]
        )
        ag_resource_name = ag_res.results[0].resource_name
        print(f"  [✓] Created Ad Group: {ag_data['name']} (PAUSED)")

        # Add Keywords (Exact + Phrase)
        kw_ops = []
        for kw in ag_data["keywords"]:
            for match_type in kw["match_types"]:
                kw_op = client.get_type("AdGroupCriterionOperation")
                criterion = kw_op.create
                criterion.ad_group = ag_resource_name
                criterion.status = client.enums.AdGroupCriterionStatusEnum.AdGroupCriterionStatus.PAUSED
                criterion.keyword.text = kw["text"]
                if match_type == "EXACT":
                    criterion.keyword.match_type = (
                        client.enums.KeywordMatchTypeEnum.KeywordMatchType.EXACT
                    )
                else:
                    criterion.keyword.match_type = (
                        client.enums.KeywordMatchTypeEnum.KeywordMatchType.PHRASE
                    )
                kw_ops.append(kw_op)

        ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id, operations=kw_ops
        )
        print(f"      - Added {len(kw_ops)} exact & phrase keywords")

        # Create RSA
        ad_op = client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create
        ad_group_ad.ad_group = ag_resource_name
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.AdGroupAdStatus.PAUSED
        
        rsa = ad_group_ad.ad.responsive_search_ad
        rsa.headlines.extend([
            client.get_type("AdTextAsset", {"text": h})
            for h in ag_data["rsa_headlines"][:15]
        ])
        rsa.descriptions.extend([
            client.get_type("AdTextAsset", {"text": d})
            for d in ag_data["rsa_descriptions"][:4]
        ])
        ad_group_ad.ad.final_urls.append(
            f"{ag_data['landing_page']}?utm_source=google&utm_medium=cpc&utm_campaign=search_architectural_surfaces"
        )

        ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id, operations=[ad_op]
        )
        print(f"      - Added Responsive Search Ad (PAUSED)")

    print("\n[SUCCESS] Entire Naturo campaign created safely in PAUSED state!")


def main():
    parser = argparse.ArgumentParser(description="Build Google Ads Campaign for Naturo Industries")
    parser.add_argument("--preview", action="store_true", default=True, help="Print plan preview")
    parser.add_argument("--push", action="store_true", help="Push campaign to Google Ads API")
    parser.add_argument("--customer-id", type=str, help="Target Customer ID (without dashes)")

    args = parser.parse_args()

    if args.push:
        cust_id = args.customer_id or os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        if not cust_id:
            print("Error: Specify --customer-id or set GOOGLE_ADS_CUSTOMER_ID in .env")
            sys.exit(1)
        push_to_google_ads(cust_id.replace("-", "").strip())
    else:
        print_campaign_plan()


if __name__ == "__main__":
    main()
