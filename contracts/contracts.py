from fastapi import APIRouter, Response, Request, Depends
from auth import auth
from database import database
from sqlalchemy.future import select
from typing import List

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
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''Creates a new contract.'''
    return

@router.get("/{contract_id}", tags=["Contracts"])
async def get_contract(
    contract_id: int, 
    request: Request, 
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract.'''
    return

@router.post("/{contract_id}/update-contract", tags=["Contracts"])
async def update_contract(
    contract_id: int,
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''Tries to update an existing contract.'''
    return

@router.post("/{contract_id}/delete-contract", tags=["Contracts"])
async def delete_contract(
    contract_id: int,
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''Deletes an existing contract.'''
    return


@router.get("/{contract_id}/{bid_id}", tags=["Bids"])
async def get_contract_bid(
    contract_id: int, 
    bid_id: int, 
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract bid.'''
    return

@router.post("/{contract_id}/create-contract-bid", tags=["Bids"])
async def create_contract_bid(
    contract_id: int,
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Creates a new contract bid.'''
    return

@router.post("/{contract_id}/{bid_id}/delete-contract-bid", tags=["Bids"])
async def create_contract_bid(
    contract_id: int,
    bid_id: int,
    request: Request, 
    response: Response, 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Deletes a contract bid.'''
    return