#!/usr/bin/env python3
"""
Automated forecast submission script
Run manually or via cron every 6 hours
"""

import os
import sys
import json
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.oracles_client import OraclesClient
from scripts.forecast_reporter import ForecastReporter

def main():
    print(f"\n{'='*70}")
    print(f"🔮 ORACLE CLAWBOT - FORECAST RUN")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'='*70}")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    agent_id = os.getenv("ORACLES_AGENT_ID")
    api_key = os.getenv("ORACLES_API_KEY")
    
    if not agent_id or not api_key:
        print("❌ ERROR: ORACLES_AGENT_ID and ORACLES_API_KEY required in .env")
        sys.exit(1)
    
    # Initialize clients
    print("\n📡 Connecting to oracles.run...")
    oracles = OraclesClient(agent_id, api_key)
    
    # Load Twitter token
    try:
        with open('.twitter_oauth2_tokens.json') as f:
            tokens = json.load(f)
        twitter_token = tokens['access_token']
        print("✅ Twitter token loaded")
    except Exception as e:
        print(f"❌ Twitter token error: {e}")
        print("   Run: python3 scripts/get_url.py")
        sys.exit(1)
    
    reporter = ForecastReporter(oracles, twitter_token)
    
    # Fetch available markets
    print("\n📊 Fetching open markets...")
    markets = oracles.list_markets(status="open")
    print(f"✅ Found {len(markets)} open markets")
    
    # =========================================================================
    # DEFINE YOUR FORECASTS HERE
    # Update this section with your analysis for each run
    # =========================================================================
    
    forecasts = []
    
    # Example 1: ETH Price
    eth_market = [m for m in markets if 'pm-what-price-will-ethereum' in m.get('slug', '')]
    if eth_market:
        forecasts.append({
            'market_slug': eth_market[0]['slug'],
            'market_name': 'ETH',
            'outcome': 'Will Ethereum reach $3,200 in February?',
            'p_yes': 0.65,  # UPDATE: Your prediction here
            'confidence': 0.70,
            'rationale': 'ETH showing strong support above $3k with positive ETF flows and bullish technical indicators.',
            'stake': 10
        })
    
    # Example 2: BTC Price
    btc_market = [m for m in markets if 'pm-what-price-will-bitcoin' in m.get('slug', '')]
    if btc_market:
        forecasts.append({
            'market_slug': btc_market[0]['slug'],
            'market_name': 'BTC',
            'outcome': 'Will Bitcoin reach $100,000 in February?',
            'p_yes': 0.58,  # UPDATE: Your prediction here
            'confidence': 0.65,
            'rationale': 'BTC momentum strong with institutional adoption continuing. Path to $100K viable.',
            'stake': 10
        })
    
    # Example 3: Fed Decision
    fed_market = [m for m in markets if 'pm-fed-decision' in m.get('slug', '')]
    if fed_market:
        outcomes = fed_market[0].get('polymarket_outcomes', [])
        no_change = [o for o in outcomes if 'no change' in o.get('question', '').lower()]
        if no_change:
            forecasts.append({
                'market_slug': fed_market[0]['slug'],
                'market_name': 'Fed',
                'outcome': no_change[0]['question'],
                'p_yes': 0.78,  # UPDATE: Your prediction here
                'confidence': 0.72,
                'rationale': 'Economic data supports holding rates steady. No urgency for changes.',
                'stake': 10
            })
    
    # ADD MORE FORECASTS HERE...
    
    # =========================================================================
    
    if not forecasts:
        print("\n⚠️ No forecasts defined. Edit this script to add forecasts.")
        sys.exit(0)
    
    print(f"\n📋 Prepared {len(forecasts)} forecasts")
    
    # Submit batch and tweet
    print("\n🚀 Submitting forecasts...")
    result = reporter.submit_batch_and_tweet(forecasts)
    
    # Print report
    reporter.print_batch_report(result)
    
    # Save results
    with open(f"forecast_log_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json", 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Done!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
