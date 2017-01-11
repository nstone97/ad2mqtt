#!/bin/python
"""
Serial Port & Number of Zones
"""
ad2_serPort = '/dev/ttyS0'
ad2_ZoneNumber = 6

"""
MQTT Broker
"""
mqtt_BrokerAddress = 'localhost'
mqtt_BrokerPort = 1883
mqtt_timeout = 60


"""
MQTT Addresses
"""
mqtt_Prefix = "alarm/"

mqtt_PanelStatusReady = mqtt_Prefix + "status/ready"
mqtt_PanelStatusAway = mqtt_Prefix + "status/away"
mqtt_PanelStatusHome = mqtt_Prefix + "status/home"
mqtt_PanelStatusBypass = mqtt_Prefix + "status/bypass"
mqtt_PanelStatusPower = mqtt_Prefix + "status/acpower"
mqtt_PanelStatusAlarmOccurred = mqtt_Prefix + "status/alarmed"
mqtt_PanelStatusAlarm = mqtt_Prefix + "status/alarm"
mqtt_PanelStatusLowBat = mqtt_Prefix + "status/lowbat"
mqtt_PanelStatusDelay = mqtt_Prefix + "status/delay"
mqtt_PanelStatusFire = mqtt_Prefix + "status/fire"
mqtt_PanelStatusDisplay = mqtt_Prefix + "display"

"""
Zone Builder
"""

def ZoneAddress(zone, strSuffix):
    global mqtt_Prefix
    mqtt_ZonePrefix = "zone"
    return mqtt_Prefix + mqtt_ZonePrefix + str(zone) + "/" + strSuffix


"""
Alarm Code - allows arming/disarming remotely
!!!!! MAKE SURE YOUR MQTT BROKER IS SECURE  !!!!!
!!!!! BEFORE ENABLING THIS                  !!!!!
"""

boolAllowSend = False       #Set this to true if you want to be able to arm/disarm remotely
intAlarmCode = 0000
