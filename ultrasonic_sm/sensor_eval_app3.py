# -*- coding: utf-8 -*-
"""
Created on Fri May 22 23:11:44 2020

@author: xtzhu
"""

import sys
import time

from PyQt5. QtWidgets import QMainWindow

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter

from comm_serial import SerialRW_SM
from oscilloscope2 import *
#from oscilloscope3 import Record_plot as Rp
from sensor_eval_ui import *
from ultra_sm import Ultra_sm_std as sm
from ultra_sm_sync import Ultra_sm_sync as sm_sync


class My_AppWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):        
        super().__init__()
        self.setupUi(self) #窗口控件布置实现，方法继承自Ui_MainWindow
        
        self.thread_sampling = Thread_sampling()#数据读取和导入线程
        self.thread_sampling.start()
        self.frames_data = self.thread_sampling.data_records()
        
        self.ani1 = None # the global animiation type should be defined, 否则会出现莫名的Funcanimation不执行，不显示
        self.add_fig2tab_1()
        self.ani2 = None
        self.add_fig2tab_2()
        self.ani3 = None
        self.add_fig2tab_3()
        
    def add_fig2tab_1(self):
        #标签1容器绘图：=========        
        layout1 = QtWidgets.QVBoxLayout(self.tab_1)      #标签容器上添加布局对象       
                
        self.fig1 = Figure(figsize=(5, 3)) #创建Matplotlib的图表对象
        tab_canvas = FigureCanvas(self.fig1)#将Matplotlib的图表置于画布上
        self.ax_tab1 = tab_canvas.figure.subplots() #创建子图轴域。这里不能直接用subplots()创建figure, ax, 否则会出现独立Matplotlib的图表窗口
        self.fig1.subplots_adjust(bottom=0.12)                
        
        layout1.addWidget(tab_canvas) #将Matplotlib的画布关联到标签容器的layout中
        self.addToolBar(QtCore.Qt.TopToolBarArea,
                        NavigationToolbar(tab_canvas, self)) #在画布上添加图表的操作菜单
      
        #在轴域中添加动态示波器曲线
        scope_line=Scope_line(fig=self.fig1, ax=self.ax_tab1, 
                              ax_limit = self.thread_sampling.ax_limit(),
                              blind_zone = self.thread_sampling.ax_blind_zone())
        try:
            self.ani1 = animation.FuncAnimation(self.fig1, scope_line.update,
                                          frames=len(self.frames_data),#init_func=scope_line.init,
                                          fargs=self.frames_data,
                                          interval=100, blit=True)
            
        except Exception as ex:
            print('error: Funcanimation:', ex)    
        '''               
        Writer = animation.writers['ffmpeg']
        writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
        ani.save('Test.mp4', writer='ffmpeg')                                

        '''
    
    def add_fig2tab_2(self):
        
        #标签2容器绘图：==============
        layout2 = QtWidgets.QVBoxLayout(self.tab_2)      #标签容器上添加布局对象       
                
        self.fig2 = Figure(figsize=(5, 3)) #创建Matplotlib的图表对象
        tab_canvas2 = FigureCanvas(self.fig2)#将Matplotlib的图表置于画布上
        self.ax_tab2 = tab_canvas2.figure.subplots() #创建子图轴域。这里不能直接用subplots()创建figure, ax, 否则会出现独立Matplotlib的图表窗口
        self.fig2.subplots_adjust(left=0.22)
        self.ax_ckbox2 = tab_canvas2.figure.add_axes([0.0, 0.48-0.08*len(self.frames_data)/2, #rect = [left, bottom, width, height]
                                                     0.13, 0.08*len(self.frames_data)])
        
        layout2.addWidget(tab_canvas2) #将Matplotlib的画布关联到标签容器的layout中
        self.addToolBar(QtCore.Qt.TopToolBarArea,
                        NavigationToolbar(tab_canvas2, self)) #在画布上添加图表的操作菜单
      
        #在轴域中添加动态示波器曲线
        
        scope_line2=Scope_line2(self.ax_tab2, ax_limit = self.thread_sampling.ax_limit(),rax=self.ax_ckbox2)    
        self.ani2 = animation.FuncAnimation(self.fig2, scope_line2.update, 
                                      frames=len(self.frames_data),
                                      fargs=self.frames_data,interval=100, blit=True)
        
    
    def add_fig2tab_3(self):
        #标签3容器绘图：==============
        #柱状图
        layout3 = QtWidgets.QVBoxLayout(self.tab_3)      #标签容器上添加布局对象       
                
        self.fig3 = Figure(figsize=(5, 3)) #创建Matplotlib的图表对象
        tab_canvas3 = FigureCanvas(self.fig3)#将Matplotlib的图表置于画布上
        self.ax_tab3 = tab_canvas3.figure.subplots() #创建子图轴域。这里不能直接用subplots()创建figure, ax, 否则会出现独立Matplotlib的图表窗口
        self.fig3.subplots_adjust(bottom=0.12)                
        
        layout3.addWidget(tab_canvas3) #将Matplotlib的画布关联到标签容器的layout中
        self.addToolBar(QtCore.Qt.TopToolBarArea,
                        NavigationToolbar(tab_canvas3, self)) #在画布上添加图表的操作菜单
      
        #在轴域中添加动态示波器曲线
        scope_stem=Scope_stem(fig=self.fig3, ax=self.ax_tab3, 
                              ax_limit = self.thread_sampling.ax_limit(),
                              blind_zone = self.thread_sampling.ax_blind_zone())
        
        self.ani3 = animation.FuncAnimation(self.fig3, scope_stem.update,
                                      frames=len(self.frames_data),#init_func=scope_line.init,
                                      fargs=self.frames_data,
                                      interval=100, blit=True)
               

