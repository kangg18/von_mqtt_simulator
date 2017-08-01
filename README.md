# von_mqtt_simulator
MQTT Simulator JastecmOBD



1.Prerequeiste 

    1) Python Install - 
        (https://www.continuum.io/downloads)

    2) Anaconda prompt

    3) requirement install 
       wget  https://bootstrap.pypa.io/get-pip.py
       python get-pip.py
       pip install -r requirments.txt 
         
    4) invokation
       python von_mqtt_simulator.py


2.Activate Device Connection


<img src="https://github.com/kangg18/von_mqtt_simulator/blob/master/device%20connection_1.png?raw=true">


https://github.com/tremoteye/device-starter-kit



3.Simulator program execution process

<img src="https://github.com/kangg18/von_mqtt_simulator/blob/master/simulator_screen_3.png?raw=true">


    1)  Run Anaconda Prompt
    2)  Change directory to the installed simulator program directory
    3)  Run python von_mqtt_simulator.py 
    4)  Set Server Address from MQTT Broker Info TAB (1)
    5)  Click Connect right below UserPWD (2)
    6)  Select Scenario by clicking Select Scenario and open drive_sec sample file (4)
    7)  Set Simulation interval from Simulation Control tab [Interval(5), FastForwarding(6)] 
    8)  Click View GPS track (7)
    9)  Click View Dynamics graph (8)
    10) Click VIEW MQTT Event (3)
    11) START Scenario (9)
    12) End Scenario (10)
