from xrpl.clients import JsonRpcClient
from xrpl.models import AccountObjects
from xrpl.utils import drops_to_xrp, ripple_time_to_datetime

def get_payment_history(account_addr : str):
    client = JsonRpcClient("https://s.altnet.rippletest.net:51234") # Connect to the server

    all_escrows_dict = {} 
    sent_escrows = [] 
    received_escrows = []

    # Build and make request
    req = AccountObjects(account=account_addr, ledger_index="validated", type="escrow")
    response = client.request(req)

    # Return account escrows
    escrows = response.result["account_objects"]

    # Loop through result and parse account escrows
    for escrow in escrows:
        escrow_data = {} 
        if isinstance(escrow["Amount"], str):
            escrow_data["escrow_id"] = escrow["index"]
            escrow_data["sender"] = escrow["Account"] 
            escrow_data["receiver"] = escrow["Destination"] 
            escrow_data["amount"] = str(drops_to_xrp(escrow["Amount"])) 
                
            # Sort escrows
            if escrow_data["sender"] == account_addr:
                sent_escrows.append(escrow_data)
            else:
                received_escrows.append(escrow_data)

    # Add lists to escrow dict
    all_escrows_dict["sent"] = sent_escrows
    all_escrows_dict["received"] = received_escrows

    print(all_escrows_dict)