# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 21:13:53 2020

@author: xtzhu
"""
import time
from bitstring import BitArray
from checksum import Checksum

class Ultra_sm_std():
    '''
    Object for Pepperl-Fuchs ultrasonic sensor module M50 and M30
    Standard profile
    '''
    
    def __init__(self, sensing_range = 4000, node_addr = 0x07):
        self.sensing_range = sensing_range #in mm         
        self.node_addr = node_addr #0x07 default msg_rxd_data_str if it is a new sensor valid msg_rxd_data_str is 1~7
        self.sm_mode = 'Standard'
        
        if self.sensing_range == 4000:
            self.blind_zone = 250 # in mm
        elif self.sensing_range == 2500:
            self.blind_zone = 150 # in mm
        
        self.distance = 0 #in mm
        self.amplitude = 0 # in unit 100% 
        self.error_code = 0xFF #error free

        #self.data_record= pd.DataFrame(columns=('Timestamp','Timestamp_struct','Measured distance','Amplitude'))

        #Operation code is the parameter index for the parameter access.
        self.op_codes = {0xFF: 'temperature',
                         0xFE: 'profile_A',
                         0xFD: 'profile_B',
                         0xFC: 'profile_C',    #default
                         0x37: 'profile_User Profile A',
                         
                         0x36: 'factory_reset',    #no checksum for msg_rxd
                         0x35: 'sensor_address',
                         0x34: 'HW_FW_version',
                         0x33: 'get_serial no.',
                         0x32: 'get_sensor_doc no.',
                         0x0A: 'PWM output/temperature compensation',
                         0x00: 'get_sensor_address/CRC_CALC', #no checkbum bytes for msg_request/response
                         
                         0x31: 'Profile Production', # manufacturer parameter
                         0x30: 'Read Calibration',# manufacturer parameter
                         0x26: 'Set Temp Offset', # manufacturer parameter
                         0x25: 'Set Serial Nr.', # manufacturer parameter
                         0x24: 'Clr_Calib_Data', # manufacturer parameter
                         0x0B: 'Set_BMM_Time-WindowSize'} # manufacturer parameter    
        
        self.event_echo = {0x00: "No echo, no object detected.",
                           0x01: "Target object too close, in blind zone.",
                           0xFF: "Target object too far, Out of measuring range."}
        
        self.error_codes = {0x00: 'Package received not complete', #自定义错误代码，标识接口程序接收到报文不完整错误
                            
                            0x01: 'Checksum error',
                            0x02: 'Telegram timeout',
                            0x03: 'Telegram below threshold',
                            0x04: 'Telegram above threshold',
                            0x05: 'Parameter error',
                            0x06: 'Session error',
                            0x07: 'Transmission error',
                            0x08: 'EEPR0M error',
                            0x09: 'OP code error',
                            0x0A: 'OP object is read-only',
                            0x0B: 'Temperature error',
                            0x0C: 'Tranducer error in active',
                            0x0D: 'Generic error',                            
                            0xFF: 'Response OK, No error'}
   
    def comm_cfg(self):
        '''       
        commumnication parameters for UART, and LIN communication
        
        Returns
        -------
        None.

        '''
        com_setting = {'baudrate':    19200,
                       'bytesize':    8,
                       'parity':      'N',
                       "stopbits":    1}
                
    def resp_time(self, op_code, num_cycles):
        '''
        self.num_cycles = 0xFF-0xFE # for test first, number of measuring cycles, 0x00~0xFE, no 0xFF.
        self.op_code = 0xFC # for test first
        self.response_time = self.resp_time(self.op_code, self.num_cycles) #in ms, from UCC4000-50GK datasheet
        '''
        Offset_time = 5 #in ms
        
        if op_code == 0xFE: #Measuring profile A, short range detection
            if self.sensing_range == 4000: #in mm 
                cycle_time = 35 #in ms
            elif self.sensing_range == 2500:
                cycle_time = 20
            else:
                print('error in resp_time caculation: sensing range')
        elif op_code == 0xFD or 0xFC : #Measuring profile B/C, middle/far range detection
            if self.sensing_range == 4000: #in mm 
                cycle_time = 75 #in ms
            elif self.sensing_range == 2500:
                cycle_time = 50
            else:
                print('error in resp_time caculation: sensing range')
        elif op_code == 0x31: #Measuring profile for final test, manufacturer parameter
            cycle_time = 60
        else:
            print('error in resp_time caculation: op_code wrong')
            cycle_time = 100 #just assuming, no information in manual
        
        safety_factor = 1.0 #
        self.response_time = (num_cycles*cycle_time + Offset_time)*safety_factor      

    
    def msg_tx_pack(self, addr = 0X07, r_w='r',op_code=0xFC,data_bytes=[0xFE],cksum_byte=None):
        '''
        request message packaging
        
        Organize the data packet based on data input.
        
        node_addr:  node address, factory default 0x7
        r_w:        'r', default, the selection of reading/writing parameter
        self.op_codes:
        data_bytes:
        checksum:   0x00, shows no checksum parameter input    
        ''' 
        #print('ultra_sm co_code = ', op_code)
        param_error = {0x01: 'parameter error: selection of parameter reading or writing, r or w?',
                       0x02: 'parameter error: wrong operation code selected.',
                       0x03: '',
                       0xFF: 'no error'}
        
        if op_code in [0xFE,0xFD, 0xFC]:
            self.resp_time(op_code, 0xFF-data_bytes[0])
        else:
            self.response_time = 60 #??
        
        msg_req = []
        msg_req_str = ''
        cksum_req = Checksum()
                
        if r_w =='r':        
            sync_byte = 0xA8 + addr
        elif r_w == 'w':
            sync_byte = 0xA0 + addr
        else:
            print(param_error[0x01])
            return param_error[0x01]
        #print('msg_tx_pack:sync_byte:', sync_byte)
        msg_req.append(sync_byte)
        
        if op_code in self.op_codes.keys():
            msg_req.append(op_code)
        else:
            print(param_error[0x02])
            return param_error[0x02]
        
        for i in range(len(data_bytes)):
            msg_req.append(data_bytes[i])    
        
        #xor_checksum caculation      
        if (op_code != 0x00) & (data_bytes[0] != 0x00):
            if cksum_byte == None:
                for j in range(len(msg_req)):
                    msg_req_str += str(hex(msg_req[j])[2:])  #[2:] is used to remove 0x from hex string 
                msg_req.append(cksum_req.xor_zip(msg_req_str,'request'))
            else:
                msg_req.append(cksum_byte)
        else: #CRC_CALC does not have the checksum byte
            pass     
        msg_req_str += str(hex(msg_req[-1])[2:]) # add checksum byte in the string.      
        #print('msg_tx_pack: msg_req_str:', msg_req_str)
        msg_req_bytestype = bytes.fromhex(msg_req_str) # format to COM package

        return msg_req_bytestype    
    
    def msg_rx_unpack_cmd(self, msg_rxd_cmd=''): #measuring profile
        
        '''
        Unpack the cmd part of message received, and verifiy the checksum byte.
        
        OP object ID below, with no checksum byte, are not is not considered in this function.
            0x00: CRC_CALC 

        '''
        
        cksum_rxd = Checksum()
        op_code_rxd = '' # in string type
        node_addr_rxd = 0x0 # if no address got from the message.
        #print('msg_rxd_cmd:',msg_rxd_cmd)
        if len(msg_rxd_cmd) == 4*2: #6 bytes. 前4个字节是原命令返回，第5个字节是data，最后一个是校验和
            #request指令，报文校验
            msg_rxd_req_str =msg_rxd_cmd[0:6]
            cksum_byte_req = cksum_rxd.xor_zip(msg_rxd_req_str,'request')
            if cksum_byte_req == int(msg_rxd_cmd[6:8],16):
                #print('checksum_request:',hex(checksum_request), 'no error')
                node_addr_rxd = int(msg_rxd_cmd[0:2],16) & 0x7                
                op_code_rxd = msg_rxd_req_str[2:4]
                #print('msg_rx_unpack_cmd: no error')
                self.error_code = 0xFF
                return [node_addr_rxd, msg_rxd_cmd[0:8], op_code_rxd, self.error_code] 
            else:                
                self.error_code = 0x01
                print('Error code 0x',self.error_code,':',self.error_codes[self.error_code], 
                      'in cmd received:', msg_rxd_cmd[0:8], '>> should be', hex(cksum_byte_req))
                return [node_addr_rxd, msg_rxd_cmd[0:8], cksum_byte_req, self.error_code] 
        else:
            print('len(msg_rxd_cmd): not right, in node', node_addr_rxd)
            return [node_addr_rxd, msg_rxd_cmd[0:8], op_code_rxd, self.error_code]

    def msg_rx_unpack_data(self, msg_rxd_data=''): #measuring profile
        
        '''
        Unpack the data part of message received, and verifiy the checksum byte.
        Extract the valid data, with n bytes 
        
        OP object ID below, with no checksum byte, are not is not considered in this function.
            0x00: CRC_CALC 

        Parameters
        ----------

        msg_rxd_data : data part of response message recieved, string type, mandatory
            DESCRIPTION. The default is '', nothing received.

        Returns
        -------

        msg_rxd_data_str:
            DESCRIPTION.
        
        self.error_code:            

        '''
        
        msg_rxd_data_str = ''        
        cksum_rxd = Checksum()
        n = len(msg_rxd_data)  
        #print('length of msg_rxd_data:', n)
        #print('msg_rxd_data:',msg_rxd_data)

        #response响应，报文校验 #m-1个字节是data，最后1个字节是校验和
        msg_rxd_data_str=msg_rxd_data[0:n-2] # data, remove 1 byte checksum, in string type
        
        cksum_rxd_response=int(msg_rxd_data[n-2:n],16) #checksum byte responsed 
        b6_str = BitArray(uint=cksum_rxd_response, length=8)
        ACK = b6_str[0]
        #print('msg_rxd_data_str:',msg_rxd_data_str)
        #print('msg_rxd_data:ACK', ACK)
        cksum_byte_calc = cksum_rxd.xor_zip(msg_rxd_data_str,'response', ACK)
        
        if cksum_rxd_response == cksum_byte_calc :             
            if ACK: #ACK (error-free transmission/measurement)
                self.error_code = 0xFF #No error, Response OK
            else: #NACK (error during transmission/measurement)
                print ("! response error reported by the sensor")
                self.error_code = int(msg_rxd_data_str,16)
                if self.error_code in self.error_codes.keys():
                    print(': error code 0x',msg_rxd_data_str,', ',self.error_codes[self.error_code])
                else:
                    print(': error code 0x',msg_rxd_data_str,', unknown error reported from sensor')
            
            return [self.node_addr, msg_rxd_data[0:n], msg_rxd_data_str, self.error_code] 
        
        else:
            self.error_code = 0x01
            print('Error code 0x',self.error_code,':',self.error_codes[self.error_code],
                  'in data received:', msg_rxd_data[0:n], '>> should be', hex(cksum_byte_calc))
            
            return [self.node_addr, msg_rxd_data[0:n], cksum_byte_calc, self.error_code] 

        

    
        
    
    def msg_rx_unpack_profile(self, msg_rxd_cmd, msg_rxd_data):
 
        '''
        Unpack the message received, and verifiy the checksum byte.
        Extract the valid data like measured distance
        
        OP object ID:
            FC: Measuring profile C, wide sound beam, default
            FD: Measuring profile B, medium sound beam
            FE: Measuring profile A, narrow sound beam
        
        Parameters
        ----------
        msg_rxd : response message recieved (rxd abbr. received data), string type, mandatory
            DESCRIPTION. The default is '', nothing received.

        Returns
        -------
        msg_rxd_data_str:
            DESCRIPTION.
        
        self.error_code:   
        '''       
        self.profiles = [0xFC, 0xFD, 0xFE]
        
        #print('ultra_sm unpack cmd')
        cmd_unpacked = self.msg_rx_unpack_cmd(msg_rxd_cmd) 
        #return [node_addr_rxd, msg_rxd_cmd[0:8], op_code_rxd, self.error_code] 
        
        #print('ultra_sm data unpack')
        data_unpacked = self.msg_rx_unpack_data(msg_rxd_data) 
        #return [self.node_addr, msg_rxd_data[0:n], msg_rxd_data_str, self.error_code]
           
        #print('ultra_sm profile uppack start')
        if cmd_unpacked[3] == 0xFF:
            
            if data_unpacked[3] == 0xFF:
                
                if int(cmd_unpacked[2],16) in self.profiles:
                                       
                    if self.sensing_range == 4000:
                        self.distance = int(data_unpacked[2][0:2],16)*1.6*10 #in mm, 测量范围4000mm时，换算系数. Bline zone：250mm
                        
                    elif self.sensing_range == 2500:
                        self.distance = int(data_unpacked[2][0:2],16)*10 #in mm, 测量范围2500mm时
                    else:
                        print('msg_rx_unpack_profile: Measuring range definition is not known')
                        
                else:
                    print('msg_rx_unpack_profile2: Wrong op_code used. no distance data_rxd got')
                
                self.error_code = data_unpacked[3]
        
        if self.error_code == 0xFF: #check error ok, if 0xFF, error free
            if int(data_unpacked[2][0:2],16) not in self.event_echo.keys():
                print('Sensor', self.node_addr, ': Measured distance value:', round(self.distance,0), 'mm')
                
            else:
                print('Sensor', self.node_addr, ':', self.event_echo[int(data_unpacked[2][0:2],16)])
                pass
        else:
            print('Error code 0x',self.error_code,':',self.error_codes[self.error_code],
                  'in data received of sensor', self.node_addr, ':',str(data_unpacked[1]).upper())
            
        
        return [self.node_addr, self.distance, self.amplitude, self.error_code]
    
   
    def msg_rx_unpack_addr(self, msg_rxd=''): #Sensor address
        msg_rxd_addr = msg_rxd
        data_addr_str = self.msg_rx_unpack(msg_rxd_addr)
        if data_profile[0] == 0x35:
            self.node_addr = int(data_profile[1],16)
        else:
            print('msg_rx_unpack_profile: Wrong op_code used. no address number got')
            self.node_addr = 0xFF # valid msg_rxd_data_str is 1~7
        
        return 
    
    def msg_req_auto(self):
        '''
        based on operation code selected, and node number read, to pack the message.
        '''
        pass



if __name__ == '__main__':
    ucc4000 = Ultra_sm_std(sensing_range=4000)
    ucc4000.node_addr=0x6
    ucc2500 = Ultra_sm_std(sensing_range=2500)
    ucc2500.node_addr=0x5    
    
    msg_req = ucc4000.msg_tx_pack(r_w='r',op_code=0xFC,data_bytes=[0xFE])
    print('request message:', msg_req, '\nmsg_req:', type(msg_req))
 
    msg_rxd='AFFCFE400FC5'
    print(msg_rxd)
    test = ucc4000.msg_rx_unpack_profile(msg_rxd)
    
    '''
    print('return: msg_rxd_data_str =', test[0], 'mm')
    if test[1] in ucc4000.self.error_codes.keys():
        print('return: self.error_code:', str(hex(test[1])).upper(), ucc4000.self.error_codes[test[1]])
    else:
        print('return: self.error_code:', str(hex(test[1])).upper(), "unknown error reported from sensor")
    '''
  