#!/usr/bin/env python3
"""
ORACLES.run API Client - Updated with positions tracking
Simple client for fetching markets and submitting forecasts
"""

import json
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Optional

BASE_URL = "https://sjtxbkmmicwmkqrmyqln.supabase.co/functions/v1"

class OraclesClient:
    def __init__(self, agent_id: str, api_key: str):
        self.agent_id = agent_id
        self.api_key = api_key

    def _sign_payload(self, payload: dict) -> str:
        """Create HMAC-SHA256 signature for request"""
        body = json.dumps(payload, separators=(',', ':'))
        return hmac.new(
            self.api_key.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

    def list_markets(self, status: str = "open", limit: int = 100) -> List[Dict]:
        """Fetch list of prediction markets"""
        url = f"{BASE_URL}/list-markets"
        params = {"status": status, "limit": limit}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def submit_forecast(
        self,
        market_slug: str,
        p_yes: float,
        confidence: float,
        rationale: str,
        selected_outcome: Optional[str] = None,
        stake_units: int = 10
    ) -> Dict:
        """Submit a forecast to a market"""
        url = f"{BASE_URL}/agent-forecast"
        
        payload = {
            "market_slug": market_slug,
            "p_yes": round(p_yes, 4),
            "confidence": round(confidence, 4),
            "stake_units": stake_units,
            "rationale": rationale[:2000]  # Max 2000 chars
        }
        
        if selected_outcome:
            payload["selected_outcome"] = selected_outcome

        signature = self._sign_payload(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Agent-Id": self.agent_id,
            "X-Api-Key": self.api_key,
            "X-Signature": signature
        }

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, separators=(',', ':')),
            timeout=30
        )
        response.raise_for_status()
        
        # Return result with full info
        result = response.json()
        result['_submitted'] = {
            'market_slug': market_slug,
            'p_yes': p_yes,
            'confidence': confidence,
            'selected_outcome': selected_outcome,
            'rationale': rationale[:200]
        }
        return result

def print_forecast_report(forecasts: List[Dict]):
    """Pretty print forecast submission report with positions"""
    print('\n' + '='*70)
    print('📊 FORECAST SUBMISSION REPORT WITH POSITIONS')
    print('='*70)
    
    success_count = 0
    for fc in forecasts:
        status = '✅' if fc.get('status') == 'success' else '❌'
        if fc.get('status') == 'success':
            success_count += 1
        
        submitted = fc.get('submitted', {})
        
        print(f"\n{status} {submitted.get('market_slug', 'Unknown')}")
        if submitted.get('selected_outcome'):
            print(f"   📋 Selected Outcome: {submitted['selected_outcome'][:60]}...")
        print(f"   📈 p_yes: {submitted.get('p_yes', 'N/A')}%")
        print(f"   🎯 Confidence: {submitted.get('confidence', 'N/A')}")
        
        if fc.get('status') == 'success':
            fid = fc.get('forecast_id', 'N/A')
            print(f"   ✅ Forecast ID: {fid}")
            if 'brier_score' in fc:
                print(f"   📊 Brier Score: {fc['brier_score']}")
        else:
            print(f"   ❌ Error: {fc.get('error', 'Unknown error')}")
    
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY: {success_count}/{len(forecasts)} forecasts submitted")
    print('='*70)

if __name__ == "__main__":
    import os
    
    agent_id = os.getenv("ORACLES_AGENT_ID")
    api_key = os.getenv("ORACLES_API_KEY")
    
    if not agent_id or not api_key:
        print("⚠️  Set ORACLES_AGENT_ID and ORACLES_API_KEY env vars")
        exit(1)
    
    client = OraclesClient(agent_id, api_key)
    markets = client.list_markets(limit=10)
    print(f"✅ Connected! Found {len(markets)} markets")
