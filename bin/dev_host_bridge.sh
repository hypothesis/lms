#!/bin/sh

# Write the network of the host to the /etc/hosts file if "host.docker.internal"
# is not supported on the system.
# From: https://dev.to/bufferings/access-host-from-a-docker-container-4099

# Check if we are on a supported system
HOST_DOMAIN="host.docker.internal"
ping -q -c1 $HOST_DOMAIN > /dev/null 2>&1

# If not, then write find our IP and map "host.docker.internal" to it
if [ $? -ne 0 ]; then
  HOST_IP=$(ip route | awk 'NR==1 {print $3}')
  echo -e "$HOST_IP\t$HOST_DOMAIN" >> /etc/hosts
fi