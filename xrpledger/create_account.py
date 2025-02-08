from xrpl.clients import JsonRpcClient
from xrpl.asyncio.wallet import generate_faucet_wallet as async_generate_faucet_wallet

async def create_account():
    JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
    client = JsonRpcClient(JSON_RPC_URL)

    # Create a wallet using the testnet faucet:
    new_wallet = await async_generate_faucet_wallet(client, debug=True)
    # Create an account str from the wallet
    return new_wallet
    