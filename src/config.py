# -*- coding: utf-8 -*-
import serial
import RPi.GPIO as GPIO  
###TESTED FOR FIRMWARE 10.00.xx4 OF GL865
MANUFACTURER='Raspberrypi'
IMEI=''
MODEL='B+'
FIRMWARE=''

#################Basic logging settings######################
DEBUG_MODE = 1 #IMP!!! Disable this on production 0/1
LOG_TO ='FILE' #[FILE,SER]. SER is Serial port. '' for Default behaviour.
MAX_LOG_SIZE = 10240 # in bytes 1024-256000 Bytes. Only valid for file logging.
#################Data Logger settings######################
ENABLE_DATA_LOGGING = 1 #1 to enable logging in case of no Server connection. 0 to Disable
DATA_LOG_UPLOAD_INTERVAL =300 #>0Seconds 
MAX_DATA_LOG_SIZE=110000 # in bytes 1024-256000 Bytes.

###############Serial Port Settings########################
SERIAL_PORTS_ENABLED = 1 # 
SERIAL_POLLING_RETRY = 2 #[0-2]No of times to retry polling if no response or error response on polling port
SERIAL_POLLING_INTERVAL = 60 # In seconds. Should be greater than 9
serial_cmd_list = []
serial_cmd_list.append(['\x00\x00', '\x01\x03\x00\x00\x00\x0C\x45\xCF']) # Enter your serial commands
serial_cmd_list.append(['\x00\x14', '\x01\x03\x00\x14\x00\x0A\x85\xC9']) # Enter your serial commands
 
serial_port = {'port' : '/dev/ttyUSB0', #port number /dev/ttyUSB0 ,/dev/ttyUSB1...
                'baudrate': 9600, #baud rate
                'parity':serial.PARITY_NONE, # Enable parity checking. Possible values: serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE
                'stopbits': serial.STOPBITS_ONE, #Number of stop bits. Possible values: serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO
                'bytesize': serial.EIGHTBITS, # Number of data bits. Possible values:  serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS,serial.EIGHTBITS
                'timeout': 3, # Set a read timeout value.
                'writeTimeout':10, # Set a write timeout value.
                'xonxoff':False, #enable software flow control 0,1
                'rtscts':False, #enable RTS/CTS flow control 0,1
                'packet_size': 3000, #Max packet size.
                'read_delay':0,
                'write_delay':0,
                'command_list': serial_cmd_list}

###############GPIO Port Settings########################
GPIO_PORTS_ENABLED = 1
GPIO_MODE=GPIO.BCM
GPIO_PORTS = [dict({'pin_number': 21,'direction': 'DO'})]  # direction Possible values: DO

####### InstaMsg Client Details ###########
ClientId = "your client id" # Enter your client_id here
AuthToken = "client auth token"  # Enter your client_auth_token here
SSL_ENABLED = 0 # or 1 for sending data over ssl

############### InstaMsg Publish/Subscribe Settings ##############
QOS=1
SUB_TOPICS = []
# this is reserved sub topics, you don't need to change this, But you can add as many sub topics as you want
GPIO_TOPIC = "instamsg/clients/" + ClientId + "/gpio"
SUB_TOPICS.append(GPIO_TOPIC)

PUB_TOPICS = []

WEBHOOK_TOPIC = "instamsg/webhook"
CONNECTIVITY ="wlan0" # if connected by lan than use eth1
