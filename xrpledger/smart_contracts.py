from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models import EscrowFinish
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet
from xrpl.constants import CryptoAlgorithm
from xrpl.models import EscrowCreate
from datetime import datetime, timedelta
from xrpl.utils import datetime_to_ripple_time, xrp_to_drops
from os import urandom
from cryptoconditions import PreimageSha256
from xrpl.models import EscrowCancel
from xrpl.transaction import submit_and_wait
from xrpl.account import get_balance

def create_account():
    JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
    client = JsonRpcClient(JSON_RPC_URL)

    new_wallet = generate_faucet_wallet(client, debug=True)

    account_addr = new_wallet.address
    account_num = new_wallet.seed
    return [account_num, account_addr]

def finish_contract(sequences : list, conditions : list, fulfillments : list, source_acc_num : str, num_contracts : int):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

    for idx in range(num_contracts):
        sequence = sequences[idx]
        condition = conditions[idx] 
        fulfillment = fulfillments[idx]

        sender_wallet = Wallet.from_seed(seed=source_acc_num, algorithm=CryptoAlgorithm.ED25519)
        source_addr = sender_wallet.address

        finish_txn = EscrowFinish(account=source_addr, owner=source_addr, offer_sequence=sequence, condition=condition, fulfillment=fulfillment)

        txn_response = submit_and_wait(finish_txn, client, sender_wallet)

        stxn_result = txn_response.result

def create_escrow(source_acc_num: str, dest_acc_num : str, payment_amt : list, expire_time=datetime.now() + timedelta(days=5)):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234") # Connect to client
    sequences = []
    conditions = []
    fulfillments = []

    for amount_to_escrow in payment_amt:
        claim_date = datetime_to_ripple_time(datetime.now() + timedelta(seconds=10))

        expiry_date = datetime_to_ripple_time(expire_time)

        secret = urandom(32)

        fufill = PreimageSha256(preimage=secret)

        condition = str.upper(fufill.condition_binary.hex())
        conditions.append(condition)

        fulfillment = str.upper(fufill.serialize_binary().hex())
        fulfillments.append(fulfillment)


        sender_wallet = Wallet.from_seed(seed=source_acc_num, algorithm=CryptoAlgorithm.ED25519)
        source_addr = sender_wallet.address

        create_txn = EscrowCreate(
            account=source_addr,
            amount=xrp_to_drops(int(amount_to_escrow)), 
            destination=dest_acc_num,
            finish_after=claim_date, 
            cancel_after=expiry_date,
            condition=condition)

        txn_response = submit_and_wait(create_txn, client, sender_wallet)

        txn_result = txn_response.result

        sequences.append(int(txn_result["tx_json"]["Sequence"]))

    return [sequences, conditions, fulfillments]

def delete_escrow(source_acc_num: str, sequence : str):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234") # Connect to client

    sender_wallet = Wallet.from_seed(seed=source_acc_num, algorithm=CryptoAlgorithm.ED25519)
    source_addr = sender_wallet.address

    cancel_txn = EscrowCancel(account=source_addr, owner=source_addr, offer_sequence=sequence)

    stxn_response = submit_and_wait(cancel_txn, client, sender_wallet)

def check_balance(account_addr : int):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
    return get_balance(address=account_addr, client=client, ledger_index="validated")


