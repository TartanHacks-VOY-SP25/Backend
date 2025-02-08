from xrpl.account import get_balance
from xrpl.clients import JsonRpcClient

def check_balance(account_addr : int):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
    return get_balance(address=account_addr, client=client, ledger_index="validated")