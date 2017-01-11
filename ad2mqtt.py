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

class AlarmState(enumerate):
    ready = 0
    notReady = 1
    armed_away = 2
    armed_stay = 3
    alarm = 4
    alarm_event = 5

class AlarmSystem():
    FirstUpdate = True       #First Update Flag
    State = 0
    Bypass = False  #Zone Bypassed 
    ACPower = False #AC Power
    Bat =   False   #Battery Low

def TFMap(boolIN):
    if boolIN:
        return 1
    else:
        return 0

serPort = '/dev/ttyS0'

# Set the Serial Port
device = AlarmDecoder(SerialDevice(interface=serPort))

client = mqtt.Client()
aAlarm = AlarmSystem()

def main():
    global client, device
    """
    Internal Variables
    """
    client = mqtt.Client()

    try:
        # Set up the AD2 Event Handlers
        device.on_zone_fault += ad_zonefault
        device.on_zone_restore += ad_zonerestore
        device.on_message += ad_message
        device.on_alarm += ad_zonealarm
        device.on_alarm_restored += ad_zonealarmrestore

        #Set up the MQTT Callbacks
        client.on_connect = mqtt_OnConnect
        client.on_message = mqtt_OnMessage

        #Connect to the MQTT server
        client.connect_async("localhost", 1883, 60)

        client.loop_start()

        with device.open(baudrate=115200):
            while True:
                time.sleep(1)

    except Exception, ex:
        print 'Exception:', ex

def ad_zonefault(sender, zone):
    global client
    client.publish("8230/alarm/zones/" + str(zone) + "/state",ZoneState.fault)

def ad_zonerestore(sender, zone):
    global client
    client.publish("8230/alarm/zones/" + str(zone) + "/state",ZoneState.ready)

def ad_zonealarm(sender, zone):
    global client
    client.publish("8230/alarm/zones/" + str(zone) + "/state",ZoneState.alarm)

def ad_zonealarmrestore(sender, zone):
    global client
    client.publish("8230/alarm/zones/" + str(zone) + "/state",ZoneState.alarmed)

def ad_message(sender, message):
    global client, aAlarm
    print sender, message

    #Update the panel message
    client.publish("8230/alarm/display",message.text,2,False)

    aNewState=0
    aSimpleState=0
    print message.ready, message.system_fault

    #Run through the variables and update as needed
    if message.ready:
        aNewState = AlarmState.ready
    elif message.armed_away:
        aNewState = AlarmState.armed_away
    elif message.armed_home:
        aNewState = AlarmState.armed_stay
    elif message.alarm_sounding:
        aNewState = AlarmState.alarm
    elif message.alarm_event_occurred:
        aNewState = AlarmState.alarm_event
    else:
        aNewState = AlarmState.notReady

    if aAlarm.State != aNewState or aAlarm.FirstUpdate:
        print "Updating Alarm State", aNewState
        aAlarm.State = aNewState
        client.publish("8230/alarm/state",aNewState,2,False)

        if aAlarm.State == AlarmState.ready and aAlarm.FirstUpdate:
            for i in range(1, 6):
                client.publish("8230/alarm/zones/" + str(i) + "/state",ZoneState.ready)

    if aAlarm.ACPower != message.ac_power or aAlarm.FirstUpdate:
        print "Update AC Power State", message.ac_power
        aAlarm.ACPower = message.ac_power
        client.publish("8230/alarm/acpower",TFMap(message.ac_power),2,False)

    if aAlarm.Bat != message.battery_low or aAlarm.FirstUpdate:
        print "Update Low Battery State", message.battery_low
        aAlarm.Bat = message.battery_low
        client.publish("8230/alarm/batlow",TFMap(message.battery_low),2,False)

    if aAlarm.Bypass != message.zone_bypassed or aAlarm.FirstUpdate:
        print "Update Zone Bypassed State", message.zone_bypassed
        aAlarm.bypass = message.zone_bypassed
        client.publish("8230/alarm/bypass",TFMap(message.zone_bypassed),2,False)

    aAlarm.FirstUpdate = False

def mqtt_OnConnect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("8230/alarm/set/state")

def mqtt_OnMessage(client, userdata, message):
    global aAlarm, device

    print("Recieved Message from Broker")
    print client, message.topic, message.payload

    if int(message.payload) != aAlarm.State:
        if int(message.payload) == AlarmState.armed_away:
            device.send(userCode+'2')
        elif int(message.payload) == AlarmState.armed_stay:
            device.send(userCode+'3')
        elif int(message.payload) == AlarmState.ready:
            device.send(usercode+'1')



if __name__ == '__main__':
    main()
