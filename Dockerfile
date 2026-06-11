FROM ros:noetic-robot

# Update system
RUN apt-get update && apt-get upgrade -y

### UTILITIES ###

# Install tmux for multiple terminal sessions (optional)
RUN apt-get install -y tmux
# Ping command for network testing (optional)
RUN apt-get install -y iputils-ping
# Discover other devices on the network using nmap (optional)
RUN apt-get install -y nmap