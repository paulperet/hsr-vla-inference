# Run your VLA on the Human Service Robot

## Features

- Decoupled server and control node, to load your policy on any machine
- Switch between tasks without restarting the server
- Change the horizon of action execution
- Sim/real implementations

## Install Instructions

### Server

On your computer or another machine with a GPU:

Start server
```bash
git clone https://github.com/paulperet/hsr-vla-inference
cd hsr-vla-inference
sudo apt install ffmpeg # or brew install ffmpeg
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export REPO_ID=paulprt/pi05-hsr-80k-aug
python server.py
```

Test server
```bash
python test_server.py
```

---

On a new terminal (And preferably on a ubuntu machine):

### Start container

```bash
git clone https://github.com/paulperet/hsr-vla-inference
cd hsr-vla-inference
docker image build -t ros_noetic .
docker run -it --net=host ros_noetic
```

### Inside the container, set the IP Adress of the computer and of the HSR

```bash
export ROS_IP=computer_ip
export ROS_MASTER_URI=http://robot_ip:11311
```

### Test connection

Verify topics are listed
```bash
rostopic list
```

### Run package
```bash
export SERVER_URL=http://example:8000/predict
export PROMPT="Grab the cup"
export MAX_TIME=600
export CHUNK_SIZE=50
rosrun hsr_controller hsr_controller.py
```

## Running on simulation (Gazebo)

From https://github.com/hsr-project/tmc_wrs_docker :
```bash
git clone --recursive https://github.com/hsr-project/tmc_wrs_docker.git
cd tmc_wrs_docker
./pull-images.sh
docker-compose up
```

Now clone my repository from inside the workspace container:
```bash
docker exec -it tmc_wrs_docker-workspace-1 /bin/bash
git clone https://github.com/paulperet/hsr-vla-inference
cd hsr-vla-inference
sudo /bin/bash ./simulation_setup.sh
source /home/developer/catkin_ws/devel/setup.bash
```

Run the node
```bash
export SERVER_URL=http://example:8000/predict
export PROMPT="Grab the cup"
export MAX_TIME=600
export CHUNK_SIZE=50
rosrun hsr_controller hsr_controller.py
```

Simulator UI: http://localhost:3000

# Troubleshooting

On the real robot, command are being sent but robot is not moving:

- Run docker on a ubuntu machine

In simulation, workspace-1 doesn't start on macos:

- Enable Settings -> General -> "Choose file sharing implementation for your containers" -> gRPC FUSE
