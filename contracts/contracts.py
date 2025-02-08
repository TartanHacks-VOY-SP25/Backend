import os
from fastapi import APIRouter, Response, Request, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum
from auth import auth
from database import database


router = APIRouter()
# Routes
@router.get("/open-contracts")
def get_open_contracts(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of open contracts.'''
    return

@router.get("/my-contracts-all")
def get_my_contracts(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns a list of all contracts affiliated with the current user.'''
    return

@router.get("/my-contract-requests")
def get_my_contract_requests(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contract requests affiliated with the current user.'''
    return

@router.get("/my-contract-bids")
def get_my_contract_bids(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Returns a list of all contracts the current user has placed a bid on.'''
    return

@router.post("/create-contract")
def create_contract(
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Creates a new contract.'''
    return

@router.post("/update-contract")
def update_contract(
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Tries to update an existing contract.'''
    return

@router.post("/delete-contract")
def delete_contract(
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)):
    '''Deletes an existing contract.'''
    return

@router.get("/details/{contract_id}")
def get_contract(
    contract_id: int, 
    request: Request, 
    response: Response,
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract.'''
    return

@router.get("/details/{contract_id}/{bid_id}")
def get_contract_bid(
    contract_id: int, 
    bid_id: int, 
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Returns the details of a specific contract bid.'''
    return

@router.post("/create-contract-bid")
def create_contract_bid(
    request: Request, 
    response: Response, 
    auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''Creates a new contract bid.'''
    return

