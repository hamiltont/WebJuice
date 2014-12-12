# Utilize a "fat container" because databases depend on a lot
# of system processes, like syslog, runsv, cron, and others
#
# Modifications:
#   - Add our SSH keys so server can log in
#   - Run SSHd on port 2442 in case of --net=host
#
FROM phusion/baseimage

# Add our own public key
ADD id_rsa.pub /tmp/id_rsa.pub
RUN cat /tmp/id_rsa.pub >> /root/.ssh/authorized_keys && \
    rm -f /tmp/your_key.pub

# Make SSHD use an odd port in case of --net=host
RUN sed -i 's/#Port 22/Port 2442/g' /etc/ssh/sshd_config
EXPOSE 2442