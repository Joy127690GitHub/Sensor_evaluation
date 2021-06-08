# -*- coding: utf-8 -*-
"""
Created on Fri May  1 22:11:35 2020

@author: xtzhu
"""

from bitstring import BitArray

class Checksum():
    def __init__(self):
        self.value_start = 0x52 #For the xor calculation of Ultrasonic , a start value of 0x52 is used.
        self.value_end = 0x80                 

    def xor(self, packet,direction='request'):
        '''
        XOR checksum caculation
        packet: data type in string 
        '''
        
        xor = self.value_start
        
        packet_b=bytes.fromhex(packet)       
        for i in range(len(packet_b)) :
            xor ^= packet_b[i] #XOR caculation
        
        if direction == 'response':
            xor ^= self.value_end
                
        return xor
    
    def xor_zip(self, packet,direction='request',ACK=True):
        '''
        to zip the 8 bit binary code into 6 bit, as a new xor
        for the write instruction of P+F Ultrasonic sensor module
        '''
        
        xor_8bit = self.xor(packet, direction)

        b8_str = BitArray(uint=xor_8bit, length=8)
        b6_str=  BitArray(uint=0, length=8)   

        #the index of bitarray is not the same as the traditional order of binary 
        # bitarray index : 0,1,2,3,4,5,6,7
        # traditioanl bin: 7,6,5,4,3,2,1,0    
        if direction == "request":
            b6_str[0]= False
        elif direction == 'response':
            b6_str[0]= ACK # ACK/NACK response
        else:
            print('xor_zip: error parameter used')
            
        b6_str[1]= True    #mandatory as manual,fixed to value “1”
        
        b6_str[2]= b8_str[0]^b8_str[2]^b8_str[4]^b8_str[6]
        b6_str[3]= b8_str[1]^b8_str[3]^b8_str[5]^b8_str[7]
        b6_str[4]= b8_str[0]^b8_str[1]
        b6_str[5]= b8_str[2]^b8_str[3] 
        b6_str[6]= b8_str[4]^b8_str[5]
        b6_str[7]= b8_str[6]^b8_str[7]    
        
        xor_6bit = int(b6_str.bin,2)  
        
        return xor_6bit

#################
#Test code below

if __name__ == '__main__':   
    

    packet_request = 'a9fa2f'
    packet_resp = '3f'
    
    cksum = Checksum()
    '''
    xor_test_r =cksum.xor(packet_request, 'request')
    print('\nxor in request HEX: 0x'+'{0:02x}'.format(xor_test_r).upper(),
          '\nxor in request BIN:', bin(xor_test_r))
    '''
    zip_test_r = cksum.xor_zip(packet_request,'request')
    print('\nxor_zip request in HEX: 0x'+'{0:02x}'.format(zip_test_r).upper(),
          '\nxor_zip request in BIN:', bin(zip_test_r))
    
    '''
    xor_test =cksum.xor(packet_resp, 'response') 
    print('\nxor in response HEX: 0x'+'{0:02x}'.format(xor_test).upper(),
          '\nxor in response BIN:', bin(xor_test))
    '''
    zip_test = cksum.xor_zip(packet_resp,'response',ACK=True)
    print('\nxor_zip in response HEX: 0x'+'{0:02x}'.format(zip_test).upper(),
          '\nxor_zip in response BIN:', bin(zip_test))
    print('\nif you find the checksum is not right, please change the ACK parameter here, and try again')
    