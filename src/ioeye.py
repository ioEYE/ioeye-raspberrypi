import instamsg
import sys
import time
import serial
import config
import exceptions
import thread
import os

SER =None
GPIo =None
InstamsgConnected =False
def start(args):
    instaMsg = None
    try:
        try:
            options={'logLevel':instamsg.INSTAMSG_LOG_LEVEL_DEBUG, 'enableSsl':config.SSL_ENABLED}
            instaMsg = instamsg.InstaMsg(config.ClientId, config.AuthKey, __onConnect, __onDisConnect, __oneToOneMessageHandler, options)
            instaMsg.start()
            while 1:
                if(SER is not None):
                    SER.process()
                if(GPIo is not None):
                    GPIo.process()
                time.sleep(10)
        except:
            print("Unknown Error in start: %s %s" %(str(sys.exc_info()[0]),str(sys.exc_info()[1])))
    finally:
        if(instaMsg):
            instaMsg.close()
            instaMsg = None
            GPIO.cleanup()  
            
def __onConnect(instaMsg):
    global SER ,InstamsgConnected,GPIo
    InstamsgConnected =True
    if (config.DEBUG_MODE): print "Client connected to Instamsg"
    for topic in config.SUB_TOPICS:
        __subscribe(instaMsg, topic, 1)
    broker =Broker(instaMsg)
    if(config.SERIAL_PORTS_ENABLED):
        SER =Serial(instaMsg,broker)
    if(config.GPIO_PORTS_ENABLED):
        GPIo = Gpio(instaMsg,broker)
    
def __onDisConnect():
    global InstamsgConnected
    InstamsgConnected =False
    print "Client disconnected."
      
def __messageHandler(mqttMessage):
    
    if(mqttMessage and config.DEBUG_MODE):print "Received message %s" %str(mqttMessage.toString())
    topic = mqttMessage.topic()
    if(topic==config.REBOOT_TOPIC):
        __rebootRaspberry()
    if(topic==config.GPIO_TOPIC):
        GPIo._handleMsg(mqttMessage)
        
def __oneToOneMessageHandler(msg):
    if(msg):
        if (config.DEBUG_MODE): print "One to One Message received %s" % msg.toString()
        msgBytes = __unhexelify(msg.body())
        Serial.processCmd(msgBytes)
        
def __subscribe(instaMsg, topic, qos):
    try:
        def _resultHandler(result):
            if (config.DEBUG_MODE): print "Subscribed to topic %s with qos %d" %(topic,qos)
        instaMsg.subscribe(topic, qos, __messageHandler, _resultHandler)
    except Exception, e:
        print str(e)
        
def __rebootRaspberry():
    try:
        if (config.DEBUG_MODE): print 'Rebooting Raspberry Pi'
        os.system("reboot")
    except Exception, e:
        print str(e)
        
def __unhexelify(data):
        a = []
        for i in range(0, len(data), 2):
            a.append(chr(int(data[i:i + 2], 16)))   
        return ''.join(a) 


class SerialError(exceptions.IOError):
    def __init__(self, value=''):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SerialTimeoutError(exceptions.IOError):
    def __init__(self, value=''):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
error=SerialError
timeout=SerialTimeoutError

class Serial:
    
    PORTS = ('/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3')
    BAUDRATES = ('300','1200','2400','4800','9600','19200','38400','57600','115200')
    BYTESIZES = (serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS,serial.EIGHTBITS)
    PARITIES  = (serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD, serial.PARITY_MARK, serial.PARITY_SPACE)
    STOPBITS  = (serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO)
    FLOWCONTROL=(True,False)
    
    def __init__(self, instamsg=None,broker = None):
        settings = config.serial_port
        self.portId=str(settings.get('port'))
        self.timeout = int(settings.get('timeout'))*10
        if(self.timeout>10 or self.timeout < 0): self.timeout=10
        self.xonxoff=int(settings.get('xonxoff'))
        self.rtscts=int(settings.get('rtscts'))
        self.commandlist = settings.get('command_list')
        self.pollingRetry = self.__getPollingRetry()
        self.instamsg =instamsg
        self.broker =broker
        instamsg.subscribe(self.portId,1, self.processCmd, self.subscribehandler)
        self.flowControl = self.__getFlowControl()
        self.port = self.__configurePort(settings)
        self.lock = thread.allocate_lock()
        self.address =config.ClientId
