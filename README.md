# Bimmer Monitor IFTTT

Monitors charge status of a BMW electric vehicle with an active Connected
Drive account and forwards the result to an IFTTT webhook. This is intended
to work as an automatable reminder to check that the car has been plugged in.

## Configure the Monitor

Either set values in config.yml or create a config file like so:

```shell
export BMW_ACCOUNT_USERNAME="my_bmw_i3@icloud.com"
export BMW_ACCOUNT_PASSWORD="connected6rivep@ssword!"
export BMW_VEHICLE_VIN=WBY1Z274C5V69471E
export BMW_IFTTT_API_KEY=UWyjI2MwYV65rxUJJKWDeX1iCnqvmhosmxnvrSYjgNo
```

## Configure an IFTTT Webhook

The monitor sends to event `charging_status` by default, and passed three
values. The first (Value1) is a phrase describing the charging state. Value2
is the percentage full and Value3 is the time remaining until full charge.

```
Your BMW battery is {{Value1}}. Charge is {{Value2}}% with {{Value3}} remaining.
```
