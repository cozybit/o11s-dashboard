#! /bin/bash

# Run this script from cron, eg.
# 1. sudo crontab -e
# 2. add a line like
# */5 * * * * /root/o11s-dash/checkin.sh
# 3. confirm that the Last Seen field for your mesh node is updated

DASHBOARD_URL='http://o11s-dashboard.appspot.com'
NETID='605_market'
MACADDR=`ip link show mesh0 | grep 'link/ether' | awk '{ print $2 }'`

wget -O - -d --post-data "netid=${NETID}&macaddr=${MACADDR}" ${DASHBOARD_URL}/checkin
# OR
# curl -f -s ${DASHBOARD_URL}/checkin -d "netid=${NETID}&macaddr=${MACADDR}"