#         if (config.DEBUG_MODE):
#                 debugLogger =self.__setDebugLogger()

    def process(self):
        dataList = []
        try:
            if self.port:
                self.broker._publishLogData()
                if (self.commandlist):
                    for cmd in self.commandlist:
                        try:
                            data = self.pollPort(cmd[1], self.pollingRetry)
                            if(data):
                                if (config.DEBUG_MODE):
                                    print("Serial Processor: Read serial data: %s" % data)
                                dataList.append([self.broker.getTimeAndOffset(),str(cmd[0]) + str(data)])
                        except:
                            pass
            if dataList:
                if (config.DEBUG_MODE):
                    print("Serial Processor: Sending serial data...")
                self.publish(dataList)
        except:
            print('Serial:: Unexpected error in process. %s %s' % (str(sys.exc_info()[0]), str(sys.exc_info()[1])))

    
    def processCmd(self,cmd):
        try:
            self.write(cmd)
        except:
            if (config.DEBUG_MODE): print('Serial:: Unable to write cmd [%s] to serial port'%str(cmd))
    
    def subscribehandler(self,result):
        try:
            if (config.DEBUG_MODE):
                if(result.failed()):print('Serial:: Unable to subscribe to serial port due to  [%s] '%str(result.cause()))
                else: print('Serial:: subscribe to serial port')
        except:
            if (config.DEBUG_MODE): print('Serial::  subscribe to serial port  ')
           
    def read(self, size=1):
        if self.port is None: raise error('Port not open')
        timeout = time.time() + self.timeout
        res =''
        while((len(res) < size) and (time.time() < timeout)):
            res =  res + self.port.read()
        return res
    
    def write(self, data):
        if self.port is None: raise error('Port not open')
        resp = self.port.write(data)
        if resp < 0: raise error("Write timeout")
        
    def readline(self,eol='\r'):
        if self.port is None: raise error('Port not open')
        res = ''
        timeout = time.time() + self.timeout
        res =  chr(self.port.readline())
        while( res.find(eol) < 0 and (time.time() < timeout)):
            res = res +  chr(self.port.readline())
        return res
    
    def close(self):
        try:
            if self.port is None: raise error('Port not open')
            self.port.close()
        except:
            pass # ignore errors here   
        
    def pollPort(self, cmd, retry=1):
        for i in range(retry):
            try:
                if cmd:
                    if (config.DEBUG_MODE):
                        print('Serial Processor: Writing "%s" to serial port %s.Try %d...' % (str(cmd), self.portId,i))
                    self.write(cmd)
                    if (config.DEBUG_MODE):
                        print("Serial Processor: Reading from serial port %s..." % self.portId)
