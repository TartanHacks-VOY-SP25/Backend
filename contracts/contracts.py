from fastapi import APIRouter, Response, Request, Depends
from auth import auth
from database import database
from sqlalchemy.future import select
from sqlalchemy import DateTime
from typing import List
from datetime import datetime
from datetime import timezone

router = APIRouter()

# Routes
@router.get("/open-contracts", tags=["Contracts"])
async def get_open_contracts(
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Returns a list of open contracts in a compacted form.
    Compacted == just ID and title.
    '''
    async with database.AsyncSessionLocalFactory() as session:
        open_contracts = await session.execute(
            select(database.Contract).where(
                database.Contract.contractStatus == database.ContractStatus.OPEN
            )
        )
        
    open_contracts:List[database.Contract] = open_contracts.scalars().all()
    compact_contracts = [
        {
            "contractID": contract.contractID,
            "title": contract.title,
        } for contract in open_contracts
    ]
    return compact_contracts

@router.get("/my-contracts-all", tags=["Contracts"])
async def get_my_contracts(
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    Returns a list of all contracts affiliated with the current user.
    This is both contracts proposed by the user, as well as contracts bidded on by the user.
    Returns in compact form (ID, Title)
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        user_contracts = await session.execute(
            select(database.Contract).where(
                (database.Contract.proposerID == user) 
            )
        )

        # get users bids, and then use embedded contractID to get the contracts those bids are associated with
        user_bids = await session.execute(
            select(database.Bid).where(
            database.Bid.bidderID == user
            )
        )
        user_bids: List[database.Bid] = user_bids.scalars().all()
        bid_contract_ids = [bid.contractID for bid in user_bids]

        bid_contracts = await session.execute(
            select(database.Contract).where(
            database.Contract.contractID.in_(bid_contract_ids)
            )
        )
        bid_contracts: List[database.Contract] = bid_contracts.scalars().all()
    user_contracts = user_contracts.scalars().all()
    user_contracts.extend(bid_contracts)
    compact_contracts = [
        {
            "contractID": contract.contractID,
            "title": contract.title,
        } for contract in user_contracts
    ]
    return compact_contracts

@router.get("/my-contract-requests", tags=["Contracts"])
async def get_my_contract_requests(
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contract requests affiliated with the current user.'''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        user_contracts = await session.execute(
            select(database.Contract).where(
                (database.Contract.proposerID == user) 
            )
        )
    user_contracts:List[database.Contract] = user_contracts.scalars().all()
    compact_contracts = [
        {
            "contractID": contract.contractID,
            "title": contract.title,
        } for contract in user_contracts
    ]
    return compact_contracts

@router.get("/my-contract-bids", tags=["Bids"])
async def get_my_contract_bids(
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contracts the current user has placed a bid on.'''
    user = auth.get_current_user(request)['sub']

    async with database.AsyncSessionLocalFactory() as session:
        user_bids = await session.execute(
                select(database.Bid).where(
                database.Bid.bidderID == user
                )
            )
        user_bids: List[database.Bid] = user_bids.scalars().all()
        bidded_contract_ids = [bid.contractID for bid in user_bids]

        # query contracts table with contract IDs in bidded_contract_ids
        bidded_contracts = await session.execute(
            select(database.Contract).where(
            database.Contract.contractID.in_(bidded_contract_ids)
            )
        )
        bidded_contracts: List[database.Contract] = bidded_contracts.scalars().all()

        compact_bids = [
            {
            "contractID": contract.contractID,
            "title": contract.title,
            } for contract in bidded_contracts
        ]
    return compact_bids

@router.post("/create-contract", tags=["Contracts"])
async def create_contract(
    request: Request, 
    response: Response,
    biddingExpiryTime: str,
    bidSelectionExpiryTime: str,
    title: str,
    desc: str,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Creates a new contract.
    Expects timestamps in "%Y-%m-%dT%H:%M:%S" format.
    '''
    
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        bidding_expiry_time = datetime.strptime(biddingExpiryTime, "%Y-%m-%dT%H:%M:%S")
        bid_selection_expiry_time = datetime.strptime(bidSelectionExpiryTime, "%Y-%m-%dT%H:%M:%S")

        new_contract = database.Contract(
            proposerID=user,
            biddingExpiryTime=bidding_expiry_time,
            biddingSelectionExpiryTime=bid_selection_expiry_time,
            title=title,
            description=desc,
            contractStatus=database.ContractStatus.OPEN
        )
        session.add(new_contract)
        await session.commit()
        await session.refresh(new_contract)
    return {"contractID": new_contract.contractID, "title": new_contract.title}

@router.get("/{contract_id}", tags=["Contracts"])
async def get_contract(
    contract_id: int, 
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    Returns all details of a specific contract.
    If requested by the owner of this contract (the payer),
    all affiliated bid Ids will be returned. If requested by anyone else,
    only bids submitted by that user will be returned. 
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
            database.Contract.contractID == contract_id
            )
        )
        contract:database.Contract = contract.scalars().first()
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found"}

        retstruct = {
            "contractID": contract.contractID,
            "proposerID": contract.proposerID,
            "biddingExpiryTime": contract.biddingExpiryTime,
            "biddingSelectionExpiryTime": contract.biddingSelectionExpiryTime,
            "title": contract.title,
            "description": contract.description,
            "contractStatus": contract.contractStatus
        }
        # query bids table for all affiliated bids, and if requestor is proposer
        # return all of them. If requestor is a bidder, return only theirs.
        bids = await session.execute(
            select(database.Bid).where(
                database.Bid.contractID == contract_id
            )
        )
        bids: List[database.Bid] = bids.scalars().all()
        if contract.proposerID == user:
            retstruct["bids"] = [bid.bidID for bid in bids]
        else:
            retstruct["bids"] = [bid.bidID for bid in bids if bid.bidderID == user]
        return retstruct

@router.get("/{contract_id}/{bid}/complete", tags=["Contracts", "Bids"])
async def complete_contract(
    contract_id: int,
    bid_id: int,
    request: Request,
    response: Response):
    '''
    Shipping partner needs to be able to mark a contract as completed. 
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract_result = await session.execute(
            select(database.Contract).where(
                database.Contract.contractID == contract_id 
            )
        )
        contract = contract_result.scalar_one_or_none()

        if not contract:
            response.status_code = 404
            return {"error": "Contract not found"}

        bid_result = await session.execute(
            select(database.Bid).where(
                database.Bid.bidID == bid_id
            )
        )
        bid = bid_result.scalar_one_or_none()

        if not bid:
            response.status_code = 404
            return {"error": "Bid not found"}

        if bid.contractID != contract.contractID:
            response.status_code = 400
            return {"error": "Bid does not belong to the specified contract"}

        # bid and contract match, mark contract as completed
        contract.contractStatus = database.ContractStatus.COMPLETED
        contract.contractCompletionTime = datetime.utcnow()
        session.add(contract)
        await session.commit()

        # TODO: calculate incentive boost using sensor records between 
        # contract award time and contract completion time

        # TODO: issue payout

        return {"message": "Contract marked as completed successfully"}

@router.get("/{contract_id}/{bid_id}", tags=["Bids"])
async def get_contract_bid(
    contract_id: int, 
    bid_id: int, 
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract bid.'''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        bid = await session.execute(
            select(database.Bid).where(
            database.Bid.contractID == contract_id,
            database.Bid.bidID == bid_id
            )
        )
        bid: database.Bid = bid.scalars().first()
        if not bid:
            response.status_code = 404
            return {"detail": "Bid not found"}

        return {
            "bidID": bid.bidID,
            "contractID": bid.contractID,
            "bidderID": bid.bidderID,
            "floorPrice": bid.bidFloorPrice,
            "incentives": bid.incentives,
            "timestamp": bid.bidTime
        }
    return

@router.post("/{contract_id}/create-contract-bid", tags=["Bids"])
async def create_contract_bid(
    contract_id: int,
    base_price: int,
    incentives: str,
    sensorid: int,
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    Creates a new contract bid and places it on the specified contract id.
    Requires sensor id to be specified.
    Only works if contract status is open.
    Incentives should be formatted as INT-INT-INT-INT.
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                database.Contract.contractID == contract_id,
                database.Contract.contractStatus == database.ContractStatus.OPEN
            )
        )
        contract: database.Contract = contract.scalars().first()
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found or not open"}

        new_bid = database.Bid(
            bidderID=user,
            contractID=contract_id,
            bidFloorPrice=base_price,
            incentives=incentives,
            bidStatus=database.BidStatus.OPEN,
            sensorID = str(sensorid), 
            #TODO: validation needs to happen that the sensor belongs to the user but skip for now
            bidTime=datetime.now()
        )
        session.add(new_bid)
        await session.commit()
        await session.refresh(new_bid)
    return {"bidID": new_bid.bidID, "contractID": new_bid.contractID}

