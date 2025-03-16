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
    Returns a list of all open contracts in a compacted form.
    Compacted == just ID and title.
    '''
    async with database.AsyncSessionLocalFactory() as session:
        open_contracts = await session.execute(
            select(database.Contract).where(
                database.Contract.contract_status == database.ContractStatus.OPEN
            )
        )

    open_contracts:List[database.Contract] = open_contracts.scalars().all()
    compact_contracts = [
        {
            "contractID": contract.contract_id,
            "title": contract.contract_title,
        } for contract in open_contracts
    ]
    return compact_contracts

@router.get("/my-contracts-all", tags=["Contracts", "Proposer", "Courier"])
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
    user_contracts: List[database.Contract] = []
    async with database.AsyncSessionLocalFactory() as session:
        # get contracts that user proposed
        user_proposed = await session.execute(
            select(database.Contract).where(
                (database.Contract.proposer_id == user)
            )
        )

        # get contracts that user accepted (to be the courier)
        user_accepted = await session.execute(
            select(database.Contract).where(
                database.Contract.courier_id == user
            )
        )

        user_proposed: List[database.Contract] = user_proposed.scalars().all()
        user_accepted: List[database.Contract] = user_accepted.scalars().all()
        user_contracts = user_proposed + user_accepted

    compact_contracts = [
        {
            "contractID": contract.contractID,
            "title": contract.title,
        } for contract in user_contracts
    ]
    return compact_contracts

@router.get("/my-contract-requests", tags=["Contracts", "Proposer"])
async def get_my_contract_requests(
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Returns a list of all contract requests affiliated with the current user.
    ie. Contracts that the user has proposed.
    '''

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
            "contractID": contract.contract_id,
            "title": contract.contract_title,
        } for contract in user_contracts
    ]
    return compact_contracts

@router.get("/my-contract-deliveries", tags=["Contracts", "Courier"])
async def get_my_contract_deliveries(
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Returns a list of all contracts the current user has accepted to deliver.
    ie.. Contracts that the user is the courier for.
    Returns in compact form (ID, Title)
    '''
    user = auth.get_current_user(request)['sub']

    async with database.AsyncSessionLocalFactory() as session:
        user_deliveries = await session.execute(
            select(database.Contract).where(
                database.Contract.courier_id == user
            )
        )
        user_deliveries: List[database.Contract] = user_deliveries.scalars().all()

        compact_bids = [
            {
            "contractID": contract.contractID,
            "title": contract.title,
            } for contract in user_deliveries
        ]
    return compact_bids

@router.post("/create-contract", tags=["Contracts", "Proposer"])
async def create_contract(
    request: Request,
    response: Response,
    title: str,
    desc: str,
    required_completion_time: str,
    collateral: int,
    base_price: int,
    t1_incentive: int,
    t2_incentive: int,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    Creates a new contract.
    Expects timeout timestamp in "%Y-%m-%dT%H:%M:%S" format.
    '''

    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        required_completion_time = datetime.strptime(
            required_completion_time,
            "%Y-%m-%dT%H:%M:%S"
        )

        new_contract = database.Contract(
            proposer_id                 =   user,
            courier_id                  =   None,
            contract_award_time         =   None,
            contract_completion_time    =   None,
            contract_timeout            =   required_completion_time,
            contract_status             =   database.ContractStatus.OPEN,
            required_collateral         =   collateral,
            base_price                  =   base_price,
            t1_bonus                    =   t1_incentive,
            t2_bonus                    =   t2_incentive,
            base_lock                   =   None,
            t1_lock                     =   None,
            t2_lock                     =   None,
            collateral_lock             =   None,
            base_key                    =   None,
            t1_key                      =   None,
            t2_key                      =   None,
            collateral_key              =   None,
            sensor_id                   =   None,
            contract_title              =   title,
            contract_desc               =   desc,
        )
        session.add(new_contract)
        await session.commit()
        await session.refresh(new_contract)
    return {"contractID": new_contract.contractID, "title": new_contract.title}

@router.get("/{contract_id}", tags=["Contracts", "Proposer", "Courier"])
async def get_contract(
    contract_id: int,
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    Returns all details of a specific contract.
    Contract has to be open, or the user has to be the proposer / courier.
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (
                    (
                        database.Contract.contract_status == database.ContractStatus.OPEN
                    ) | (
                        (database.Contract.proposer_id == user) |
                        (database.Contract.courier_id == user)
                    )
                )
            )
        )
        contract:database.Contract = contract.scalars().first()
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found"}

        retstruct = {
            "contract_id":  contract.contract_id,
            "proposer_id":  contract.proposer_id,
            "courier_id":   contract.courier_id,
            "contract_award_time": contract.contract_award_time,
            "contract_completion_time": contract.contract_completion_time,
            "contract_timeout": contract.contract_timeout,
            "contractStatus": contract.contractStatus,
            "required_collateral": contract.required_collateral,
            "base_price": contract.base_price,
            "t1_bonus": contract.t1_bonus,
            "t2_bonus": contract.t2_bonus,
            "title": contract.title,
            "description": contract.description,
        }
        return retstruct

