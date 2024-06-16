import asyncio
import os
from datetime import timezone
from bimmer_connected.account import MyBMWAccount
from bimmer_connected.api.regions import Regions

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
REGION = Regions.NORTH_AMERICA
VIN = os.getenv('VIN')

async def main():
    account = MyBMWAccount(USERNAME, PASSWORD, REGION)
    await account.get_vehicles()
    vehicle = account.get_vehicle(VIN)
    print(vehicle.brand, vehicle.name, vehicle.vin)

    result = await vehicle.remote_services.trigger_remote_air_conditioning()
    print(result.event_id, result.state, result.details)
    result = await vehicle.remote_services.trigger_charge_stop()
    print(result.event_id, result.state, result.details)

    remaining_battery_percent = vehicle.fuel_and_battery.remaining_battery_percent
    print(f'Remaining battery: {remaining_battery_percent}%')
    
    charging_status = vehicle.fuel_and_battery.charging_status
    print(f'Charging status: {charging_status}')
    
    charging_end_time = vehicle.fuel_and_battery.charging_end_time.astimezone(timezone.utc)
    print(f'Charging estimated until {charging_end_time}')

asyncio.run(main())
