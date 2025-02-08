from xrpl.clients import JsonRpcClient
from xrpl.models import EscrowFinish
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.wallet import Wallet
from xrpl.constants import CryptoAlgorithm
from xrpl.utils import drops_to_xrp


def finish_contract(sequences : list, conditions : list, fulfillments : list, source_acc_num : str, num_contracts : int):
    # Connect to Server
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

    for idx in range(num_contracts):
        sequence = sequences[idx]
        condition = conditions[idx] 
        fulfillment = fulfillments[idx]

        sender_wallet = Wallet.from_seed(seed=source_acc_num, algorithm=CryptoAlgorithm.ED25519)
        source_addr = sender_wallet.address

        # Build escrow finish transaction
        finish_txn = EscrowFinish(account=source_addr, owner=source_addr, offer_sequence=sequence, condition=condition, fulfillment=fulfillment)

        # Autofill, sign, then submit transaction and wait for result
        stxn_response = submit_and_wait(finish_txn, client, sender_wallet)

        # Parse response and return result
        stxn_result = stxn_response.result
        metadata = stxn_result.get("meta", {})