@router.post("/{contract_id}/update-contract", tags=["Contracts", "Proposer"])
async def update_contract(
    contract_id: int,
    new_base_price: int,
    new_t1_incentive: int,
    new_t2_incentive: int,
    new_timeout: str,
    new_title: str,
    new_desc: str,
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Tries to update an existing contract's pricing structure.
    ONLY WORKS IF CONTRACT STATUS IS OPEN.
    ONLY WORKS IF USER IS PROPOSER.
    '''

    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (database.Contract.proposer_id == user) &
                (database.Contract.contract_status == database.ContractStatus.OPEN)
            )
        )
        contract: database.Contract = contract.scalars().first()
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found or not open"}

        # modify the contract to set the new values
        contract.base_price = new_base_price
        contract.t1_bonus = new_t1_incentive
        contract.t2_bonus = new_t2_incentive
        contract.contract_timeout = datetime.strptime(new_timeout, "%Y-%m-%dT%H:%M:%S")
        contract.contract_title = new_title
        contract.contract_desc = new_desc

        # commit entry back to database
        session.add(contract)
        await session.commit()

    return {"detail": "Contract updated successfully"}

@router.post("/{contract_id}/delete-contract", tags=["Contracts", "Proposer"])
async def delete_contract(
    contract_id: int,
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)):
    '''
    Deletes an existing contract.
    ONLY WORKS IF CONTRACT STATUS IS OPEN.
    ONLY WORKS IF USER IS PROPOSER.
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (database.Contract.proposer_id == user) &
                (database.Contract.contract_status == database.ContractStatus.OPEN)
            )
        )
        contract: database.Contract = contract.scalars().first()
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found or not open"}

        # delete the contract
        await session.delete(contract)
        await session.commit()
    return {"detail": "Contract deleted successfully"}

@router.post("/{contract_id}/accept-contract", tags=["Contracts", "Courier"])
async def accept_contract(
    contract_id: int,
    sensorid: int,
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    API for when a Courier accepts a contract.
    Requires Sensor to be specified.
    Only works if contract status is open.
    Locks in actual contract with the XRP network.
    '''

    user = auth.get_current_user(request)['sub']

    # TODO: XRP INTEGRATION HERE - NEED TO CREATE ESCROWS.
    TESTING_base_lock = "0x0"
    TESTING_t1_lock = "0x0"
    TESTING_t2_lock = "0x0"
    TESTING_collateral_lock = "0x0"
    TESTING_base_key = "0x0"
    TESTING_t1_key = "0x0"
    TESTING_t2_key = "0x0"
    TESTING_collateral_key = "0x0"

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

        # modify the contract to set the courier, sensor, and status
        contract.courier_id = user
        contract.sensor_id = sensorid
        contract.contract_status = database.ContractStatus.FULFILLMENT
        contract.contract_award_time = datetime.now(timezone.utc)

        # set the locks and keys in the database
        contract.base_lock = TESTING_base_lock
        contract.t1_lock = TESTING_t1_lock
        contract.t2_lock = TESTING_t2_lock
        contract.collateral_lock = TESTING_collateral_lock
        contract.base_key = TESTING_base_key
        contract.t1_key = TESTING_t1_key
        contract.t2_key = TESTING_t2_key
        contract.collateral_key = TESTING_collateral_key

        # commit entry back to database
        session.add(contract)
        await session.commit()
        await session.refresh(contract)

        # return the contract id and the updated fields
        return ({
            "contract_id": contract.contract_id,
            "courier_id": contract.courier_id,
            "sensor_id": contract.sensor_id,
            "contract_status": contract.contract_status,
            "contract_award_time": contract.contract_award_time,
        })
