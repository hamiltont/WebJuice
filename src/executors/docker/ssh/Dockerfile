FROM rastasheep/ubuntu-sshd:14.04

# Basic SSH container plus passwordless-SSH. 
# 
# Usage: 
#   - Run with *.pub files mounted inside /tmp/zz_ssh, 
#     container will add them to authorized_keys
#   - (Optional) Run with --net=host
#   - Use TFB toolset to SSH in and install load software
#   - Use TFB toolset to SSH in and trigger load generation
#
# Changes to base image:
#   - Add .ssh folder and authorized_keys
#   - Modifies config for SSH key login
#   - Adds *.pub file from /tmp/ssh to authorized_keys
#   - Runs SSH on port 2332 (in case of --net=host)
# 
# Note: User/pass is root/root

# Setup SSH for passwordless login
RUN echo "AuthorizedKeysFile %h/.ssh/authorized_keys" >> /etc/ssh/sshd_config
RUN mkdir /root/.ssh && \
    touch /root/.ssh/authorized_keys && \
    chown -R root:root /root/.ssh && \
    chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/authorized_keys

# Add public key files to authorized_keys to enable login from remotes
# Add private key file to home directory to enable login to remotes
ADD . /tmp/ssh
RUN for k in `ls /tmp/ssh/*.pub`; do \
      cat $k >> /root/.ssh/authorized_keys; \
    done && \
    cp /tmp/ssh/* ~/.ssh && \
    chmod 600 ~/.ssh/id_rsa

# Avoid hundreds of errors about setlocale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  

EXPOSE 22

ADD bootstrap.sh /bootstrap.sh

CMD /bootstrap.sh