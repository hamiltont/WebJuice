FROM rastasheep/ubuntu-sshd:14.04

# Basic SSH container plus passwordless-SSH.
# 
# Usage: 
#   - Adds local *.pub files mounted inside /tmp/zz_ssh, 
#     container will add them to authorized_keys
#   - (Optional) Run with --net=host
#   - Use TFB toolset to SSH in and install load software
#   - Use TFB toolset to SSH in and trigger load generation
#
# Changes to base image:
#   - Add .ssh folder and authorized_keys
#   - Modifies config for SSH key login
#   - Adds any *.pub files from /tmp/zz_ssh to authorized_keys
#   - Runs SSH on port 2552 (in case of --net=host)
# 
# Note: User/pass is root/root

# Note: LXC execution driver requires folders to be created 
# inside the container before you can mount into them
RUN mkdir /tmp/zz_ssh

# Setup SSH for passwordless login
RUN echo "AuthorizedKeysFile /root/.ssh/authorized_keys" >> /etc/ssh/sshd_config
RUN mkdir /root/.ssh && \
    touch /root/.ssh/authorized_keys && \
    chown -R root:root /root/.ssh && \
    chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/authorized_keys

# Make SSHD use an odd port
RUN sed -i 's/Port 22/Port 2552/g' /etc/ssh/sshd_config
EXPOSE 2552

ENV HOME /root

# Must copy on run to properly setup keys
CMD for k in `ls /tmp/zz_ssh/*.pub`; do \
      cat $k >> /root/.ssh/authorized_keys; \
    done && \
    /usr/sbin/sshd -D -e