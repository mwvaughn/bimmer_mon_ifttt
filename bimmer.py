#!/usr/bin/env python3
import os
import sys
import json
import logging
import requests
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


def to_slack(settings, message,
             channel='notifications',
             icon=':electric_plug:'):

    payload = {'channel': channel,
               'icon_emoji': icon,
               'username': 'chargebot',
               'text': message}

    r = requests.post(settings.webhook,
                      data=json.dumps(payload),
                      headers={"Content-type": "application/json"})

    r.raise_for_status()


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
                logger.warning("Battery is not charging for some reason")
                send_event(settings.ifttt.api_key,
                           settings.ifttt.event,
                           value1=charging_status_human,
                           value2=battery_level,
                           value3=time_remaining)

            try:
                slack_icon = ':electric_plug:'
                if battery_level < 50:
                    slack_icon = ':warning:'
                slack_message = "Your BMW is {}.".format(charging_status_human)
                slack_message = slack_message + " Its battery is {}% full.".format(battery_level)
                if battery_level < 95:
                    slack_message = slack_message + " {} remains till fully charged.".format(time_remaining)

                # # mention car owners in Slack message if battery is low
                # if battery_level < 60:
                #     slack_message = slack_message + ' '.join(settings.slack.mentions)

                to_slack(settings.slack, slack_message, icon=slack_icon)

            except Exception as e:
                logger.warning("Failed to post to Slack: {}".format(e))

    except Exception as e:
        logger.error("Failed to iterate over vehicle state", e)
        sys.exit(1)

    exit(0)


if __name__ == '__main__':
    main()
