from fastapi import APIRouter, Response, Request, Depends
from auth import auth
from database import database
from sqlalchemy.future import select
from sqlalchemy import DateTime
from datetime import datetime, timezone
import pytz
from typing import List
import xrpledger.smart_contracts as xrp

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
                database.Contract.contract_status == database.ContractStatus.OPEN.value
            )
        )

    open_contracts:List[database.Contract] = open_contracts.scalars().all()
    compact_contracts = [
        {
            # "contract_id": contract.contract_id,
            # "title": contract.contract_title,

            "contract_id":  contract.contract_id,
            "proposer_id":  contract.proposer_id,
            "courier_id":   contract.courier_id,
            "contract_award_time": contract.contract_award_time,
            "contract_completion_time": contract.contract_completion_time,
            "contract_timeout": contract.contract_timeout,
            "contractStatus": contract.contract_status,
            "required_collateral": contract.required_collateral,
            "base_price": contract.base_price,
            "t1_bonus": contract.t1_bonus,
            "t2_bonus": contract.t2_bonus,
            "title": contract.contract_title,
            "description": contract.contract_description,
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
            "contractID": contract.contract_id,
            "title": contract.contract_title,
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
                (database.Contract.proposer_id == user)
            )
        )
    user_contracts:List[database.Contract] = user_contracts.scalars().all()
    compact_contracts = [
        {
            # "contract_id": contract.contract_id,
            # "title": contract.contract_title,
                        "contract_id":  contract.contract_id,
            "proposer_id":  contract.proposer_id,
            "courier_id":   contract.courier_id,
            "contract_award_time": contract.contract_award_time,
            "contract_completion_time": contract.contract_completion_time,
            "contract_timeout": contract.contract_timeout,
            "contractStatus": contract.contract_status,
            "required_collateral": contract.required_collateral,
            "base_price": contract.base_price,
            "t1_bonus": contract.t1_bonus,
            "t2_bonus": contract.t2_bonus,
            "title": contract.contract_title,
            "description": contract.contract_description,
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
            # "contract_id": contract.contract_id,
            # "title": contract.contract_title,

                        "contract_id":  contract.contract_id,
            "proposer_id":  contract.proposer_id,
            "courier_id":   contract.courier_id,
            "contract_award_time": contract.contract_award_time,
            "contract_completion_time": contract.contract_completion_time,
            "contract_timeout": contract.contract_timeout,
            "contractStatus": contract.contract_status,
            "required_collateral": contract.required_collateral,
            "base_price": contract.base_price,
            "t1_bonus": contract.t1_bonus,
            "t2_bonus": contract.t2_bonus,
            "title": contract.contract_title,
            "description": contract.contract_description,


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
        required_completion_time = required_completion_time.replace(
            tzinfo=pytz.utc
        ) # Set timezone to UTC

        new_contract = database.Contract(
            proposer_id                 =   user,
            courier_id                  =   None,
            contract_award_time         =   None,
            contract_completion_time    =   None,
            contract_confirm_completion =   None,
            contract_timeout            =   required_completion_time,
            contract_status             =   database.ContractStatus.OPEN.value,
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
            contract_description        =   desc,
        )
        session.add(new_contract)
        await session.commit()
        await session.refresh(new_contract)
    return {"contract_id": new_contract.contract_id, "title": new_contract.contract_title}

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
    print(f"User: {user}")
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (
                    (
                        database.Contract.contract_status == database.ContractStatus.OPEN.value
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
            "contractStatus": contract.contract_status,
            "required_collateral": contract.required_collateral,
            "base_price": contract.base_price,
            "t1_bonus": contract.t1_bonus,
            "t2_bonus": contract.t2_bonus,
            "title": contract.contract_title,
            "description": contract.contract_description,
        }
        return retstruct

@router.post("/{contract_id}/update-contract", tags=["Contracts", "Proposer"])
async def update_contract(
    contract_id: int,
    new_base_price: int,
    new_collateral: int,
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
    dt = datetime.strptime(
        new_timeout,
        "%Y-%m-%dT%H:%M:%S"
    )
    dt = dt.replace(tzinfo=pytz.utc) 
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (database.Contract.proposer_id == user) &
                (database.Contract.contract_status == database.ContractStatus.OPEN.value)
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
        contract.required_collateral = new_collateral

        contract.contract_timeout = dt
        contract.contract_title = new_title
        contract.contract_description = new_desc

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
                (database.Contract.contract_status == database.ContractStatus.OPEN.value)
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
    sensorid: str,
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
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                database.Contract.contract_id == contract_id,
                database.Contract.contract_status == database.ContractStatus.OPEN.value
            )
        )
        contract: database.Contract = contract.scalars().first()

        sensor = await session.execute(
            select(database.Sensor).where(
                database.Sensor.sensor_id == sensorid,
                database.Sensor.owner_id == user
            )
        )
        sensor: database.Sensor = sensor.scalars().first()

        sensor_in_use = await session.execute(
            select(database.Contract).where(
                database.Contract.sensor_id == sensorid,
                database.Contract.contract_status != database.ContractStatus.COMPLETED.value
            )
        )
        sensor_in_use: database.Contract = sensor_in_use.scalars().first()
        
        
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found or not open."}
        
        if not sensor:
            response.status_code = 404
            return {"detail": "Sensor not found or not owned by user."}
        
        if sensor_in_use:
            response.status_code = 404
            return {"detail": "Sensor currently in use for other contract."}


        # modify the contract to set the courier, sensor, and status
        contract.courier_id = user
        contract.sensor_id = sensor.sensor_id
        contract.contract_status = database.ContractStatus.FULFILLMENT.value
        contract.contract_award_time = datetime.now(timezone.utc)

        # get xrp details for proposer and courier
        proposer_details = await session.execute(
            select(database.User).where(
                database.User.user_id == contract.proposer_id
            )
        )
        proposer_details: database.User = proposer_details.scalars().first()

        courier_details = await session.execute(
            select(database.User).where(
                database.User.user_id == user
            )
        )
        courier_details: database.User = courier_details.scalars().first()

        print(f"courier wallet num:{courier_details.wallet_number}")
        print(f"courier wallet addr:{courier_details.wallet_address}")
        print(f"proposer wallet num:{proposer_details.wallet_number}")
        print(f"proposer wallet addr:{proposer_details.wallet_address}")


        [sequences, conditions, fulfillments] = await xrp.create_escrow(
            proposer_details.wallet_number, 
            courier_details.wallet_address, 
            [contract.base_price, contract.t1_bonus, contract.t2_bonus], 
            False,
            contract.contract_timeout
        )

        [collateral_txid, collateral_lock, collateral_key] = await xrp.create_escrow(
            courier_details.wallet_number, 
            proposer_details.wallet_address, 
            [contract.required_collateral], 
            True,
            contract.contract_timeout
        )

        # set the locks and keys in the database
        contract.base_txn_id        = str(sequences[0])
        contract.t1_txn_id          = str(sequences[1])
        contract.t2_txn_id          = str(sequences[2])
        contract.collateral_txn_id  = str(collateral_txid[0])
        contract.base_lock          = conditions[0]
        contract.t1_lock            = conditions[1]
        contract.t2_lock            = conditions[2]
        contract.collateral_lock    = collateral_lock[0]
        contract.base_key           = fulfillments[0]
        contract.t1_key             = fulfillments[1]
        contract.t2_key             = fulfillments[2]
        contract.collateral_key     = collateral_key[0]

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

@router.post("/{contract_id}/complete-contract", tags=["Contracts", "Courier", "Proposer"])
async def complete_contract(
    contract_id: int,
    request: Request,
    response: Response,
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    '''
    API for when a contract is completed.
    Only works if contract status is FULFILLMENT.
    Finishes the contract, and releases the fund locks.
    Both the proposer and the courier have to agree to the completion. 
    '''
    user = auth.get_current_user(request)['sub']
    async with database.AsyncSessionLocalFactory() as session:
        contract = await session.execute(
            select(database.Contract).where(
                (database.Contract.contract_id == contract_id) &
                (database.Contract.contract_status == database.ContractStatus.FULFILLMENT.value)
            )
        )
        contract: database.Contract = contract.scalars().first()

        


        # check if contract exists and is in fulfillment
        if not contract:
            response.status_code = 404
            return {"detail": "Contract not found or not in fulfillment"}

        sensor_data_entry = await session.execute(
            select(database.SensorData).where(
                database.SensorData.sensor_id == contract.sensor_id
            )
        )
        sensor_data: database.SensorData = sensor_data_entry.scalars().first()
        if not sensor_data:
            print("No sensor data found...")

        # check if user is the proposer or courier
        if contract.proposer_id != user and contract.courier_id != user:
            response.status_code = 403
            return {"detail": "User is not the proposer or courier"}

        # if the user is the courier and the contract is not completed yet
        if contract.courier_id == user and contract.contract_completion_time is None:
            # Courier is the first user to mark the contract as completed
            contract.contract_completion_time = datetime.now(timezone.utc)
            session.add(contract)
            await session.commit()
            return {'detail': "Courier has marked contract as completed, waiting for proposer to confirm"}

        # if the user is the courier and the contract is already completed, error
        elif contract.courier_id == user and contract.contract_completion_time is not None:
            response.status_code = 403
            return {"detail": "Courier has already marked contract as completed"}

        # if the user is the proposer and the contract is not completed yet, error
        elif contract.proposer_id == user and contract.contract_completion_time is None:
            response.status_code = 403
            return {"detail": "Courier has not marked contract as completed yet"}

        # if the user is the proposer and the courier has already marked the contract as completed
        # proposer is confirming the completion
        contract.contract_confirm_completion = datetime.now(timezone.utc)
        contract.contract_status = database.ContractStatus.COMPLETED.value

        # get xrp details for proposer and courier
        proposer_details = await session.execute(
            select(database.User).where(
                database.User.user_id == user
            )
        )
        proposer_details: database.User = proposer_details.scalars().first()

        courier_details = await session.execute(
            select(database.User).where(
                database.User.user_id == contract.courier_id
            )
        )
        courier_details: database.User = courier_details.scalars().first()


        # TODO: Use the sensor data here to finish the contract / return collat. conditionally
        #1,2,3 as last arg mean base, t1 incentive, t2 incentive respectively
        
        # 0 means return collateral to the courier, 1 means give the courier's collateral to the proposer
        collateral_status = 0
        if(sensor_data):
            # if we have sensor data
            if (sensor_data.drop_alerts <= 2):
                # great performance, 
                await xrp.finish_contract([contract.base_txn_id, contract.t1_txn_id, contract.t2_txn_id],
                                [contract.base_lock, contract.t1_lock, contract.t2_lock],
                                [contract.base_key, contract.t1_key, contract.t2_key], 
                                proposer_details.wallet_number, 
                                3)
            elif (2 < sensor_data.drop_alerts <= 4):
                # lose tier 2, only get tier 1 and base
                await xrp.finish_contract([contract.base_txn_id, contract.t1_txn_id, contract.t2_txn_id],
                                [contract.base_lock, contract.t1_lock, contract.t2_lock],
                                [contract.base_key, contract.t1_key, contract.t2_key], 
                                proposer_details.wallet_number, 
                                2)
            elif (4 < sensor_data.drop_alerts <= 6):
                # only get base
                await xrp.finish_contract([contract.base_txn_id, contract.t1_txn_id, contract.t2_txn_id],
                                [contract.base_lock, contract.t1_lock, contract.t2_lock],
                                [contract.base_key, contract.t1_key, contract.t2_key], 
                                proposer_details.wallet_number, 
                                1)
            elif (6 < sensor_data.drop_alerts):
                # lose collateral if too many drops
                collateral_status = 1
        else:
            # default to full payout
            await xrp.finish_contract([contract.base_txn_id, contract.t1_txn_id, contract.t2_txn_id],
                                [contract.base_lock, contract.t1_lock, contract.t2_lock],
                                [contract.base_key, contract.t1_key, contract.t2_key], 
                                proposer_details.wallet_number, 
                                3)


        if(collateral_status):
            await xrp.finish_contract([contract.collateral_txn_id],
                            [contract.collateral_lock],
                            [contract.collateral_key], 
                            courier_details.wallet_number, 
                            1)
        else:
            await xrp.delete_escrow(
                courier_details.wallet_number,
                int(contract.collateral_txn_id)
            )

        # Wipes the sensor data entry
        if(sensor_data):
            sensor_data.drop_alerts = 0
            sensor_data.overtemp_alerts = 0
            sensor_data.water_events = 0
            sensor_data.longitude = 0
            sensor_data.latitude = 0
            session.add(sensor_data)


        # commit entry back to database
        session.add(contract)
        await session.commit()
        await session.refresh(contract)
        

    # return the contract id and the updated fields
    return ({
        "contract_id": contract.contract_id,
        "proposer_id": contract.proposer_id,
        "courier_id": contract.courier_id,
        "contract_status": contract.contract_status,
        "contract_completion_time": contract.contract_completion_time,
        "contract_confirm_completion": contract.contract_confirm_completion,
    })



# TODO: functionality to mark a contract as failed
# TODO: functionality to delete a contract that is in fulfillment and return funds to both parties only if both parties agree