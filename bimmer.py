#!/usr/bin/env python3
import os
import sys
import logging
from tacconfig import config
from pyfttt import *
from bimmer_connected.account import ConnectedDriveAccount
from bimmer_connected.country_selector import get_region_from_name

HERE = os.getcwd()

MAPPINGS = {
    'CHARGING': 'charging',
    'ERROR': 'not charging due to an error',
    'FINISHED_FULLY_CHARGED': 'completely charged',
    'FINISHED_NOT_FULL': 'done charging but not full',
    'INVALID': 'probably not charging',
    'NOT_CHARGING': 'not charging',
    'WAITING_FOR_CHARGING': 'waiting to charge'
}


def main():
    settings = config.read_config(namespace='BMW')
    logger = logging.getLogger(__file__)
    logger.debug(settings)
    logger.setLevel(settings.logs.level)
    logger.addHandler(logging.StreamHandler())

    try:
        reg = get_region_from_name(settings.account.country)
    except Exception as e:
        logger.error("Failed to get API URL", e)
        sys.exit(1)

    try:
        bc = ConnectedDriveAccount(username=settings.account.username,
                                   password=settings.account.password,
                                   region=reg)
    except Exception as e:
        logger.error("Failed to connect to BMW servers", e)
        sys.exit(1)


    try:
        for v in bc.vehicles:

            v.state.update_data()

            ts = v.state.timestamp
            last_update_reason = v.state.last_update_reason

            pos = v.state.gps_position
            charging_status = v.state.charging_status.name
            charging_status_human = MAPPINGS[charging_status]
            # cosmetic tweak to status
            if charging_status == 'INVALID':
                if last_update_reason == 'VEHICLE_SHUTDOWN':
                    charging_status_human = 'not charging though the car is parked'
                if last_update_reason == 'VEHICLE_MOVING':
                    charging_status_human = 'not charging as it is being driven'

            battery_level = v.state.charging_level_hv
            time_remaining = v.state.charging_time_remaining
            if time_remaining is None:
                time_remaining = 'Unknown'

            logger.info('Last update: {}'.format(ts))
            logger.info('Last reason: {}'.format(last_update_reason))
            logger.info('Position: {}, {}'.format(pos[0], pos[1]))
            logger.info('Charging status: {}'.format(
                charging_status))
            logger.info('Charge time remaining: {}'.format(
                time_remaining))
            logger.info('Charge percentage: {}'.format(
                battery_level))

            if charging_status in settings.when:
                logger.warning("Batter is not charging for some reason")
                send_event(settings.ifttt.api_key,
                           settings.ifttt.event,
                           value1=charging_status_human,
                           value2=battery_level,
                           value3=time_remaining)

    except Exception as e:
        logger.error("Failed to iterate over vehicle state", e)
        sys.exit(1)

    exit(0)


if __name__ == '__main__':
    main()
