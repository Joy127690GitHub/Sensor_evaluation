# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 23:19:38 2020

Oscilloscope, referring to Matplotlib sample.

@author: xtzhu
"""
import time

import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import CheckButtons

import pandas as pd

#import PySerialTest.py

class Scope():
    def __init__(self, ax, maxt=30):
        self.ax = ax
        self.maxt = maxt #in second 时间轴长度  
        
        self.data_time = 7*[pd.Series(dtype='int64')]        
        self.node_addr = 7*[pd.Series(dtype='int64')] 
        self.data_dist = 7*[pd.Series(dtype='int64')]  
        self.data_amp = 7*[pd.Series(dtype='int64')] 
        #self.scat=7*[plt.scatter([],[])]
        
        self.start_time = 7*[0]
        self.last_record = 7*[0]

class Scope_line(Scope):
    def __init__(self,fig, ax, ax_limit, blind_zone, maxt=30):
        super().__init__(ax)
        
        self.color_cycle=['b', 'g', 'c', 'm', 'y', 'k', 'w']
        
        self.fig = fig
        self.blind_zone = blind_zone
        
        #ax 参数设置
        #第一轴：主轴ax参数设置：Time_Distance
        self.ax.set_title("Time vs Distance(lines on/off via clicking legend)") 
        self.ax.set_xlim(0, self.maxt) #横坐标阈值设置
        self.ax.set_ylim(-0.02*ax_limit, 1.1*ax_limit)#纵坐标阈值设置, #default for UCC2500 test
        self.ax.set_xlabel('Time (second)')
        self.ax.set_ylabel('Distance (mm)')  
                
        #self.ax.axhline(y=blind_zone,color='r', label='Blind zone')   
                         
        
        #第二轴：副轴ax2参数设置
        self.ax2 = self.ax.twinx()
        self.ax2.set_ylabel('Amplitude (dB SPL)')
        self.ax2.set_ylim(-0.02*255, 1.1*255)#纵坐标阈值设置, 
        
        self.line_index = 0        
        self.count_win_move = 1 #曲线时间窗移动次数
    
    
    
    def update(self, i, *frames_data):
        
        #时间窗内的数据显示的缓冲存储
        try:
            if len(frames_data[i]['Timestamp']) >1: #空的数据帧将带来后续代码的不可预测的索引错误，这里判断过滤
                if self.count_win_move == 1:
                    self.start_time[i] = frames_data[i]['Timestamp'][0]
                
                self.data_time[i] = frames_data[i]['Timestamp'][self.last_record[i]:-1]-self.start_time[i]
                self.node_addr[i] = frames_data[i]['Node_address'][self.last_record[i]:-1]
                self.data_dist[i] = frames_data[i]['Distance'][self.last_record[i]:-1]
                self.data_amp[i] = frames_data[i]['Amplitude'][self.last_record[i]:-1]
                
                if self.data_time[i].iloc[-1] > (self.maxt * self.count_win_move): # reset the arrays
                    #显示窗口移动
                    self.last_record[i] = len(self.data_time[i])-1
                    #print('self.last_record[i]:',self.last_record[i])
                    self.count_win_move +=1
                    #设置坐标轴移动                
                    self.ax.set_xlim(self.maxt*(self.count_win_move-1),
                                     self.maxt*self.count_win_move)
                    self.ax.figure.canvas.draw()
            else:
                pass
           
        except IndexError as ex: #for handling empty frames_data problem
            print('Error: Frames_data '+ str(ex)+'. Size:', frames_data[i].shape )
            time.sleep(1)
                    
        else:            
            if i == self.line_index: #单次执行
                self.ax.add_line(Line2D(self.data_time[i], self.data_dist[i],linestyle='-', 
                                        color=self.color_cycle[i], animated=True,
                                        label='Node.'+str(int(self.node_addr[i][0]))+' Dist.'))
                self.ax2.add_line(Line2D(self.data_time[i],self.data_amp[i],linestyle=':',
                                         color=self.color_cycle[i], animated=True,
                                         label='Node.'+str(int(self.node_addr[i][0]))+' Amp.'))
                  
                self.list_lines = (self.ax.lines+self.ax2.lines)
                
                if i == (len(frames_data)-1):  #等待所有曲线创建完毕，创建legend
                    self.leg = self.fig.legend(fancybox=True, shadow=True, loc='lower center',ncol=len(self.list_lines)) 
                    self.ax.axhline(y=self.blind_zone,xmin=0, xmax=1,color='r', label='Blind zone')#axline需放在legend创建之后，否则会出问题
                    
                    self.fig.canvas.draw()
                    self.init_legend(self.list_lines)                                       
                    self.fig.canvas.mpl_connect('pick_event', self.on_pick)  
                
                self.line_index +=1
            else:                
                self.ax.lines[i].set_data(self.data_time[i], self.data_dist[i])
                self.ax2.lines[i].set_data(self.data_time[i], self.data_amp[i])
                self.list_lines = self.ax.lines + self.ax2.lines
            return self.list_lines
                
    def init_legend(self,lines):
        self.lined = {}  # Will map legend lines to original lines.
        for legline, origline in zip(self.leg.get_lines(), lines):
            legline.set_picker(True)  # Enable picking on the legend line.
            #print('legline.get_picker:', legline.get_picker())
            self.lined[legline] = origline
        
    def on_pick(self,event):        
        # On the pick event, find the original line corresponding to the legend
        # proxy line, and toggle its visibility.
        legline = event.artist        
        origline = self.lined[legline]
        visible = not origline.get_visible()
        origline.set_visible(visible)
        # Change the alpha on the line in the legend so we can see what lines have been toggled.
        legline.set_alpha(1.0 if visible else 0.2)
        self.fig.canvas.draw()
        

class Scope_line2(Scope):
    def __init__(self, ax, ax_limit, rax, maxt=30):
        super().__init__(ax)
        
        self.color_cycle=['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        
        #ax 参数设置
        #第一轴：主轴ax参数设置：Time_Distance
        self.ax.set_title("Time vs Distance") 
        self.ax.set_xlim(0, self.maxt) #横坐标阈值设置
        self.ax.set_ylim(-0.02*ax_limit, 1.1*ax_limit)#纵坐标阈值设置, #default for UCC2500 test
        self.ax.set_xlabel('Time (second)')
        self.ax.set_ylabel('Distance (mm)')    
        
        self.rax = rax          
        
        #第二轴：副轴ax2参数设置
        self.ax2 = self.ax.twinx()
        self.ax2.set_ylabel('Amplitude (dB SPL)')
        self.ax2.set_ylim(-0.02*255, 1.1*255)#纵坐标阈值设置, 
        
        self.line_index = 0
        #曲线时间窗移动次数
        self.count_win_move = 1
    
    
    
    def update(self, i, *frames_data):
        
        #时间窗内的数据显示的缓冲存储
        try:
            if len(frames_data[i]['Timestamp']) >1: #空的数据帧将带来后续代码的不可预测的索引错误，这里判断过滤
                if self.count_win_move == 1:
                    self.start_time[i] = frames_data[i]['Timestamp'][0]
                
                self.data_time[i] = frames_data[i]['Timestamp'][self.last_record[i]:-1]-self.start_time[i]
                self.node_addr[i] = frames_data[i]['Node_address'][self.last_record[i]:-1]
                self.data_dist[i] = frames_data[i]['Distance'][self.last_record[i]:-1]
                self.data_amp[i] = frames_data[i]['Amplitude'][self.last_record[i]:-1]
                
                if self.data_time[i].iloc[-1] > (self.maxt * self.count_win_move): # reset the arrays
                    #显示窗口移动

                    self.last_record[i] = len(self.data_time[i])-1
                    self.count_win_move +=1
                   
                    #设置坐标轴移动                
                    self.ax.set_xlim(self.maxt*(self.count_win_move-1),
                                     self.maxt*self.count_win_move)
                    self.ax.figure.canvas.draw()
            else:
                pass
           
        except IndexError as ex: #for handling empty frames_data problem
            print('Error: Frames_data '+ str(ex)+'. Size:', frames_data[i].shape )
            time.sleep(1)
                    
        else:
 
            if i == self.line_index: #单次执行
                self.ax.add_line(Line2D(self.data_time[i], self.data_dist[i],linestyle='-', 
                                        color=self.color_cycle[i], animated=True,
                                        label='Node.'+str(int(self.node_addr[i][0]))+' Dist.'))
                self.ax2.add_line(Line2D(self.data_time[i],self.data_amp[i],linestyle=':',
                                         color=self.color_cycle[i], animated=True,
                                         label='Node.'+str(int(self.node_addr[i][0]))+' Amp.',visible=False))
                self.list_lines = (self.ax.lines+self.ax2.lines)
                
                if i == (len(frames_data)-1):  #等待所有曲线常见完毕，创建Checkbox                  
                    self.init_checkbox()
                    self.check.on_clicked(self.func_checkbox)
                    self.ax.figure.canvas.draw()
                
                self.line_index +=1
            else:                
                self.ax.lines[i].set_data(self.data_time[i], self.data_dist[i])
                self.ax2.lines[i].set_data(self.data_time[i], self.data_amp[i])
        
            self.list_lines = self.ax.lines + self.ax2.lines
                        
            
        
            return self.list_lines 
                
    def init_checkbox(self):
        
        self.line_labels = [str(line.get_label()) for line in self.list_lines]
        visibility = [line.get_visible() for line in self.list_lines]
        
        self.check = CheckButtons(self.rax, self.line_labels, visibility)  
        
    def func_checkbox(self,label):        
        index = self.line_labels.index(label)        
        self.list_lines[index].set_visible(not self.list_lines[index].get_visible())
        
class Scope_stem(Scope):
    def __init__(self,fig, ax, ax_limit, blind_zone):
        super().__init__(ax)
        
        self.fig = fig
        self.blind_zone = blind_zone
        
        self.ax.set_xlim(-0.02*ax_limit, 1.1*ax_limit) #横坐标阈值设置 #for UCC2500 test
        self.ax.set_ylim(-0.02*255, 1.1*255)#纵坐标阈值设置, #for amplitude 100%
        self.ax.set_xlabel('Distance (mm)')
        self.ax.set_ylabel('Amplitude (dB SPL)')
        self.ax.set_title("Distance vs Amplitude")
        
        self.colorline_cycle=['C0-', 'C1-', 'C2-', 'C4-', 'C5-', 'C6-', 'C7-']  
        self.colormarker_cycle=['C0o', 'C1o', 'C2o', 'C4o', 'C5o', 'C6o', 'C7o'] 
        
        self.basefmt=' '    
                
        self.markerline= 7*[None]
        self.stemlines= 7*[None]
        self.baseline=7*[None]
        self.stem_container = 7*[None]
        self.container_labels = 7*[None]

        
        self.count_sample = 5 #显示采样次数限制，仅显示连续5次的采样值
        self.count_win_move = 1 #曲线时间窗移动次数
        self.line_index = 0 


    def update(self, i, *frames_data):
        #时间窗内的数据显示的缓冲存储
        
        try:
            if len(frames_data[i]['Timestamp']) >=self.count_sample: #空的数据帧将带来后续代码的不可预测的索引错误，这里判断过滤
                if self.count_win_move == 1:
                    self.start_time[i] = frames_data[i]['Timestamp'][0]
               
                self.data_time[i] = frames_data[i]['Timestamp'][-self.count_sample:-1]-self.start_time[i]
                self.node_addr[i] = frames_data[i]['Node_address'][-self.count_sample:-1]
                self.data_dist[i] = frames_data[i]['Distance'][-self.count_sample:-1]
                self.data_amp[i] = frames_data[i]['Amplitude'][-self.count_sample:-1]
                
                self.count_win_move +=1
                self.ax.figure.canvas.draw()
            else:
                pass
           
        except IndexError as ex: #for handling empty frames_data problem
            print('Error: Frames_data '+ str(ex)+'. Size:', frames_data[i].shape )
            time.sleep(1)
        
        else:             
            #self.markerline[i], self.stemlines[i], self.baseline[i]
            self.stem_container[i]= self.ax.stem(self.data_dist[i], self.data_amp[i],
                                                 linefmt=self.colorline_cycle[i],
                                                 markerfmt=self.colormarker_cycle[i],
                                                 basefmt=self.basefmt,
                                                 label='Node.'+str(int(self.node_addr[i].iloc[-1])),#self.node_addr[i] is Pandas series type, iloc should be used, cannot use self.node_addr[i][-1]
                                                 use_line_collection=True)
            self.stem_container[i].markerline.set_markersize(3)
                        
            if i == self.line_index: #单次执行
                self.container_labels[i] = self.stem_container[i].get_label()
                if i == (len(frames_data)-1):  #等待所有曲线创建完毕，创建legend
                    self.leg = self.fig.legend(self.stem_container[0:len(frames_data)], #这里要用切片，否则None type在这里会报UserWarning错误
                                               self.container_labels[0:len(frames_data)],
                                               fancybox=True, shadow=True, loc='lower center',ncol=len(frames_data) )
                    self.ax.axvline(x=self.blind_zone,ymin=0, ymax=1,linestyle=':',color='r', label='Blind zone')#axline需放在legend创建之后，否则会出问题
                    
                    self.fig.canvas.draw()
                    #self.init_legend(self.stem_container[0:len(frames_data)])                                       
                    #self.fig.canvas.mpl_connect('pick_event', self.on_pick)  
                
                self.line_index +=1
            else:  
                pass
          
            #return self.markerline, self.stemlines, self.baseline
            return self.stem_container[i]



if __name__ == "__main__":

    def emitter(p=0.03): #随机数据流生成器
        """Return a random value in [0, 1) with probability p, else 0."""
        t =0,
        while True:
            v = np.random.rand(1)
            t += v
            if v > p:
                yield t, 0., 0.
            else:
                yield t, np.random.rand(1), 50*(np.random.rand(1)+1), #注意勿忘了逗号


    # Fixing random state for reproducibility
    np.random.seed(19680801)
    
    
    fig, ax = plt.subplots()
    scope = Scope(ax)
    frames_data = emitter()
    print(next(frames_data))
    
    # pass a generator in "emitter" to produce data for the update func
    
    ani = animation.FuncAnimation(fig, scope.update, frames_data, interval=10,
                                  blit=True)
    
    plt.show()
