import instamsg
import sys
import time
import serial
import config
import exceptions
import thread

SER =None
def start(args):
    instaMsg = None
    try:
        try:
            options={'logLevel':instamsg.INSTAMSG_LOG_LEVEL_DEBUG, 'enableSsl':1}
            instaMsg = instamsg.InstaMsg(config.ClientId, config.AuthKey, __onConnect, __onDisConnect, __oneToOneMessageHandler, options)
            while 1:
                instaMsg.process()
                SER.process()
                time.sleep(10)
        except:
            print("Unknown Error in start: %s %s" %(str(sys.exc_info()[0]),str(sys.exc_info()[1])))
    finally:
        if(instaMsg):
            instaMsg.close()
            instaMsg = None
    
def __onConnect(instaMsg):
    global SER
    if (config.DEBUG_MODE): print "Client connected to Instamsg"
    SER =Serial(instaMsg)
    
def __onDisConnect():
    print "Client disconnected."
    
      
def __messageHandler(mqttMessage):
        if(mqttMessage):
           if(config.DEBUG_MODE):print "Received message %s" %str(mqttMessage.toString())
        
def __oneToOneMessageHandler(msg):
    if(msg):
        print "One to One Message received %s" % msg.toString()
        msgBytes = __unhexelify(msg.body())
        Serial.write(msgBytes)
        time.sleep(1)
        read_val = Serial.read(1000)
        if (config.DEBUG_MODE): print "Read data:%s" %str(read_val)
#         msg.reply(__hexlify(read_val))
        
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
    
    def __init__(self, instamsg=None):
        settings = config.serial_port
        self.portId=str(settings.get('port'))
        self.timeout = int(settings.get('timeout'))*10
        if(self.timeout>10 or self.timeout < 0): self.timeout=10
        self.xonxoff=int(settings.get('xonxoff'))
        self.rtscts=int(settings.get('rtscts'))
        self.commandlist = settings.get('command_list')
        self.pollingRetry = self.__getPollingRetry()
        self.instamsg =instamsg
        instamsg.subscribe(self.portId,1, self.processCmd, self.subscribehandler)
        self.flowControl = self.__getFlowControl()
        self.port = self.__configurePort(settings)
        self.lock = thread.allocate_lock()
        self.address ='abc'

    def process(self):
        dataList = []
        try:
            if self.port:
                if (self.commandlist):
                    for cmd in self.commandlist:
                        try:
                            data = self.pollPort(cmd[1], self.pollingRetry)
                            if(data):
                                if (config.DEBUG_MODE):
                                    print("Serial Processor: Read serial data: %s" % data)
                                dataList.append([self.getTimeAndOffset(),str(cmd[0]) + str(data)])
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
           
    def publishhandler(self,result):
        try:
            if (config.DEBUG_MODE): 
                if(result.failed()):
                    print('Serial:: Unable to publish to client due to  [%s] '%str(result.cause()))
                else: print('Serial::data publish to client   [%s] '%str(config.ClientId))
        except:
            if (config.DEBUG_MODE): print('Serial:: data publish to client [%s] '%str(config.ClientId))
            
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
                        self.__publishDataString(address, data, datalist[0], log)
                        i = i + 1
                    except:
                        print('%s Serial:: Unexpected error in publish. %s %s' % (self.name, str(sys.exc_info()[0]), str(sys.exc_info()[1])))
        except:
            self.sockInit = 0
            pass
        finally:
            self.lock.release()
            return i
        
    def __publishDataString(self, address, data, time=None, log=1):
        if(log):
            if(not time):
                time = self.getTimeAndOffset()
            data = '<?xml version="1.0"?><datas>' + "<data_node><manufacturer>" + config.MANUFACTURER + "</manufacturer><data>" + data + "</data>" + \
            "<id>" + address + "</id><time>" + time[0] + "</time><offset>" + time[1] + "</offset></data_node>" + '</datas>'
        if(log or log is None):
            data = '%08d' % (len(data)) + data
        try:
            self.instamsg.publish('9533d950-c88b-11e4-bf22-bc764e102b63', data, 2, 0, self.publishhandler)
            if (config.DEBUG_MODE):
                print("%s Serial: TCP data sent: %s" % (self.name, data))
        except Exception, e:
            if(log and self.dataLogger):
                self.dataLogger.write(data) 
                if (config.DEBUG_MODE):
                    print("%s Serial: TCP publisher data send failed. Logged it." % self.name)
            raise Exception(str(e))
            
        
    def getTimeAndOffset(self):
        try:
            return (time.strftime("%Y%m%d") + "x" + time.strftime("%H%M%S%z")).split('+')
        except Exception, e:
            raise error('Time:: Unable to parse time.')
        
    
    def __hexlify(self,data):
        a = []
        for x in data:
            a.append("%02X" % (ord(x)))
        return ''.join(a)
if  __name__ == "__main__":
    rc = start(sys.argv)
    sys.exit(rc)
    