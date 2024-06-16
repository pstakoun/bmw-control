import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from bimmer_connected.account import MyBMWAccount
from bimmer_connected.api.regions import Regions
from bimmer_connected.vehicle.fuel_and_battery import ChargingState

load_dotenv()

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
REGION = Regions.NORTH_AMERICA
VIN = os.getenv('VIN')
INTERVAL = 3600

async def main():
    last_check = None

    while True:
        if last_check is None or (datetime.now() - last_check).total_seconds() > INTERVAL:
            last_check = datetime.now()

            account = MyBMWAccount(USERNAME, PASSWORD, REGION)
            await account.get_vehicles()
            vehicle = account.get_vehicle(VIN)

            remaining_battery_percent = vehicle.fuel_and_battery.remaining_battery_percent
            print(f'Remaining battery: {remaining_battery_percent}%')
            
            charging_status = vehicle.fuel_and_battery.charging_status
            if charging_status != ChargingState.CHARGING:
                print(f'Charging status: {charging_status}')
                continue
            
            charging_end_time = vehicle.fuel_and_battery.charging_end_time
            print(f'Charging estimated until {charging_end_time}')

            print('Triggering preconditioning')
            result = await vehicle.remote_services.trigger_remote_air_conditioning()
            print(result.state)

asyncio.run(main())
