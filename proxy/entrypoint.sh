#!/bin/bash
# Generate nginx resolver config from /etc/resolv.conf
set -e

# Extract nameserver from resolv.conf and generate resolver directive
NAMESERVER=$(awk '/^nameserver/{print $2;exit}' /etc/resolv.conf)
if [ -n "$NAMESERVER" ]; then
    echo "resolver $NAMESERVER valid=10s ipv6=off;" > /etc/nginx/resolver.conf
else
    # Fallback to common Podman DNS
    echo "resolver 10.89.0.1 valid=10s ipv6=off;" > /etc/nginx/resolver.conf
fi

exec nginx -g 'daemon off;'
