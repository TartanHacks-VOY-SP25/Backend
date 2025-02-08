from datetime import datetime, timedelta
from xrpl.clients import JsonRpcClient
from xrpl.models import EscrowCreate
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.utils import datetime_to_ripple_time, xrp_to_drops
from xrpl.wallet import Wallet
from xrpl.constants import CryptoAlgorithm
from os import urandom
from cryptoconditions import PreimageSha256


def create_escrow(source_acc_num: str, dest_acc_num : str, payment_amt : list, expire_time=datetime.now() + timedelta(days=5)):
    # Connect to Server
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234") # Connect to client
    sequences = []
    conditions = []
    fulfillments = []

    # Get transfer amount
    for amount_to_escrow in payment_amt:
        # Escrow will be available to claim after 10 sec
        claim_date = datetime_to_ripple_time(datetime.now() + timedelta(seconds=10))

        # Escrow will expire after 5 days
        expiry_date = datetime_to_ripple_time(expire_time)

        # Generate a random preimage with at least 32 bytes of cryptographically-secure randomness.
        secret = urandom(32)
        # Generate cryptic image from secret
        fufill = PreimageSha256(preimage=secret)
        # Parse image and return the condition and fulfillment
        condition = str.upper(fufill.condition_binary.hex())
        conditions.append(condition)

        fulfillment = str.upper(fufill.serialize_binary().hex())
        fulfillments.append(fulfillment)

        # sender wallet object
        sender_wallet = Wallet.from_seed(seed=source_acc_num, algorithm=CryptoAlgorithm.ED25519)
        source_addr = sender_wallet.address
        # Build escrow create transaction
        create_txn = EscrowCreate(
            account=source_addr,
            amount=xrp_to_drops(int(amount_to_escrow)), 
            destination=dest_acc_num,
            finish_after=claim_date, 
            cancel_after=expiry_date,
            condition=condition)

        # Autofill, sign, then submit transaction and wait for result
        stxn_response = submit_and_wait(create_txn, client, sender_wallet)

        # Return result of transaction
        stxn_result = stxn_response.result

        sequences.append(int(stxn_result["tx_json"]["Sequence"]))

    return [sequences, conditions, fulfillments]