import asyncio
import os
from datetime import datetime, timedelta, timezone
from bimmer_connected.account import MyBMWAccount
from bimmer_connected.api.regions import Regions
from bimmer_connected.vehicle.climate import ClimateActivityState
from bimmer_connected.vehicle.fuel_and_battery import ChargingState

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
REGION = Regions.NORTH_AMERICA
VIN = os.getenv('VIN')

MIN_TARGET_SOC = 50
MAX_TARGET_SOC = 70
MIN_CHARGE_HOURS = 24
MAX_CHARGE_HOURS = 48
CHECK_INTERVAL = 60 * 5

def get_target_soc(curent_soc):
    for target_soc in range(MIN_TARGET_SOC, MAX_TARGET_SOC + 1, 5):
        if target_soc >= curent_soc + 5:
            return target_soc
    return MAX_TARGET_SOC

async def main():
    account = MyBMWAccount(USERNAME, PASSWORD, REGION)
    await account.get_vehicles()
    vehicle = account.get_vehicle(VIN)
    print(vehicle.brand, vehicle.name, vehicle.vin)

    start_time = datetime.now(timezone.utc)
    ac_limits = vehicle.charging_profile.ac_available_limits

    min_end_time = start_time + timedelta(hours=MIN_CHARGE_HOURS)
    max_end_time = start_time + timedelta(hours=MAX_CHARGE_HOURS)

    print(f'Starting charging at {start_time} until between {min_end_time} and {max_end_time} with target SOC between {MIN_TARGET_SOC} and {MAX_TARGET_SOC}')

    current_target_soc = get_target_soc(vehicle.fuel_and_battery.remaining_battery_percent)
    current_ac_limit_index = ac_limits.index(vehicle.charging_profile.ac_current_limit) if vehicle.charging_profile.ac_current_limit in ac_limits else 0

    print(f'Initializing with target SOC {current_target_soc} and AC limit {ac_limits[current_ac_limit_index]}')
    result = await vehicle.remote_services.trigger_charging_settings_update(target_soc=current_target_soc, ac_limit=ac_limits[current_ac_limit_index])
    print(result.state)

    last_check = datetime.now(timezone.utc)
    while True:
        if (datetime.now(timezone.utc) - last_check).total_seconds() > CHECK_INTERVAL:
            last_check = datetime.now(timezone.utc)

            remaining_battery_percent = vehicle.fuel_and_battery.remaining_battery_percent
            print(f'Remaining battery: {remaining_battery_percent}%')
            
            charging_status = vehicle.fuel_and_battery.charging_status
            if charging_status != ChargingState.CHARGING:
                print(f'Charging status: {charging_status}')
                continue
            
            charging_end_time = vehicle.fuel_and_battery.charging_end_time.astimezone(timezone.utc)
            print(f'Charging estimated until {charging_end_time}')

            if charging_end_time < min_end_time:
                if current_ac_limit_index > 0:
                    print('Reducing AC limit')
                    current_ac_limit_index -= 1
                    result = await vehicle.remote_services.trigger_charging_settings_update(target_soc=current_target_soc, ac_limit=ac_limits[current_ac_limit_index])
                    print(result.state)
                elif vehicle.climate.activity != ClimateActivityState.COOLING:
                    print('Starting climate control')
                    result = await vehicle.remote_services.trigger_remote_air_conditioning()
                    print(result.state)
                elif current_target_soc < MAX_TARGET_SOC:
                    print('Increasing target SOC')
                    current_target_soc = get_target_soc(current_target_soc)
                    result = await vehicle.remote_services.trigger_charging_settings_update(target_soc=current_target_soc, ac_limit=ac_limits[current_ac_limit_index])
                    print(result.state)
                else:
                    print('Cannot slow down charging')
            elif charging_end_time > max_end_time:
                if vehicle.climate.activity == ClimateActivityState.COOLING:
                    print('Stopping climate control')
                    result = await vehicle.remote_services.trigger_remote_air_conditioning_stop()
                    print(result.state)
                elif current_target_soc > MIN_TARGET_SOC:
                    print('Decreasing target SOC')
                    current_target_soc = get_target_soc(current_target_soc - 10)
                    result = await vehicle.remote_services.trigger_charging_settings_update(target_soc=current_target_soc, ac_limit=ac_limits[current_ac_limit_index])
                    print(result.state)
                elif current_ac_limit_index < len(ac_limits) - 1:
                    print('Increasing AC limit')
                    current_ac_limit_index += 1
                    result = await vehicle.remote_services.trigger_charging_settings_update(target_soc=current_target_soc, ac_limit=ac_limits[current_ac_limit_index])
                    print(result.state)
                else:
                    print('Cannot speed up charging')
            else:
                print('Charging on track')

asyncio.run(main())
