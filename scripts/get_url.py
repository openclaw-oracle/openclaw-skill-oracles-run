#!/usr/bin/env python3
"""
Generate OAuth 2.0 authorization URL for Twitter/X
Usage: python3 scripts/get_url.py
"""

import json
import base64
import hashlib
import secrets
import urllib.parse

def main():
    print("="*70)
    print("🐦 TWITTER OAUTH 2.0 - AUTHORIZATION URL")
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
        if not CLIENT_ID:
            raise ValueError("TWITTER_CLIENT_ID not found in .env")
    except Exception as e:
        print(f"❌ Error loading .env: {e}")
        print("   Create .env with TWITTER_CLIENT_ID=your_id")
        return
    
    # Generate PKCE
    print("\n✅ Generating PKCE pair...")
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip('=')
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    
    # Save verifier
    with open('.pkce_verifier.txt', 'w') as f:
        f.write(verifier)
    
    print(f"   Verifier saved to .pkce_verifier.txt")
    
    # Build URL with webhook.site callback
    WEBHOOK = 'https://webhook.site/dc980780-809c-4ec9-bda2-2dccd53e5f40'
    
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': WEBHOOK,
        'scope': 'tweet.read tweet.write users.read offline.access',
        'state': 'auth',
        'code_challenge': challenge,
        'code_challenge_method': 'S256'
    }
    
    url = f"https://x.com/i/oauth2/authorize?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*70)
    print("🔗 AUTHORIZATION URL:")
    print("="*70)
    print(url)
    
    print("\n" + "="*70)
    print("⚡️ NEXT STEPS (complete within 30 seconds):")
    print("="*70)
    print("""
1. COPY the URL above
2. OPEN it in your browser
3. LOGIN to Twitter if needed
4. CLICK "Authorize app"
5. GO TO: https://webhook.site/dc980780-809c-4ec9-bda2-2dccd53e5f40
6. FIND the GET request with 'code=' parameter
7. COPY the code value (long string)
8. RUN: python3 scripts/exchange.py "YOUR_CODE"
""")
    print("="*70)

if __name__ == "__main__":
    main()
