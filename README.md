### Install

```bash
git clone ...
docker image build -t ros_noetic .
sudo apt install ffmpeg # or brew install ffmpeg
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements
```

### Run

```bash
docker run -it --net=host ros_noetic
```

### Set the IP Adress of the HSR

```bash
export ROS_IP=192.168.x.x
export ROS_MASTER_URI=http://example:11311
```

### Test connection

```bash
rostopic list
```

#### Server

Start server
```bash
python server.py
```
Test server

```bash
python test_server.py
```