#                     if self.readDelay:
#                         time.sleep(self.readDelay)
#                     if self.connectionType == 'EOL':
#                         data = self.readline(eol=self.settings.get('eol_char'))
#                     else:
#                         data = self.read(int(self.settings.get('packet_size')))
                    data = self.read(int(config.serial_port.get('packet_size')))
                    if (config.DEBUG_MODE):
                        print('Serial Processor: Read serial port raw data: %s'  % str(data))
                    if(data): break
            except Exception, e:
                if (config.DEBUG_MODE):
                    print("Serial Processor: Serial port error: " %(str(sys.exc_info()[0]), str(sys.exc_info()[1])))    
        return data
    
        
    def __configurePort(self,settings):
        try:
            if str(settings.get('baudrate')) not in self.BAUDRATES: raise ValueError("Not a valid baudrate: %s" % str(settings.get('baudrate')))
            if settings.get('bytesize') not in self.BYTESIZES: raise ValueError("Not a valid byte size: %s" % str(settings.get('bytesize')))
            if settings.get('parity') not in self.PARITIES: raise ValueError("Not a valid parity: %s" % str(settings.get('parity')))
            if settings.get('stopbits') not in self.STOPBITS: raise ValueError("Not a valid stop bit: %s" % str(settings.get('stopbits')))
            if self.xonxoff not in self.FLOWCONTROL: raise ValueError("Not a valid xonxoff value: %s" % str(self.xonxoff))
            if self.rtscts not in self.FLOWCONTROL: raise ValueError("Not a valid rtscts value: %s" % str(self.rtscts))
            if self.portId not in self.PORTS: raise ValueError("Not a valid rtscts value: %s" % self.portId)
            return serial.Serial(self.portId,baudrate=settings.get('baudrate'),
                                 parity=settings.get('parity'),
                                 stopbits=settings.get('stopbits'),
                                 bytesize=settings.get('bytesize'),
                                 writeTimeout = settings.get('writeTimeout'),
                                 timeout = settings.get('bytesize'),
                                 rtscts=self.rtscts,
                                 dsrdtr=False,
                                 xonxoff=self.xonxoff)
        except error,e:
            if (config.DEBUG_MODE):
                print("SerialProcessor:: Unable to set baudrate for port SER%d." %self.portId)
                return None
        except Exception, e:
            if (config.DEBUG_MODE):
                print("Serial Processor: Unexpected Error configuring serial port %s: %s %s" %(self.portId, str(sys.exc_info()[0]), str(sys.exc_info()[1])))
        return None

    def __getFlowControl(self):
        if (self.xonxoff==True and self.rtscts==False):
            return 4 #software bi-directional with filtering (XON/XOFF)
        elif (self.xonxoff==False and self.rtscts==True):
            return 3 #hardware bi-directional flow control
        elif (self.xonxoff==True and self.rtscts==True):
            return 6 #both hardware bi-directional flow control (both RTS/CTS active) and software bi-directional flow control (XON/XOFF) with filtering
        return 0 #no flow control
        
    def __getPollingRetry(self):    
        if(config.SERIAL_POLLING_RETRY <= 0):
            return 1
        if(config.SERIAL_POLLING_RETRY > 2):
            return 3
        return config.SERIAL_POLLING_RETRY + 1

    def publish(self, datalists, address=None, log=1):
        i = 0
        try:
            self.lock.acquire()
            address = address or self.address
            if(datalists and address):
                for datalist in datalists:
                    try:
                        if(log): 
                            data = self.__hexlify(datalist[1])
                        else: data = datalist[1]
                        self.broker._forward_data_string(address, data, datalist[0], log)
                        i = i + 1
                    except:
                        print('Serial:: Unexpected error in publish. %s %s' % (str(sys.exc_info()[0]), str(sys.exc_info()[1])))
        except:
            pass
        finally:
            self.lock.release()
            return i
             
    
    def __hexlify(self,data):
        a = []
        for x in data:
            a.append("%02X" % (ord(x)))
        return ''.join(a)
    
    
            
class Logger:
    
    def __init__(self,handler,uploadInterval=300):
        self.handler = handler
        self.uploadInterval=uploadInterval
        self._nextUploadTime = time.time()
        self.lock = thread.allocate_lock()
    
    def write(self,msg):
        if(msg and msg not in ('\n', '\r\n')):
            try:
                self.lock.acquire()
                self.handler.log(msg)
            finally:
                self.lock.release() 
    
    def cleanUp(self):
        try:
            self.lock.acquire()
            self.handler.close()
        except:
            pass
        finally:
            self.lock.release()
    
    def getRecords(self,number,start=0):
        try:
            self.lock.acquire()
            return self.handler.getRecords(number,start)
        finally:
            self.lock.release()
    
    def deleteRecords(self,number,start=0):
        try:
            self.lock.acquire()
            return self.handler.deleteRecords(number,start)
        finally:
            self.lock.release()
    
    def shouldUpload(self):
        t=time.time()
        if(self._nextUploadTime - t < 0):
            self._nextUploadTime = t + self.uploadInterval
            return 1
        return 0

