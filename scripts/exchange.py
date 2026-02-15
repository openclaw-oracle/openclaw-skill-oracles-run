#!/usr/bin/env python3
"""
Exchange OAuth 2.0 authorization code for access token
Usage: python3 scripts/exchange.py "YOUR_CODE_HERE"
"""

import sys
import json
import base64
import requests

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 exchange.py 'CODE_HERE'")
        print("Example: python3 exchange.py 'abc123xyz...'")
        sys.exit(1)
    
    CODE = sys.argv[1].strip()
    WEBHOOK = 'https://webhook.site/dc980780-809c-4ec9-bda2-2dccd53e5f40'
    
    print("="*70)
    print("🔄 EXCHANGING CODE FOR TOKEN")
    print("="*70)
    
    # Load credentials
    try:
        with open('.env') as f:
            lines = f.readlines()
            creds = {}
            for line in lines:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    creds[key] = val
        
        CLIENT_ID = creds.get('TWITTER_CLIENT_ID')
        CLIENT_SECRET = creds.get('TWITTER_CLIENT_SECRET')
        
        if not CLIENT_ID or not CLIENT_SECRET:
            raise ValueError("Twitter credentials not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Load verifier
    try:
        with open('.pkce_verifier.txt', 'r') as f:
            verifier = f.read().strip()
    except:
        print("❌ PKCE verifier not found. Run get_url.py first.")
        sys.exit(1)
    
    print(f"✅ Code: {CODE[:30]}...")
    print(f"✅ Verifier: {verifier[:30]}...")
    
    # Exchange
    print("\n🔄 Sending request...")
    
    data = {
        'grant_type': 'authorization_code',
        'code': CODE,
        'redirect_uri': WEBHOOK,
        'code_verifier': verifier,
        'client_id': CLIENT_ID
    }
    
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    basic_auth = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {basic_auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    resp = requests.post('https://api.x.com/2/oauth2/token', data=data, headers=headers)
    
    print(f"📥 Status: {resp.status_code}")
    
    if resp.status_code == 200:
        tokens = resp.json()
        print(f"\n✅✅✅ SUCCESS! TOKEN RECEIVED ✅✅✅")
        print(f"   Access Token: {tokens['access_token'][:40]}...")
        
        # Save
        with open('.twitter_oauth2_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"\n   💾 Tokens saved to .twitter_oauth2_tokens.json")
        
        # Test tweet
        print("\n📝 Posting test tweet...")
        tweet = "🤖 Hello World! Oracle ClawBot is LIVE! 🏆 #oraclesrun #AI"
        
        post = requests.post(
            'https://api.x.com/2/tweets',
            headers={
                'Authorization': f"Bearer {tokens['access_token']}",
                'Content-Type': 'application/json'
            },
            json={'text': tweet}
        )
        
        if post.status_code == 201:
            tid = post.json()['data']['id']
            print(f"\n🎉 SUCCESS!")
            print(f"🔗 https://x.com/oraclesrun/status/{tid}")
        else:
            print(f"❌ Test tweet failed: {post.status_code}")
    else:
        print(f"\n❌ Failed: {resp.status_code}")
        print(resp.text[:300])

if __name__ == "__main__":
    main()