class Thread_sampling(QtCore.QThread):
    def __init__(self):
        super().__init__()
        self.ser_comm() 
        self.ax_sensingRange = 2500 #in mm, default
                            
    def ser_comm(self): 
        com_port = 'COM7'
        #com_port = 'COM9'
        com_cfg_sm = {'baudrate':    19200,
                      'bytesize':    8,
                      'parity':      'N',
                      "stopbits":    1}
        
        # sensor module type
        ucc2500_7 = sm(sensing_range=2500,node_addr=0x7)        
        ucc4000_2 = sm(sensing_range=4000,node_addr=0x2)    
        ucc4000_3 = sm(sensing_range=4000,node_addr=0x3)
        ucc4000_7 = sm(sensing_range=4000,node_addr=0x7)
        #self.list_sm = [ucc2500]
        #self.list_sm = [ucc4000_7,]
        
        self.list_sm = [ucc4000_7]
        #self.list_sm = [ucc4000_2,ucc4000_3]
        print(len(self.list_sm))
        
        # Sensor module type with sync function
        ucc4000_sync2 = sm_sync(sensing_range=4000,node_addr=0x2)    
        ucc4000_sync3 = sm_sync(sensing_range=4000,node_addr=0x3)   
        ucc2500_sync7 = sm_sync(sensing_range=2500,node_addr=0x7)
        #self.list_sm = [ucc4000_sync2,ucc4000_sync3]
        #self.list_sm = [ucc4000_sync3]
        #self.list_sm = [ucc2500_sync7]
        #self.list_sm = [ucc2500]
        
        self.ser_sm = SerialRW_SM(com_port, com_cfg_sm,self.list_sm)
        
        try:
             
            if self.ser_sm.start():                
                '''
                print("main thread wakes up")
                btn_connect = True
                ser.stop(btn_connect)
                '''
            else:
                pass            
        except Exception as ex:            
            print (ex)
    
    def data_records(self):        
       
        return self.ser_sm.records_data
    
    def ax_limit(self):
        
        for i in range(len(self.list_sm)):
            if self.list_sm[i].sensing_range > self.ax_sensingRange:
                self.ax_sensingRange = self.list_sm[i].sensing_range
                
        return self.ax_sensingRange
    
    def ax_blind_zone(self):
        return self.list_sm[0].blind_zone
    

if __name__ == "__main__": 
    
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).    
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = My_AppWindow()
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec_()