class SerialHandler:
    def __init__(self):
        SER.set_speed('115200','8N1')
    
    def log(self,msg):
        SER.send(msg + '\r\n')
        
    def close(self):
        pass
    
    def getRecords(self,number,start=0):
        return []
    
    def deleteRecords(self,number,start=0):
        return []
    
class FileHandler:
    
    def __init__(self, filename, maxBytes, timeStamp=1, rotate=1):
        self.maxBytes = maxBytes
        self.timeStamp = timeStamp
        self.baseFilename = filename
        self.rotate=rotate
        self.mode ='ab'
        self.file = None
        
    def log(self,msg):
        try:
            if self.file is None:
                self.__open(self.mode)
            if(self.timeStamp):
                msg= "%s- %s\r\n" %(self.asctime(),msg)
            else:
                msg= "%s\r\n" %(msg)
            if self.__shouldRollover(msg):
                if(self.rotate):
                    self.__doRollover()
                else:
                    self.__doFifoRollover(msg)
            if(self.file):
                self.file.write(msg)
                self.file.flush()
        except IOError:
            if(self.file):
                self.close()
                self.file = None
        except:
            pass
    
    def getRecords(self,number,start=0):
        try:
            try:
                lines = []
                if(self.file):
                    self.close()
                self.file=self.__open('rb')
                lines = self.file.readlines()
                self.close()
                lines =lines[start:(start+number)]
                return lines
            except:
                lines=[]
        finally:
            self.close()
            return lines
    
    def deleteRecords(self,number,start=0):
        try:
            try:
                success=-1
                if(self.file):
                    self.close()
                self.file=self.__open('rb')
                lines = self.file.readlines()
                self.close()
                lines =lines[0:start] + lines[(start+number):]
                self.file= self.__open('wb')
                self.file.writelines(lines)
                self.file.flush()
                self.close()
                self.file = None
                success=1
            except:
                pass
        finally:
            self.close()
            return success
    
    def close(self):
        try:
            if(self.file):
                self.file.close()
            self.file=None
        except:
            pass
        
    def __shouldRollover(self, msg):
        if(self.file):
            if (self.__file_size() + len(msg) >= self.maxBytes):
                return 1 
        return 0

    def __doRollover(self):
        if(self.file):
            self.close()
            self.file= self.__open('wb')
            
    def __doFifoRollover(self,msg):
        try:
            if(self.file):
                fileSize = self.__file_size()
                lenMsg = len(msg)
                self.close()
                self.file=self.__open('rb')
                lines = self.file.readlines()
                while(fileSize + lenMsg >= self.maxBytes):
                    fileSize=fileSize - len(lines[0])
                    lines.pop(0)
                lines.append(msg)
                self.close()
                self.file= self.__open('wb')
                self.file.writelines(lines)
                self.file.flush()
                self.close()
                self.file = None
        except:
            self.close()
            
    def __open(self, mode):
        self.file = open(self.baseFilename, mode)
        return self.file
    
    def __file_size(self):
        self.file.seek(0, 2)
        return self.file.tell()
  
import RPi.GPIO as GPIO  

