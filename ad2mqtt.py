#!/usr/bin/python

import time
from alarmdecoder import AlarmDecoder
from alarmdecoder.devices import SerialDevice
from alarmdecoder import messages
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import config

class ZoneState(enumerate):
    ready = 0
    fault = 1
    alarm = 2
    alarmed = 3

class AlarmSystem():
    FirstUpdate = True          #First Update Flag
    Ready = False               #Alarm Ready Status
    Away = False                #Armed in Away
    Home = False                #Armed in Stay
    Bypass = False              #Zone Bypassed 
    Power = False               #Panel on AC Power
    LowBat =   False            #Battery Low
    AlarmOccurred = False       #An alarm has occured - system no longer sounding
    Alarm = False               #Alarm currently sounding
    Delay = False               #Alarm arm delay active
    Fire = False                #Fire alarm triggered
    Display = ''                #Pannel display

def TFMap(boolIN):
    if boolIN:
        return 1
    else:
        return 0

ad2PI = AlarmDecoder(SerialDevice(interface=config.ad2_serPort))
mqttClient = mqtt.Client()
aAlarm = AlarmSystem()

def main():
    global ad2PI, mqttClient

    try:
        # Set up the AD2 Event Handlers
        ad2PI.on_zone_fault += ad_zonefault
        ad2PI.on_zone_restore += ad_zonerestore
        ad2PI.on_message += ad_message
        ad2PI.on_alarm += ad_zonealarm
        ad2PI.on_alarm_restored += ad_zonealarmrestore

        #Set up the MQTT Callbacks
        mqttClient.on_connect = mqtt_OnConnect
        mqttClient.on_message = mqtt_OnMessage

        #Connect to the MQTT server
        mqttClient.connect_async("localhost", 1883, 60)

        mqttClient.loop_start()

        with ad2PI.open(baudrate=115200):
            while True:
                time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

def ad_zonefault(sender, zone):
    global client
    mqttClient.publish(config.ZoneAddress(zone, state), ZoneState.fault)

def ad_zonerestore(sender, zone):
    global client
    mqttClient.publish(config.ZoneAddress(zone, state), ZoneState.ready)

def ad_zonealarm(sender, zone):
    global client
    mqttClient.publish(config.ZoneAddress(zone, state), ZoneState.alarm)

def ad_zonealarmrestore(sender, zone):
    global client
    mqttClient.publish(config.ZoneAddress(zone, state), ZoneState.alarmed)

def ad_message(sender, message):
    global client, aAlarm
    print sender, message

    #Update the panel message
    mqttClient.publish(config.mqtt_PanelStatusDisplay ,message.text.strip(), 2, False)

    if message.ready and aAlarm.FirstUpdate:
    	for i in range(1, config.ad2_ZoneNumber):
        	mqttClient.publish(config.ZoneAddress(i, 'state'), ZoneState.ready)

    if aAlarm.Ready != message.ready or aAlarm.FirstUpdate:
        print "Update Alarm Ready State:", message.ready
        aAlarm.Ready = message.ready
        mqttClient.publish(config.mqtt_PanelStatusReady, TFMap(message.ready), 2, False)

    if aAlarm.Away != message.armed_away or aAlarm.FirstUpdate:
        print "Update Alarm Away State:", message.armed_away
        aAlarm.Away = message.armed_away
        mqttClient.publish(config.mqtt_PanelStatusAway, TFMap(message.armed_away), 2, False)

    if aAlarm.Home != message.armed_home or aAlarm.FirstUpdate:
        print "Update Alarm Home State:", message.armed_home
        aAlarm.Home = message.armed_home
        mqttClient.publish(config.mqtt_PanelStatusHome, TFMap(message.armed_home), 2, False)

    if aAlarm.Bypass != message.zone_bypassed or aAlarm.FirstUpdate:
        print "Update Zone Bypassed State:", message.zone_bypassed
        aAlarm.bypass = message.zone_bypassed
        mqttClient.publish(config.mqtt_PanelStatusBypass, TFMap(message.zone_bypassed), 2, False)

    if aAlarm.Power != message.ac_power or aAlarm.FirstUpdate:
        print "Update AC Power State:", message.ac_power
        aAlarm.Power = message.ac_power
        mqttClient.publish(config.mqtt_PanelStatusPower, TFMap(message.ac_power), 2, False)

    if aAlarm.AlarmOccurred != message.alarm_event_occurred or aAlarm.FirstUpdate:
        print "Update Alarm Occurred State:", message.alarm_event_occurred
        aAlarm.AlarmOccurred = message.alarm_event_occurred
        mqttClient.publish(config.mqtt_PanelStatusAlarmOccurred, TFMap(message.alarm_event_occurred), 2, False)

    if aAlarm.Alarm != message.alarm_sounding or aAlarm.FirstUpdate:
        print "Update Alarm Sounding State:", message.alarm_sounding
        aAlarm.Alarm = message.alarm_sounding
        mqttClient.publish(config.mqtt_PanelStatusAlarm, TFMap(message.alarm_sounding), 2, False)

    if aAlarm.LowBat != message.battery_low or aAlarm.FirstUpdate:
        print "Update Low Battery State:", message.battery_low
        aAlarm.LowBat = message.battery_low
        mqttClient.publish(config.mqtt_PanelStatusLowBat, TFMap(message.battery_low), 2, False)

    if aAlarm.Delay != message.entry_delay_off or aAlarm.FirstUpdate:
        print "Update Entry Delay State:", message.entry_delay_off
        aAlarm.Delay = message.entry_delay_off
        mqttClient.publish(config.mqtt_PanelStatusDelay, TFMap(message.entry_delay_off), 2, False)

    if aAlarm.Fire != message.fire_alarm or aAlarm.FirstUpdate:
        print "Update Fire Alarm State:", message.fire_alarm
        aAlarm.Fire = message.fire_alarm
        mqttClient.publish(config.mqtt_PanelStatusFire, TFMap(message.fire_alarm), 2, False)

    aAlarm.FirstUpdate = False

def mqtt_OnConnect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    mqttClient.subscribe("8230/alarm/set/State:")

def mqtt_OnMessage(client, userdata, message):
    global aAlarm, device

    print("Recieved Message from Broker")
    print client, message.topic, message.payload

    if int(message.payload) != aAlarm.State:
        if int(message.payload) == AlarmState.armed_away:
            ad2PI.send(userCode+'2')
        elif int(message.payload) == AlarmState.armed_stay:
            ad2PI.send(userCode+'3')
        elif int(message.payload) == AlarmState.ready:
            ad2PI.send(usercode+'1')



if __name__ == '__main__':
    main()
