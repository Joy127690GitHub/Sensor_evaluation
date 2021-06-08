# Data Visualization GUI for Ultrasonic Sensor Modules / 超声波传感器模组的数据可视化呈现

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

**Reference: Hardware requirements/硬件需求参考**

RS232: Digtus DA-70156驱动安装：  
https://www.digitus.info/en/products/computer-and-office-accessories/computer-accessories/usb-components-and-accessories/interface-adapter/da-70156/

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

## 3. 未完成计划更新中
 - 可视化参数输入：尚未完成
 - 自动化程序测试：尚未完成

## 4. 版本更新说明：
 - 20210608： 
   - Readme.md，文件创建
   - environment_m50.yml，文件创建，尚未测试