class Gpio:
    def __init__(self, instamsg=None,broker = None):
        self.instamsg = instamsg
        self.broker =broker
        self.address=config.ClientId
        self.__configure_gpio_ports()

    def _handleMsg(self,message):
        if(message):
            if (config.DEBUG_MODE): print "Gpio Message received %s" % message.toString()
            msg = message.body()
            msgList= msg.split('/')
            GPIO.output(int(msgList[0]),(int(msgList[1])))
            
    def __getDirection(self,port,direction):
        if(direction=='DI'):
            return GPIO.IN
        elif (direction=='DO'):
            return GPIO.OUT
        else: raise ValueError, "Unrecognized GPIO direction %s for pin %d." % (direction, port)
              
              
    def __configure_gpio_ports(self):
        try:
            for port in config.GPIO_PORTS:
                pinNumber = port.get('pin_number')
                direction = self.__getDirection(port.get('pin_number'),port.get('direction'))
                GPIO.setmode(config.GPIO_MODE)
                GPIO.setup(pinNumber,direction)
        except Exception ,e :
            print str(e)
            print"Gpio:: Unexpected error setting GPIO ports pin number: %d and direction %s." % (pinNumber,direction)
    
    def process(self):
        self.broker._publishLogData()
        data_list = list()
        data = 'GPIO'
        if self.address:
            try:
                    for ports in config.GPIO_PORTS:
                        pinNumber = ports.get('pin_number')
                        portNumber = str(pinNumber)
                        direction = ports.get('direction')
                        if (len(portNumber) == 1):
                            portNumber = '0' + portNumber
                        if direction == 'DO':
                            data = data + ',DO' + portNumber + str(GPIO.input(pinNumber))
                        elif direction == 'DI': 
                            data = data + ',DI' + portNumber + str(GPIO.input(pinNumber))
                        else:                     
                            raise ValueError, "Unrecognized GPIO mode [%d] for pin [%d]." % (direction, pinNumber)
                    data_list.append(data)
                    data = self.process_data(self.address, data, data_list)
            except Exception, e:
                if (config.DEBUG_MODE):
                    print ("GPIO Processor: Unexpected error: %s" % str(e))
#                     gateway.LOGGER.error("GPIO Processor: Unexpected error: %s" % str(e))
    def process_data(self, address, data, sample_data_list):
        if (sample_data_list and len(sample_data_list) is not 0):
            forward_data = self.forward_data(address, sample_data_list)
            data = data + forward_data
        return data 
    
    def forward_data(self, address, data_list):
        for data in data_list:
            self.broker._forward_data_string(address, data, None,1)
        
        return ''
    
    def forward_data_string(self, address, data, offset):
        if (data):
            data = self.format_data(address, data, offset)
            try:
                data = '<?xml version="1.0"?><datas>' + data + '</datas>'
                #print 'TCPForwarder;forwarding data ' + data
                data = self.header_size(data) + data
                self.broker._publishDataString(self, data,log=1)
                if (config.DEBUG_MODE):
                    print("GPIO: Data sent: %s" % data)
            except Exception, e:
                if (config.DEBUG_MODE):
                    print("GPIO forward_data_string error")
                raise Exception(str(e))
     
    def header_size(self, data):
        length = str(len(data))
        header_size = length.zfill(8)
        return header_size
           
    def input(self,pinNumber):
        # input from GPIO7
        return GPIO.input(pinNumber)
     
    def output(self,pinNumber,msg): 
        # output to GPIO8
        GPIO.output(pinNumber, msg)

