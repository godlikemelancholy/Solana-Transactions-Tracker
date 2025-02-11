# Solana-Transactions-Tracker
Parse and track all incoming transactions from your wallets list through helius

1. Install `requirements.txt`
2. Add wallets in `solana_wallets_main.csv` and `solana_wallets.csv`.
3. Setup `config.py`:

1) `HELIUS_KEY` - Helius API Key.
2) `BOT_TOKEN` - Telegram Bot Token.
3) `CHAT_ID` - Your Telegram ID, which bot will use to send alerts.
4) `MAX_SUBSCRIPTIONS` - Durability and Flexibility of parsing mode. Recommended value - 300 to 500. Increasing this value also increase parse cost on Helius.

4. Run `solana_ws.py`
   
