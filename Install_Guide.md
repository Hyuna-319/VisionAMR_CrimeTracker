# Install Guide



<br>



📌 User
------
**1. Install packages** 

```
git clone https://github.com/Hyuna-319/visionAMR_crime_tracker.git
```

**2. Set up workspace**
```
cd ~/Downloads/CrimeTracker_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```
**3. Execution**
```
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$HOME/map.yaml
ros2 launch yolo_integration yolo_launch.py
```

<br>

📌 AMR
------

**1. Install packages** 

```
ssh -X user@.192.168.10.xx
```
```
pip install ultralytics opencv-python requests numpy pyautogui
sudo apt install ros-humble-turtlebot3 ros-humble-turtlebot3-navigation2 
```
```
scp ~/Downloads/turtlebot_ws.zip user@192.168.10.xx:/home/user
cd /home/user
unzip turtlebot_ws.zip
 ```

**2. Set up workspace**
```
cd turtlebot_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```


**3. Execution**
```
source install/setup.bash
ros2 run turtlebot3_move turtleview
ros2 run turtlebot3_move rviz_capture
```
  



