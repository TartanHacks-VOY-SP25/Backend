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
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of open contracts.'''
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
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns a list of all contracts affiliated with the current user.'''
    return

@router.get("/my-contract-requests", tags=["Contracts"])
async def get_my_contract_requests(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contract requests affiliated with the current user.'''
    return

@router.get("/my-contract-bids", tags=["Bids"])
async def get_my_contract_bids(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contracts the current user has placed a bid on.'''
    return

@router.post("/create-contract", tags=["Contracts"])
async def create_contract(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Creates a new contract.'''
    return

@router.get("/{contract_id}", tags=["Contracts"])
async def get_contract(
    contract_id: int, 
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract.'''
    return

@router.post("/{contract_id}/update-contract", tags=["Contracts"])
async def update_contract(
    contract_id: int,
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Tries to update an existing contract.'''
    return

@router.post("/{contract_id}/delete-contract", tags=["Contracts"])
async def delete_contract(
    contract_id: int,
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Deletes an existing contract.'''
    return


@router.get("/{contract_id}/{bid_id}", tags=["Bids"])
async def get_contract_bid(
    contract_id: int, 
    bid_id: int, 
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract bid.'''
    return

@router.post("/{contract_id}/create-contract-bid", tags=["Bids"])
async def create_contract_bid(
    contract_id: int,
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Creates a new contract bid.'''
    return

@router.post("/{contract_id}/{bid_id}/delete-contract-bid", tags=["Bids"])
async def create_contract_bid(
    contract_id: int,
    bid_id: int,
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Deletes a contract bid.'''
    return