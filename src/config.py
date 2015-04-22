# -*- coding: utf-8 -*-
import serial
import RPi.GPIO as GPIO  
###TESTED FOR FIRMWARE 10.00.xx4 OF GL865
MANUFACTURER='Raspberrypi'
# WATCH_DOG_TIMEOUT =600 #0-36000 seconds. 0 to disable
# CYCLIC_REBOOT_INTERVAL=0 #(0-86400)Interval in seconds. 0 to disable. Will force reboot after interval.
#################Network Settings#################
# SIM_DETECTION_MODE=1 #(0-2)0-"SIM Not Inserted", 1-"SIM Inserted", 2- Automatic sim detection
# SIM_PIN=''
# GPRS_APN = 'airtelgprs.com'
# GPRS_USERID = ''
# GPRS_PASSW = ''
#################Firewall Settings#################
#By default fire wall blocks all incomming connections. Add unblock rules here.
#To enable address 197.158.1.1 to 197.158.255.255 use ["197.158.1.1","255.255.0.0"]
#To enable  address "197.158.1.1" use "197.158.1.1","255.255.255.255"
FIRE_WALL_ADDRESS = []
#FIRE_WALL_ADDRESS.append(['197.158.1.1','255.255.255.255'])
#FIRE_WALL_ADDRESS.append(['197.158.1.1','255.255.0.0'])

#################Basic logging settings for gateway######################
DEBUG_MODE = 1 #IMP!!! Disable this on production 0/1
LOG_TO ='FILE' #[FILE,SER]. SER is Serial port. '' for Default behaviour.
MAX_LOG_SIZE = 10240 # in bytes 1024-256000 Bytes. Only valid for file logging.
#################NTP settings for gateway######################
NTP_SERVER='ntp.ioeye.com' #leave '' for disabling NTP
NTP_PORT=123 #default port 123
#################Data Logger settings######################
ENABLE_DATA_LOGGING = 1 #1 to enable logging in case of no Server connection. 0 to Disable
DATA_LOG_UPLOAD_INTERVAL =300 #>0Seconds 
MAX_DATA_LOG_SIZE=10240 # in bytes 1024-256000 Bytes.
###############ioEYE server setting for gateway########################
# PUBLISHER = 'TCP'  #Valid values 'HTTP' or 'TCP'
# TCP_HOST = 'test.ioeye.com'
# TCP_PORT = 8400
# HTTP_HOST = 'test.ioeye.com'
# HTTP_PORT = 80
# HTTP_URL = '/store_data'
###############Serial Port Settings########################
SERIAL_PORTS_ENABLED = 1 # 
SERIAL_POLLING_RETRY = 0 #[0-2]No of times to retry polling if no response or error response on polling port
SERIAL_PORTS = []
GPIO_PORTS = []
SERIAL_POLLING_INTERVAL = 60 # In seconds. Should be greater than 9

serial_cmd_list = []
#serial_cmd_list.append(['\x00\x03', 'This is a test...'])
serial_cmd_list.append(['\x00\x00', '\x01\x03\x00\x00\x00\x0C\x45\xCF'])
serial_cmd_list.append(['\x00\x14', '\x01\x03\x00\x14\x00\x0A\x85\xC9'])
 

####### InstaMsg Client Details ###########
ClientId = "9533d950-c88b-11e4-bf22-bc764e102b63"
PubTopic ="abc" 
# ClientId = "62513710-86c0-11e4-9dcf-a41f726775dd"
# PubTopic ="92b58550-86c0-11e4-9dcf-a41f726775dd" 
AuthKey = "AVE5DgIGycSjoiER8k33sIQdPYbJqEe3u"  

############### InstaMsg Publish/Subscribe Settings ##############
TOPIC="instamsg/webhook"
QOS=1
SSL_ENABLED = 0 # or 1 for sending data over ssl
SUB_TOPICS = []
REBOOT_TOPIC = ClientId + "/system/reboot"
SUB_TOPICS.append(REBOOT_TOPIC)
                
# Define local serial port settings
serial_port = {'port' : '/dev/ttyUSB0', #port number /dev/ttyUSB0 ,/dev/ttyUSB1...
                'baudrate': 9600, #baud rate
                'parity':serial.PARITY_NONE, # Enable parity checking. Possible values: serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
                'stopbits': serial.STOPBITS_ONE, #Number of stop bits. Possible values: serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
                'bytesize': serial.EIGHTBITS, # Number of data bits. Possible values:  serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS,serial.EIGHTBITS
                'timeout': 3, # Set a read timeout value.
                'writeTimeout':10, # Set a write timeout value.
                'xonxoff':False, #enable software flow control 0,1
                'rtscts':False, #enable RTS/CTS flow control 0,1
                'packet_size': 2000, #Max packet size.
                'command_list': serial_cmd_list}

# direction Possible values: DI , DO
GPIO_MODE=GPIO.BCM
GPIO_PORTS = [dict({'pin_number': 2,'direction': 'DI'}),
                    dict({'pin_number': 3,'direction': 'DI'}),
                    dict({'pin_number': 4,'direction': 'DI'}),
                    dict({'pin_number': 5,'direction':'DI'})] 
