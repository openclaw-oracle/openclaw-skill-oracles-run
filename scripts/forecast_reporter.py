#!/usr/bin/env python3
"""
Oracle ClawBot - Forecast + Tweet Integration
After submitting forecast, posts tweet with results
"""

import json
import requests
from datetime import datetime
from oracles_client import OraclesClient

class ForecastReporter:
    def __init__(self, oracles_client, twitter_token):
        self.oracles = oracles_client
        self.twitter_token = twitter_token
    
    def post_tweet(self, text: str) -> dict:
        """Post tweet via X API v2"""
        url = "https://api.x.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.twitter_token}",
            "Content-Type": "application/json"
        }
        payload = {"text": text}
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 201:
            return {"success": True, "tweet_id": resp.json()['data']['id']}
        return {"success": False, "error": resp.text}
    
    def submit_forecast_single(self, market_slug: str, market_name: str, 
                                 outcome: str, p_yes: float, confidence: float,
                                 rationale: str, stake: int = 10) -> dict:
        """Submit single forecast (no tweet)"""
        print(f"\n📊 Submitting forecast to {market_name}...")
        try:
            result = self.oracles.submit_forecast(
                market_slug=market_slug,
                p_yes=p_yes,
                confidence=confidence,
                rationale=rationale,
                selected_outcome=outcome,
                stake_units=stake
            )
            forecast_id = result.get('forecast_id', 'N/A')
            print(f"   ✅ Forecast submitted! ID: {forecast_id[:20]}...")
            return {
                "success": True,
                "market": market_name,
                "outcome": outcome,
                "p_yes": p_yes,
                "confidence": confidence,
                "stake": stake,
                "forecast_id": forecast_id
            }
        except Exception as e:
            print(f"   ❌ Forecast failed: {str(e)[:60]}")
            return {"success": False, "error": str(e), "market": market_name}
    
    def post_summary_tweet(self, forecasts: list) -> dict:
        """Post one summary tweet for all forecasts"""
        if not forecasts:
            return {"success": False, "error": "No forecasts to tweet"}
        
        successful = [f for f in forecasts if f.get('success')]
        if not successful:
            return {"success": False, "error": "No successful forecasts"}
        
        # Build markets list
        market_names = [f['market'] for f in successful]
        markets_str = " • ".join(market_names[:6])  # Max 6 markets
        if len(market_names) > 6:
            markets_str += " & more"
        
        total_stake = sum(f['stake'] for f in successful)
        # Correct profile URL
        profile_url = "https://oracles.run/agents/clawbot-predictor"
        
        # Summary tweet
        tweet = f"""🔮 New forecasts submitted: {len(successful)} markets

{markets_str}
💰 Total stake: {total_stake} units

Track my predictions:
{profile_url}

@oracles_run Sandbox S1 🏆
#oraclesrun #polymarket #AI"""
        
        print(f"\n🐦 Posting summary tweet...")
        result = self.post_tweet(tweet)
        
        if result['success']:
            tweet_url = f"https://x.com/oraclesrun/status/{result['tweet_id']}"
            print(f"   ✅ Tweet posted!")
            print(f"   🔗 {tweet_url}")
            return {"success": True, "url": tweet_url, "tweet_id": result['tweet_id']}
        else:
            print(f"   ❌ Tweet failed: {result.get('error', 'Unknown')}")
            return {"success": False, "error": result.get('error')}
    
    def submit_batch_and_tweet(self, forecasts_list: list) -> dict:
        """Submit multiple forecasts and post one summary tweet"""
        results = []
        
        # Submit all forecasts
        for fc in forecasts_list:
            result = self.submit_forecast_single(**fc)
            results.append(result)
        
        # Post one summary tweet
        tweet_result = self.post_summary_tweet(results)
        
        return {
            "forecasts": results,
            "tweet": tweet_result,
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r.get('success')]),
                "tweet_posted": tweet_result.get('success', False)
            }
        }
    
    def print_batch_report(self, result: dict):
        """Print full report for batch submission with summary tweet"""
        print('\n' + '='*70)
        print('📊 FORECAST BATCH REPORT')
        print('='*70)
        
        forecasts = result.get('forecasts', [])
        tweet = result.get('tweet', {})
        summary = result.get('summary', {})
        
        # Print each forecast
        for i, fc in enumerate(forecasts, 1):
            if not fc.get('success'):
                print(f"\n{i}. ❌ {fc.get('market', 'Unknown')}: {fc.get('error', 'Failed')}")
                continue
            
            print(f"\n{i}. ✅ {fc['market']}")
            print(f"   📋 Outcome: {fc['outcome'][:50]}...")
            print(f"   📈 p_yes: {fc['p_yes']*100:.0f}% | Conf: {fc['confidence']*100:.0f}% | Stake: {fc['stake']}")
            print(f"   🔮 Forecast ID: {fc['forecast_id'][:25]}...")
        
        # Print tweet info
        print('\n' + '-'*70)
        print('🐦 SUMMARY TWEET')
        print('-'*70)
        if tweet.get('success'):
            print(f"✅ Tweet posted: {tweet['url']}")
        else:
            print(f"❌ Tweet failed: {tweet.get('error', 'Unknown error')}")
        
        # Print summary
        print('\n' + '='*70)
        print(f"✅ Forecasts: {summary.get('successful', 0)}/{summary.get('total', 0)}")
        print(f"🐦 Summary tweet: {'Posted' if summary.get('tweet_posted') else 'Failed'}")
        print(f"💰 Total stake: {sum(fc.get('stake', 0) for fc in forecasts if fc.get('success'))} units")
        print('='*70)


def main():
    """Demo: Submit batch forecasts and post one summary tweet"""
    import os
    
    # Load credentials
    agent_id = os.getenv("ORACLES_AGENT_ID", "c99bfb5e-2df0-4d9b-bd57-3b2163724b11")
    api_key = os.getenv("ORACLES_API_KEY", "ap_q3I9c5eOIsSJCsKhTyHEmW6JUzXTKvx7")
    
    # Load Twitter token
    try:
        with open('.twitter_oauth2_tokens.json') as f:
            tokens = json.load(f)
            twitter_token = tokens['access_token']
    except:
        print("❌ Twitter token not found!")
        return
    
    # Initialize
    oracles = OraclesClient(agent_id, api_key)
    reporter = ForecastReporter(oracles, twitter_token)
    
    # Example forecasts batch
    forecasts_list = [
        {
            'market_slug': 'pm-what-price-will-ethereum-hit-in-february',
            'market_name': 'ETH',
            'outcome': 'Will Ethereum reach $3,200 in February?',
            'p_yes': 0.65,
            'confidence': 0.70,
            'rationale': 'ETH showing strong support above $3k.',
            'stake': 10
        },
        {
            'market_slug': 'pm-what-price-will-bitcoin-hit-in-february',
            'market_name': 'BTC',
            'outcome': 'Will Bitcoin reach $100,000 in February?',
            'p_yes': 0.72,
            'confidence': 0.75,
            'rationale': 'BTC momentum strong with institutional adoption.',
            'stake': 10
        }
    ]
    
    # Submit batch and post one summary tweet
    result = reporter.submit_batch_and_tweet(forecasts_list)
    
    # Print report
    reporter.print_batch_report(result)


if __name__ == "__main__":
    main()
