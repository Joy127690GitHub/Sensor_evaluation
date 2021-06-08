# 超声波传感器模组的数据可视化呈现  
Data Visualization GUI for Ultrasonic Sensor Modules  


## 1. Installation / 安装说明
**IDE platform recommended/集成化开发环境推荐**  

Anaconda：支持最新Windows/Linux/Mac操作系统，下载链接:  
 - 官网：https://www.anaconda.com/products/individual-b  
 - 清华大学开源软件镜像站（中国用户推荐）： https://mirror.tuna.tsinghua.edu.cn/help/anaconda/  

**Install the missing dependencies/安装程序包依赖:**  

 - Anaconda开发环境的自动部署:  
 
    ```  
    conda env create -f environment_m50.yml  
    conda activate env_m50  
    ````
    
 - 其他IDE的手动包依赖安装：  
 
   请记事本打开environment_m50.yml，查看程序调试所必须的第三方程序包依赖，按需求进行安装。



## 2 程序调用结构

该传感器评估程序的设计，基于MVC（Model-View-Controller, 模型-视图-控制器）模式，大致程序的调用结构如下：
```
|- sensor_eval_app3.py        #主程序入口（Controller）
   | - sensor_eval_ui.py      #界面视图（View）
       | - sensor_eval_ui.ui  #界面视图，PyQt可视化绘制的文件
       | - oscilloscope2.py   #可视化数据呈现程序
   | - comm_serial.py         #串行通信，数据读取、清洗（Model)
       | - ultra_sm           #超声波模组类，标准型号
           | - checksum.py    #通信数据自校验
           | - ultra_sm_sync  #超声波模组类，继承，定制型号  
```

## 3 程序包快速使用说明

**硬件连接：**  
PC <=> USB2COM <=> COM2LIN <=> Ultrasonic sensor modules (1~7 nodes connected serially acceptable)

**通信参数配置：**  
程序包尚未完成可视化参数输入。硬件参数配置，需要代码中调整，步骤如下：- 
- sensor_eval_app3.py中:
  - 程序将自动检索USB2COM串口端口号并进行设置。若你期望手动设置，请检索com_port变量，进行更改。
  - 检索self.list_sm变量，是否和你硬件连接的sensor module类别、传感参数、节点地址一致。若不一致，需要更改
  
- comm_serial.py中：
  - 若需要更改超声波模组的声锥等相关指令参数，你可以检索snddata变量，更改内部相关参数。请注意，仅更改和你连接的超声波模组的类别对应的snddata变量

**备注**  
- 控制台传感器状态显示：在传感器对应的类文件msg_rx_unpack_profile方法下，if self.error_code == 0xFF代码段下，取消print语句的注释，将打开传感器的实时测量值在控制台显示。

## 3. 未完成计划更新中
 - 可视化参数输入：尚未完成
 - 自动化程序测试：尚未完成

## 4. 版本更新说明：
 - 20210608： 
   - Readme.md，文件创建，添加“程序包快速使用说明”部分
   - environment_m50.yml，文件创建，尚未测试
   
## A. Reference

**Hardware requirements/硬件需求参考**

RS232: Digtus DA-70156驱动安装：  
https://www.digitus.info/en/products/computer-and-office-accessories/computer-accessories/usb-components-and-accessories/interface-adapter/da-70156/



