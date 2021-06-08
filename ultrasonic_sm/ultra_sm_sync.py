# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 21:13:53 2020

@author: xtzhu
"""
import time
from bitstring import BitArray

from checksum import Checksum

from ultra_sm import Ultra_sm_std

class Ultra_sm_sync(Ultra_sm_std):
    '''
    for Ultrasonic sensor with synchron sensor-array mode
    '''
    def __init__(self, sensing_range = 4000, node_addr = 0x07):
        super().__init__(sensing_range,node_addr)

        self.sm_mode = 'Synchron Sensor-Array'
        
        self.op_codes_sync = {0xFB: 'profile_Send/Receive mode', # 1 send, n receive
                              0xFA: 'profile_Synchron Send mode', # common sync, n send/receive together
                              
                              
                              0x23: 'BurstCount_A', #parameters for User Profile A
                              0x22: 'Gain_A', #parameters for User Profile A
                              0x21: 'Current_A',#parameters for User Profile A
                              
                              0x0D: 'Address_Prog_Tolerance',
                              0x0C: 'Address_Prog_distance'}
    
    def msg_tx_pack(self, addr = 0X01, r_w='r',op_code=0xFA,data_bytes=[0x2F],cksum_byte=None):
        #print('co_code = ', op_code)
        self.op_codes.update(self.op_codes_sync)
        return super().msg_tx_pack(addr, r_w,op_code,data_bytes,cksum_byte)
    
    def msg_rx_unpack_profile(self, msg_rxd_cmd, msg_rxd_data):
 
        '''
        Unpack the message received, and verifiy the checksum byte.
        Extract the valid data like measured distance data_rxd, and self.amplitude
        
        OP object ID:
            0xFB: 'profile_Send/Receive mode', # 1 send, n receive
            0xFA: 'profile_Synchron Send mode', # common sync, n send/receive together
            0x37: 'profile_User Profile A',
        
        Parameters
        ----------
        msg_rxd : response message recieved (rxd abbr. received data), string type, mandatory
            DESCRIPTION. The default is '', nothing received.

        Returns
        -------
        data_rxd:
            DESCRIPTION.
        
        self.error_code:            

        '''
        self.profiles = [0xFB, 0xFA, 0x37]

        cmd_unpacked = self.msg_rx_unpack_cmd(msg_rxd_cmd) #return [node_addr_rxd, msg_rxd_cmd[0:8], op_code_rxd, self.error_code] 
        
        data_unpacked = self.msg_rx_unpack_data(msg_rxd_data) #return [self.node_addr, msg_rxd_data[0:n], msg_rxd_data_str, self.error_code]
            
        
        if cmd_unpacked[3] == 0xFF:            
            if data_unpacked[3] == 0xFF:                
                if int(cmd_unpacked[2],16) in self.profiles:
                    if self.sensing_range == 4000:
                        self.distance = int(data_unpacked[2][0:2],16)*1.6*10 #in mm, 测量范围4000mm时，换算系数. Bline zone：250mm
                    elif self.sensing_range == 2500:
                        self.distance = int(data_unpacked[2][0:2],16)*10 #in mm, 测量范围2500mm时
                    else:
                        print('msg_rx_unpack_profile: Measuring range definition is not known')
                    
                    self.amplitude = int(data_unpacked[2][2:4],16) #0~255 in decimal
                
                else:
                    print('msg_rx_unpack_profile2: Wrong op_code used. no distance data_rxd got')
                
                self.error_code = data_unpacked[3]
            else:
                print('Error: sync msg_rx_unpack_profile: data_unpacked[3]',data_unpacked[3])
                pass
        else:
            print('Error: sync msg_rx_unpack_profile: cmd_unpacked[3]',cmd_unpacked[3])
            pass
        
        
        if self.error_code == 0xFF: #check error ok, if 0xFF, error free
            if int(data_unpacked[2][0:2],16) not in self.event_echo.keys():
                print('Sensor', self.node_addr, 'measured distance:', round(self.distance,0), 'mm,', 'amplitude:', round(self.amplitude,0), 'dB SPL')
                pass
            else:
                print('Sensor', self.node_addr, ':', self.event_echo[int(data_unpacked[2][0:2],16)])
                pass
        else:
            print('Error code 0x', self.error_code,':', self.error_codes[self.error_code],
                  'in data received of sensor', self.node_addr,':', str(data_unpacked[1]).upper())
            
        
        return [self.node_addr, self.distance, self.amplitude, self.error_code]
        
             
        
if __name__ == '__main__':

    ucc4000_sync = Ultra_sm_sync(sensing_range=2500)
    ucc4000_sync.node_addr=0x07
    
    msg_req = ucc4000_sync.msg_tx_pack(addr=0x01,r_w='r',op_code=0xFA,data_bytes=[0x2F])
    print('request message:', msg_req, type(msg_req))

    
    msg_rxd_sync='AFFCFE400F0ED40F0ED4'
    print(msg_rxd_sync)
    test = ucc4000_sync.msg_rx_unpack_profile(msg_rxd_sync) 
    '''
    print('return: data_rxd =', test, 'mm')
    if test in ucc4000_sync.self.error_codes.keys():
        print('return: self.error_code:', str(hex(test)).upper(), ucc4000.self.error_codes[test[1]])
    else:
        print('return: self.error_code:', str(hex(test)).upper(), "unknown error reported from sensor")
    '''