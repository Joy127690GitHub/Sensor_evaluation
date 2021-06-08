# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 21:55:23 2020

参考：https://blog.csdn.net/colcloud/article/details/42454839
 - 原程序二次执行的时候，存在问题:原因Input() IO被进程强行关闭，造成的IO资源无法释放。

@author: xtzhu
"""

import serial, threading, time
import serial.tools.list_ports
import pandas as pd

from datetime import datetime

from ultra_sm import Ultra_sm_std as sm
from ultra_sm_sync import Ultra_sm_sync as sm_sync

class Comm_serial():
    '''
    '''
    def __init__(self, port='', com_setting={}):
        #初始化串口
        try:
            self.my_serial = serial.Serial() #创建串口对象, 
            port_list_device = self.list_com()
            if port in port_list_device:
                self.my_serial.port = port
            else:
                self.my_serial.port = port_list_device[0]
                print('Warning: COM port assigned not found，connecting to USB2COM found:', port_list_device[0])
            self.my_serial.apply_settings(com_setting) #timeout in second
        except Exception as e:
            print('Error: COM port assigned cannot be connected')
       

        self.btn_connect = True
        self.btn_send = True
        self.btn_record = True
        
        self.sts_connected = False  
        
        self.cyclic = 100 #in ms，轮询周期，如果为0，表示只发送一次。
        
    
    def list_com(self):

        port_list = list(serial.tools.list_ports.grep('USB')) #only list the USB2COM devices.
        port_list_device = []
        
        if len(port_list) == 0:
            print('Error: no USB2COM adapter connected.')
        else:
            for i in range(len(port_list)): 
                port_list_device.append(port_list[i].device)
                #print(port_list_device)
                #print(port_list[i].device, ' - ', port_list[i].description, '\n') 
            if len(port_list) > 1 :
                print('Warning: too much USB2COM adapter connected.')
        
        return port_list_device
        
 
class SerialRW_SM(Comm_serial): 
    # Read/write ultrasonic sensor module via Serial communication
    
    def __init__(self, port='', com_setting={}, list_sm=[]):
        super().__init__(port, com_setting)
        self.list_sm = list_sm
        #图表参数控制：    
        self.time_window = 10 #in minutes，图表刷新和寄存器溢出管理
        
        table_data = pd.DataFrame(columns=('Timestamp','Node_address','Distance','Amplitude'))
        table_event = pd.DataFrame(columns=('Timestamp','Node_address','Error_code','Error_discription'))
        self.records_data = []
        self.records_event = []        
        for r in range(len(self.list_sm)):
            self.records_data.append(table_data)
            self.records_event.append(table_event)
        
    def start(self):
        #开串口及建立读写线程
        self.my_serial.open()
                
        if self.my_serial.isOpen():
            self.sts_connected = True
            
            #多线程创建和线程守护, 创建线程,不同线程对应不同事件
            self.event_poll_ctrl = threading.Event() #False default, 先发后收顺序控制
                        
            self.thread_send = threading.Thread(target=self.sender, name='Thread_send')
            self.thread_send.setDaemon(True)
            
            self.thread_read = threading.Thread(target=self.reader, name='Thread_read')
            self.thread_read.setDaemon(True)
            
            # 如果在start()之前设置t1.setDaemon(True)则不阻塞主线程，后台运行
            self.thread_send.start()   
            self.thread_read.start()

            return True
        else:
            return False

    def sender(self):
        if self.sts_connected:
            while self.btn_send:                
                try:
                    if self.list_sm[0].sm_mode == 'Standard':
                        #print("here 1")
                        #snddata = self.list_sm[0].msg_tx_pack(addr = self.list_sm[0].node_addr)
                        snddata = self.list_sm[0].msg_tx_pack(addr = self.list_sm[0].node_addr, op_code=0xFE,data_bytes=[0xFE])
                        #snddata = self.list_sm[0].msg_tx_pack(addr = self.list_sm[0].node_addr, op_code=0xFD,data_bytes=[0xFE])
                        #snddata = self.list_sm[0].msg_tx_pack(addr = self.list_sm[0].node_addr, op_code=0xFC,data_bytes=[0xFE])
                        
                    elif self.list_sm[0].sm_mode == 'Synchron Sensor-Array':               

                        snddata = self.list_sm[0].msg_tx_pack(addr=0x01, r_w='r',op_code=0xFA,data_bytes=[0x2F]) #Synchron send mode
                        #snddata = self.list_sm[0].msg_tx_pack(addr=0x02, r_w='r',op_code=0xFB,data_bytes=[0x3F]) #send receive mode
                        #snddata = self.list_sm[0].msg_tx_pack(addr=0x02, r_w='r',op_code=0x37,data_bytes=[0x3F]) #user-profile A

                    result=self.my_serial.write(snddata)

                    if result:
                        #print('Command sent')
                        self.event_poll_ctrl.set() #设定为True,表示数据已发送
                        
                        if self.cyclic <self.list_sm[0].response_time:
                            print("Warning: Parameter improper: 轮询命令周期设置过短，已调整为参数对应最短时间")
                            self.cyclic = self.list_sm[0].response_time  #控制命令发送周期，不得小于cyclic设定值
                        time.sleep(self.cyclic/1000) #控制命令发送周期，不得小于cyclic设定值  
                    else:
                        print('Preparing the sending of command data')
                        self.event_poll_ctrl.wait() #False 堵塞                   
                    
                except Exception as ex:

                    print ('sender exception:', ex)
        else:
            self.btn_send = False
            print("Error: COM interface is not connected, the command cannot be sent.")
        
        return    
    
    def reader(self):  
        
        if self.list_sm[0].sm_mode == 'Standard':
            self.len_bytes_msg = 6  #in bytes  
        elif self.list_sm[0].sm_mode == 'Synchron Sensor-Array':
            self.len_bytes_msg = 4+3*len(self.list_sm)
        
        count_tried = 0
        
        while self.sts_connected:
            self.msg_rxd_buf='' #存储当前报文数据
            self.time_buf= 0 #存储当前报文数据抵达时间
            try:
                if self.event_poll_ctrl.is_set():      #判断是否设置了标志位，是否为True   
                    if self.my_serial.in_waiting: # the iswaiting must be used, orelse, the program will suspend there for ever.
                        
                        self.time_buf = round(time.time(),3)
                        self.msg_rxd_buf = self.my_serial.read(self.len_bytes_msg).hex() #most OP-CODE will have the response packets in 6 bytes.
                        self.record_fmt(self.time_buf, self.msg_rxd_buf)                        
                                                
                        if len(self.msg_rxd_buf):
                            #print('reader here 3')   
                            self.event_poll_ctrl.clear() #串口缓存区数据已读取
                    else:
                        count_tried += 1
                        if count_tried > 20:
                            print('waiting for response data from sensor') 
                            count_tried = 0
                        else:
                            time.sleep(self.cyclic/1000)
                            pass
                else:                    
                    self.event_poll_ctrl.wait()  #False 堵塞                    
            
            except Exception as ex:
                print('reader exception:',ex) 
        
        return
 

    
    def record_fmt(self,time_buf, msg_rxd_buf):
        
        msg_rxd_cmd = self.msg_rxd_buf[0:8]
        msg_rxd_data = self.msg_rxd_buf[8:2*self.len_bytes_msg]
        cmd_unpacked = self.list_sm[0].msg_rx_unpack_cmd(msg_rxd_cmd) #return [node_addr_rxd, msg_rxd_cmd[0:8], op_code_rxd, self.error_code]
        
        if cmd_unpacked[3] == 0xFF: # error free
                   
            for i in range(len(self.list_sm)): #??? problem location 

                if self.list_sm[i].sm_mode == 'Standard':                   
                    #print('record_fmt here')
                    record_buf = self.list_sm[i].msg_rx_unpack_profile(msg_rxd_cmd, msg_rxd_data[0:4]) #数据解析为mm距离值返回
                    #record_buf: [self.node_addr, self.distance, self.amplitude, self.error_code]
                    #print('record_fmt here2')
                elif self.list_sm[i].sm_mode == 'Synchron Sensor-Array':
                    
                    record_buf = self.list_sm[i].msg_rx_unpack_profile(msg_rxd_cmd, msg_rxd_data[0+6*i:6+6*i])
                
                #print('record_fmt here3')             
                if record_buf[3] == 0xFF: #check error ok, if 0xFF, error free
                    
                    record_buf_fmted = pd.Series({'Timestamp':self.time_buf,
                                                  'Node_address':record_buf[0], #Pandas自动推断数据类型出错，将整型意外转换为浮点型。恢复方法尚未找到
                                                  'Distance':record_buf[1],
                                                  'Amplitude':record_buf[2]})
                    self.records_data[i] = self.records_data[i].append(record_buf_fmted, ignore_index=True) #store distance value (in mm) to records_data.
                    
                    #print(self.records_data[i].tail(3))
                    
                else:
                    
                    record_buf_fmted= pd.Series({'Timestamp':self.time_buf,
                                                 'Node_address':record_buf[0],
                                                 'Error_code':record_buf[3],
                                                 'Error_discription':self.list_sm[i].error_codes[record_buf[3]]})
                    
                    self.records_event[i] = self.records_event[i].append(record_buf_fmted, ignore_index=True) #store error event for review later
                    
        else:
            print('Abnormal data received:', self.msg_rxd_buf)
            self.my_serial.reset_input_buffer() #当错误发生时，遗留buffer内容，可能造成解析问题                 
            if self.my_serial.in_waiting ==0:
                print('input buffer reseted successufully.')
            else:
                print('input buffer reseted not successufully.')
            pass
        
        if self.btn_record == True: 
            if len(self.records_data[0]) > (self.time_window*60*1000/self.cyclic):
                print('record to file')
                self.record2file()
       
    def record2file(self):        
        #初始化blog文件名称        
        for i in range(len(self.list_sm)):            
            fname = time.strftime("%Y%m%d_%H%M%S")#blog名称为当前时间
            print('r2file')
            rfname_pd = self.my_serial.port+'_read_'+fname+'node_'+str(self.list_sm[i].node_addr)+'.csv' #接收blog名称 
            self.records_data[i].to_csv(rfname_pd,sep='\t',index=True,header=True)
            self.records_data[i].drop(self.records_data[i].index, inplace=True) # 清空数据记录，重新画图
            
            rfname_pd2 = self.my_serial.port+'_event_'+fname+'node_'+str(self.list_sm[i].node_addr)+'.csv' #接收blog名称         
            self.records_event[i].to_csv(rfname_pd2,sep='\t',index=True,header=True)
            self.records_event[i].drop(self.records_event[i].index, inplace=True) # 清空数据记录

    def stop(self, btn_connect):
        print('try to stop and clear')
        self.btn_connected = btn_connect

        if not self.btn_connected:
 
            if self.my_serial.isOpen():
                self.btn_send = False
                self.sts_connected = False
                time.sleep(50/1000) #等待20ms,待线程程序结束，再关闭串口
                self.my_serial.close()
                
                print('successfully stopped')        


if __name__ == '__main__':


    #test = Comm_serial()
    #test.list_com()
    
    #com_port = 'COM6'
    com_port = 'COM7'
    com_cfg_sm = {'baudrate':    19200,
                  'bytesize':    8,
                  'parity':      'N',
                  'stopbits':    1,
                  'timeout':    1}
    
    # sensor module type
    
    ucc2500 = sm(sensing_range=2500,node_addr=0x7)
    ucc4000_2 = sm(sensing_range=4000,node_addr=0x2)    
    ucc4000_3 = sm(sensing_range=4000,node_addr=0x3)
    ucc4000_7 = sm(sensing_range=4000,node_addr=0x7)
    #list_sm = [ucc2500,]
    #list_sm = [ucc4000_2]
    list_sm = [ucc4000_7]
    #list_sm = [ucc4000_2,ucc4000_3]
    
    ucc4000_sync2 = sm_sync(sensing_range=4000,node_addr=0x2)    
    ucc4000_sync3 = sm_sync(sensing_range=4000,node_addr=0x3)
    #list_sm = [ucc4000_sync2,ucc4000_sync3]
    #list_sm = [ucc4000_sync2]
    
    ser = SerialRW_SM(com_port, com_cfg_sm,list_sm)
 
    try:
         
        if ser.start(): 
            
            time.sleep(5) #
            print("main thread wakes up")
            btn_connect = False
            ser.stop(btn_connect)
        else:
            pass            
    except Exception as ex:
        print (ex)
    
  
    
