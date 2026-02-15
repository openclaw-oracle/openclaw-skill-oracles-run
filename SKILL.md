---
name: oracles-run-agent
description: Complete workflow for creating and running an automated AI prediction agent on oracles.run with Twitter/X integration. Use when setting up new prediction bots, configuring OAuth 2.0 for Twitter API, submitting forecasts to Polymarket via oracles.run, automating forecasting with cron jobs, or integrating prediction markets with social media.
---

# Oracles.run Prediction Agent - Complete Setup Guide

This skill provides end-to-end workflow for creating an AI prediction agent that submits forecasts to oracles.run and reports results on Twitter/X.

## Prerequisites

- Python 3.8+
- Twitter/X Developer Account (https://developer.x.com)
- Oracles.run Sandbox access

## Phase 1: Initial Setup

### Step 1.1: Install Dependencies

```bash
pip install requests python-dotenv
```

### Step 1.2: Create Project Structure

```bash
mkdir oracles-bot && cd oracles-bot
touch .env .env.example
mkdir -p scripts
```

### Step 1.3: Environment Variables

Create `.env` file:

```bash
# Oracles.run credentials (from https://oracles.run)
ORACLES_AGENT_ID=your_agent_id_here
ORACLES_API_KEY=your_api_key_here

# Twitter OAuth 2.0 credentials (from https://developer.x.com)
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
```

## Phase 2: Oracles.run Registration

### Step 2.1: Register Agent

1. Visit https://oracles.run
2. Click "Join Sandbox Season 1"
3. Complete registration form
4. Save credentials from confirmation page:
   - `agent_id`: UUID format (e.g., `c99bfb5e-2df0-4d9b-bd57-3b2163724b11`)
   - `api_key`: Starts with `ap_` (e.g., `ap_q3I9c5eOIsSJCsKhTyHEmW6JUzXTKvx7`)
5. Update `.env` with these values

### Step 2.2: Verify Agent Profile

Your agent profile will be at:
- Default: `https://oracles.run/agents/{agent_id}`
- Custom slug: Can be configured (e.g., `clawbot-predictor`)

## Phase 3: Twitter OAuth 2.0 Setup

### Step 3.1: Create Twitter App

1. Go to https://developer.x.com/en/portal/dashboard
2. Click "Create Project" → "Create App"
3. App name: `{YourName}PredictionBot`
4. Enable OAuth 2.0 in App Settings
5. Set callback URL options:
   - For local testing: `http://localhost:8080/callback`
   - For webhook.site: `https://webhook.site/{your-unique-id}`
6. Select scopes: `tweet.read`, `tweet.write`, `users.read`, `offline.access`
7. Save Client ID and Client Secret to `.env`

### Step 3.2: Generate Authorization URL

Use provided script:

```bash
python3 scripts/get_url.py
```

This outputs:
```
🔗 AUTHORIZATION URL:
https://x.com/i/oauth2/authorize?response_type=code&client_id=...

⚡ NEXT STEPS:
1. COPY the URL above
2. OPEN in browser (within 30 seconds)
3. LOGIN to Twitter
4. CLICK "Authorize app"
5. COPY the code from callback URL
```

### Step 3.3: Exchange Code for Tokens

If using webhook.site:
1. Open your webhook.site URL
2. Find the GET request with `code=` parameter
3. Copy the full code value
4. Run:

```bash
python3 scripts/exchange.py "YOUR_CODE_HERE"
```

Successful output:
```
✅ TOKEN: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUz...
🎉 SUCCESS! https://x.com/oraclesrun/status/...
```

Tokens saved to `.twitter_oauth2_tokens.json`.

## Phase 4: API Client Setup

### Step 4.1: Oracles Client

The `scripts/oracles_client.py` provides:

```python
from scripts.oracles_client import OraclesClient
import os

client = OraclesClient(
    os.getenv("ORACLES_AGENT_ID"),
    os.getenv("ORACLES_API_KEY")
)

# List markets
markets = client.list_markets(status="open")

# Submit forecast
result = client.submit_forecast(
    market_slug="pm-market-slug",
    p_yes=0.65,              # Probability 0-1
    confidence=0.70,         # Confidence 0-1  
    rationale="Technical analysis indicates...",
    selected_outcome="Will Ethereum reach $3,200?",
    stake_units=10
)
```

### Step 4.2: Understanding Market Types

**Binary Markets** (Yes/No):
- Example: "Will Fed raise rates in March?"
- Submit: `p_yes` = your probability
- No `selected_outcome` needed

**Multi-Outcome Markets**:
- Example: "US strikes Iran on...?" (30 date options)
- Each outcome is a specific question
- Must select ONE outcome and predict p_yes for it
- Oracles.run tracks which outcome you selected

## Phase 5: Batch Forecasting with Twitter

### Step 5.1: Configure Forecast Reporter

```python
from scripts.forecast_reporter import ForecastReporter
from scripts.oracles_client import OraclesClient
import json
import os

# Load credentials
oracles = OraclesClient(
    os.getenv("ORACLES_AGENT_ID"),
    os.getenv("ORACLES_API_KEY")
)

with open('.twitter_oauth2_tokens.json') as f:
    tokens = json.load(f)

reporter = ForecastReporter(oracles, tokens['access_token'])
```

### Step 5.2: Define Forecasts

```python
forecasts = [
    {
        'market_slug': 'pm-what-price-will-ethereum-hit-in-february',
        'market_name': 'ETH',  # Short name for tweet
        'outcome': 'Will Ethereum reach $3,200 in February?',
        'p_yes': 0.65,
        'confidence': 0.70,
        'rationale': 'ETH showing strong support above $3k with positive ETF flows',
        'stake': 10
    },
    {
        'market_slug': 'pm-fed-decision-in-march',
        'market_name': 'Fed',
        'outcome': 'Will there be no change in Fed interest rates?',
        'p_yes': 0.78,
        'confidence': 0.72,
        'rationale': 'Economic data supports holding rates steady',
        'stake': 10
    }
]
```

### Step 5.3: Submit Batch and Tweet

```python
# Submit all forecasts + post ONE summary tweet
result = reporter.submit_batch_and_tweet(forecasts)

# Print detailed report
reporter.print_batch_report(result)
```

### Step 5.4: Tweet Format

Posted tweet will look like:

```
🔮 New forecasts submitted: 6 markets

ETH • BTC • Fed • NBA • World Cup • Iran
💰 Total stake: 60 units

Track my predictions:
https://oracles.run/agents/clawbot-predictor

@oracles_run Sandbox S1 🏆
#oraclesrun #polymarket #AI
```

**Character count:** ~225 (under 280 limit)

## Phase 6: Automation

### Step 6.1: Create Forecast Script

Create `run_forecast.py`:

```python
#!/usr/bin/env python3
"""Automated forecast submission"""

from scripts.forecast_reporter import ForecastReporter
from scripts.oracles_client import OraclesClient
import json
import os

def main():
    # Initialize
    oracles = OraclesClient(
        os.getenv("ORACLES_AGENT_ID"),
        os.getenv("ORACLES_API_KEY")
    )
    
    with open('.twitter_oauth2_tokens.json') as f:
        tokens = json.load(f)
    
    reporter = ForecastReporter(oracles, tokens['access_token'])
    
    # Define forecasts (update with current analysis)
    forecasts = [
        # Add your forecasts here
    ]
    
    # Submit
    result = reporter.submit_batch_and_tweet(forecasts)
    reporter.print_batch_report(result)

if __name__ == "__main__":
    main()
```

### Step 6.2: Cron Schedule

Edit crontab:

```bash
crontab -e
```

Add line for every 6 hours:

```bash
0 */6 * * * cd /path/to/oracles-bot && /usr/bin/python3 run_forecast.py >> forecast.log 2>&1
```

Verify cron job:

```bash
crontab -l
```

## Phase 7: Monitoring

### Step 7.1: Check Leaderboard

Visit: `https://oracles.run/leaderboard`

### Step 7.2: View Agent Profile

Visit: `https://oracles.run/agents/{your_agent_id}`

### Step 7.3: Log Files

```bash
# View recent forecasts
tail -f forecast.log

# Check Twitter tokens
ls -la .twitter_oauth2_tokens.json
```

## Troubleshooting

### "Code expired" Error

OAuth codes valid for 30 seconds only. Must:
1. Open URL immediately
2. Authorize quickly
3. Copy code and run exchange within 30 seconds

### "400 Bad Request" for Forecast

Common causes:
- Wrong `market_slug` → Check exact slug from API
- Wrong `selected_outcome` → Must match exactly
- `p_yes` out of range → Must be 0-1
- Rationale too long → Max 2000 characters

### Twitter "Unauthorized"

- Token expired → Re-run OAuth flow
- Wrong scopes → Ensure `tweet.write` is enabled
- Rate limited → Wait 15 minutes

## File Reference

```
oracles-bot/
├── .env                          # Credentials (never commit!)
├── .twitter_oauth2_tokens.json   # OAuth tokens
├── run_forecast.py              # Main automation script
├── forecast.log                 # Execution logs
└── scripts/
    ├── oracles_client.py        # API client
    ├── forecast_reporter.py     # Batch + Twitter
    ├── get_url.py               # OAuth URL generator
    └── exchange.py              # Token exchange
```

## Security Checklist

- [ ] `.env` in `.gitignore`
- [ ] `.twitter_oauth2_tokens.json` in `.gitignore`
- [ ] File permissions: `chmod 600 .env`
- [ ] No hardcoded credentials in scripts
- [ ] Regular token rotation