class Broker :
    
    def __init__(self, instamsg=None):
        self.instamsg = instamsg
        self.lock = thread.allocate_lock()
        self.dataLogger = self.__setDataLogger()
    
    def _publishDataString(self, data,log=1):
        try:
            self.instamsg.publish(config.PubTopic, data, 2, 0, self.__publishhandler)
            if (config.DEBUG_MODE):
                print("Broker: TCP data sent: %s" %data)
        except Exception, e:
            if(log and self.dataLogger):
                self.dataLogger.write(data) 
                if (config.DEBUG_MODE):
                    print("Broker: TCP publisher data send failed. Logged it.")
            raise Exception(str(e))
        
    def __publishhandler(self,result):
        try:
            if (config.DEBUG_MODE): 
                if(result.failed()):
                    print('Serial:: Unable to publish to client due to  [%s] '%str(result.cause()))
                else: print('Serial::data publish to client   [%s] '%str(config.ClientId))
        except Exception, e:
            if (config.DEBUG_MODE): print('Serial:: Unexpected error in processing publishhandler %s' %str(e))
            
    def __setDataLogger(self):
        if(config.ENABLE_DATA_LOGGING):
            if (config.DEBUG_MODE):
                print('Raspberrypi:: Setting up data logger...')
            mb=config.MAX_DATA_LOG_SIZE
            if(mb > 256000 and mb < 1024):
                mb=1024 
            fh = FileHandler('data.log', maxBytes=mb,timeStamp=0, rotate=0)
            return Logger(fh,int(config.DATA_LOG_UPLOAD_INTERVAL))

    def _forward_data_string(self, address, data, time=None, log=1):
        try:
            if(log):
                if(not time):
                    time = self.getTimeAndOffset()
                data = '<?xml version="1.0"?><datas>' + "<data_node><manufacturer>" + config.MANUFACTURER + "</manufacturer><data>" + data + "</data>" + \
                "<id>" + address + "</id><time>" + time[0] + "</time><offset>" + time[1] + "</offset></data_node>" + '</datas>'
            if(log or log is None):
                data = '%08d' % (len(data)) + data
            self._publishDataString(data,log)
        except Exception, e:
            if (config.DEBUG_MODE):
                print("Serial: Error in formating data string..")
                
    def getTimeAndOffset(self):
        try:
            return (time.strftime("%Y%m%d") + "x" + time.strftime("%H%M%S%z")).split('+')
        except Exception, e:
            raise error('Time:: Unable to parse time.')
        
    def _setDebugLogger(self):
        try:
            if(config.LOG_TO =='FILE'):
                mb=config.MAX_LOG_SIZE
                if(mb > 256000 and mb < 1024):
                    mb=1024  
                handler = FileHandler('system.log', maxBytes=mb)   
                debugLogger=sys.stdout = sys.stderr = Logger(handler)
            elif(config.LOG_TO =='SER'):
                handler = SerialHandler()   
                debugLogger = sys.stdout = sys.stderr = Logger(handler)
            return debugLogger
        except:
            if (config.DEBUG_MODE):
                error = 'Raspberrypi:: : Unable to set debug logger. Continuing without it...'
                if(config.LOG_TO =='SER'):
                    print(error) 
                else:self.__bootLogger(error)
            
    def _bootLogger(self,msg):
#This works while the modules are being loaded
        try:
            f = open('error.log', 'ab')
            f.write(msg + '\r\n')
        finally:
            f.close()
    
    def _publishLogData(self):
        try:
            self.lock.acquire()
            if(InstamsgConnected):
                if(self.dataLogger and self.dataLogger.shouldUpload()):
                    if (config.DEBUG_MODE):
                        print("Sending log data to instamsg")
                    self.__processDataLogs()
        except:
            if (config.DEBUG_MODE):
                print("Unknown Error in process: %s %s" % (str(sys.exc_info()[0]), str(sys.exc_info()[1])))
        finally:
            self.lock.release()
            
    def __processDataLogs(self):
        try:
            if(self.dataLogger):
                datalist = self.dataLogger.getRecords(10)
                i = 0
                if(datalist):
                    for data in datalist:
                        if ((data.find('<?xml version="1.0"?>') > 0)):
                            if (config.DEBUG_MODE):
                                print("Broker: Processing log data %s" %str(data))
                            self.instamsg.publish(config.PubTopic, data, 2, 0, self.__publishhandler)
#                             if(not self.publish([[None, data.strip()]], None, 0)):
#                                 break
                        i = i + 1
                else:
                    if (config.DEBUG_MODE):
                        print("Broker: No data logs to process..." )            
                if(i > 0):
                    if (config.DEBUG_MODE):
                        print(" Broker: %d data logs sent to server..." % i)
                    resp = self.dataLogger.deleteRecords(i) 
                    if (config.DEBUG_MODE):
                        if(resp == 1):
                            print("Broker: Deleted %d data logs sent to server." % i)
                        else:
                            print("Broker: Error deleting %d data logs sent to server." % i)
        except:
            if (config.DEBUG_MODE):
                print(':: Unexpected error in processing data logs. %s %s' % (str(sys.exc_info()[0]), str(sys.exc_info()[1])))
            
                               
if  __name__ == "__main__":
    rc = start(sys.argv)
    sys.exit(rc)
    
