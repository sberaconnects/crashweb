#!/bin/bash
# Set up cron environment, then start cron + gunicorn.

set -e

# Write cron job with current env vars
mkdir -p /etc/cron.d
cat > /etc/cron.d/sdk-auto-install <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
@reboot     root /usr/local/bin/auto-install-sdk.sh >> /var/www/sdks/.auto-install.log 2>&1
0 0 * * *   root /usr/local/bin/auto-install-sdk.sh >> /var/www/sdks/.auto-install.log 2>&1
EOF
chmod 0644 /etc/cron.d/sdk-auto-install

mkdir -p /var/www/sdks

service cron start

exec gunicorn --bind 0.0.0.0:8080 --workers 2 app:app
