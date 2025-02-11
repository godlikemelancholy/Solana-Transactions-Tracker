import asyncio
import csv
import requests
from time import sleep
from cachetools import TTLCache
from solana.constants import LAMPORTS_PER_SOL
from solana.rpc.websocket_api import connect as ws_connect
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solders.rpc.responses import SubscriptionResult, LogsNotification
from telegram import Bot
from log import logger
from config import CSV_FILE, SOLANA_RPC_URL, HELIUS_KEY, BOT_TOKEN, CHAT_ID, MAX_SUBSCRIPTIONS

signatures = TTLCache(maxsize=200, ttl=5000)
wallet_map = {}
bot = Bot(token=BOT_TOKEN)


async def get_ws_connection():
    while True:
        try:
            return await ws_connect(SOLANA_RPC_URL, ping_timeout=60, ping_interval=10)
        except Exception as e:
            logger.error(f"Ошибка подключения к вебсокету: {e}, попытка реконнекта...")
            await asyncio.sleep(5)


async def subscribe_wallets():
    connection = await get_ws_connection()
    tasks = [asyncio.create_task(listen_ws(connection))]
    with open(CSV_FILE, mode="r") as file:
        for row in csv.DictReader(file):
            wallet_map[row["publicKey"]] = row.get("name", "")
            await subscribe_wallet(connection, row["publicKey"])
            sleep(0.1)
    await asyncio.gather(*tasks)


async def listen_ws(connection):
    while True:
        try:
            message = await connection.recv()
            if isinstance(message, LogsNotification):
                if any("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" in log for log in message.result.value.logs):
                    await parse_transaction(str(message.result.value.signature))
        except Exception as e:
            logger.error(f"Ошибка при получении сообщения: {e}, перезапуск вебсокета...")
            await connection.close()
            connection = await get_ws_connection()
            connection = await get_ws_connection()
            await asyncio.sleep(5)


async def subscribe_wallet(connection, pubkey):
    try:
        await connection.logs_subscribe(RpcTransactionLogsFilterMentions(Pubkey.from_string(pubkey)))
    except Exception as e:
        logger.error(f"Ошибка подписки {pubkey}: {e}")


async def parse_transaction(signature):
    if signature in signatures:
        return
    signatures[signature] = "processed"
    try:
        response = requests.post(
            f"https://api.helius.xyz/v0/transactions?api-key={HELIUS_KEY}",
            headers={"Content-Type": "application/json"},
            json={"transactions": [signature]}
        ).json()[0]
        description, sol, token, amount = response.get("description", ""), None, None, None
        swap = "swapped" in description
        if swap:
            sol = round(int(response["events"]["swap"]["nativeInput"]["amount"]) / LAMPORTS_PER_SOL, 2)
        for transfer in response.get("tokenTransfers", []):
            if transfer["mint"] != "So11111111111111111111111111111111111111112":
                token, amount = transfer["mint"], transfer["tokenAmount"]
        if sol:
            await send_alert(response["accountData"][0]["account"], token, sol, amount, signature)
    except Exception as e:
        logger.error(f"Ошибка при парсинге транзакции: {e}")


async def send_alert(wallet, token, sol, amount, signature):
    ticker = await get_ticker(token)
    name = wallet_map.get(wallet, "")
    text = (f"BUY\n\nName: {name}\nWallet: {wallet}\nCA: {token}\nTicker: {ticker}\n"
            f"{sol} SOL -> {amount}\n\n<a href='https://solscan.io/tx/{signature}'>txs</a>")
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML", disable_web_page_preview=True)


async def get_ticker(ca):
    try:
        response = requests.post(
            f"https://mainnet.helius-rpc.com/?api-key={HELIUS_KEY}",
            headers={"Content-Type": "application/json"},
            json={"jsonrpc": "2.0", "id": "test", "method": "getAsset", "params": {"id": ca}}
        )
        return response.json()["result"]["content"]["metadata"]["symbol"]
    except:
        return "Unknown"


async def main():
    await subscribe_wallets()

if __name__ == "__main__":
    asyncio.run(main())