@router.post("/{contract_id}/{bid_id}/accept", tags=["Bids"])
async def accept_contract_bid(
    contract_id: int,
    bid_id: int,
    request: Request,
    _auth:None=Depends(auth.check_and_renew_access_token)
):
    '''
    Contract Owner needs to be able to accept a bid on a contract.
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:

        # mark bid as accepted
        bid_result = await session.execute(
            select(database.Bid).where(
                database.Bid.bidID == bid_id,
                database.Bid.contractID == contract_id
            )
        )
        bid:database.Bid = bid_result.scalar_one_or_none()
        if not bid:
            return {"error": "Bid not found"}

        bid.bidStatus = database.BidStatus.ACCEPTED
        session.add(bid)
        await session.commit()
        await session.refresh(bid)

        #update contract fields
        contract = await session.execute(
            select(database.Contract).where(
                database.Contract.contractID == contract_id
            )
        )
        contract:database.Contract = contract.scalar_one_or_none()
        
        if not contract:
            return {"error": "Contract not found"}

        contract.contractStatus    = database.ContractStatus.IN_PROGRESS
        contract.contractAwardTime = datetime.now()
        session.add(contract)
        await session.commit()
        await session.refresh(contract)

        # get wallet info for transaction
        payer_user   = await session.execute(select(database.User).where(database.User.userID == contract.proposerID))
        shipper_user = await session.execute(select(database.User).where(database.User.userID == bid.bidderID))
        payer_user:database.User    = payer_user.scalar_one_or_none()
        shipper_user:database.User  = shipper_user.scalar_one_or_none() 





    # account number of contract owner
    # account number of winnning bid owner
    # list of payment amounts (base price)
        
        

    return {"message": "Bid accepted successfully"}


@router.post("/{contract_id}/{bid_id}/reject", tags=["Bids"])
async def reject_contract_bid(
    contract_id: int,
    bid_id: int,
    _auth:None=Depends(auth.check_and_renew_access_token)
):
    '''
    Contract Owner needs to be able to dismiss / reject a bid on a contract
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:

        # mark bid as accepted
        bid_result = await session.execute(
            select(database.Bid).where(
                database.Bid.bidID == bid_id,
                database.Bid.contractID == contract_id
            )
        )
        bid = bid_result.scalar_one_or_none()
        if not bid:
            return {"error": "Bid not found"}

        bid.bidStatus = BidStatus.REJECTED
        session.add(bid)
        await session.commit()
        await session.refresh(bid)
    return


# @router.post("/{contract_id}/{bid_id}/delete-contract-bid", tags=["Bids"])
# async def delete_contract_bid(
#     contract_id: int,
#     bid_id: int,
#     request: Request, 
#     response: Response, 
#     _auth: None=Depends(auth.check_and_renew_access_token)
#     ):
#     '''
#     Deletes a contract bid. NOT YET IMPLEMENTED.
#     '''

#     return