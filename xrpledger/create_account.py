from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet

def create_account():
    JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
    client = JsonRpcClient(JSON_RPC_URL)

    # Create a wallet using the testnet faucet:
    new_wallet = generate_faucet_wallet(client, debug=True)

    # Create an account str from the wallet
    account_addr = new_wallet.address
    account_num = new_wallet.seed
    return [account_num, account_addr]
