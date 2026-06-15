### Install

```bash
git clone https://github.com/paulperet/hsr-vla-inference
docker image build -t ros_noetic .
sudo apt install ffmpeg # or brew install ffmpeg
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Server

On your computer or another machine with a GPU:

Start server
```bash
python server.py
```

Test server
```bash
python test_server.py
```

---

On a new terminal:

### Start container

```bash
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
rosrun hsr_controller hsr_controller.py
```