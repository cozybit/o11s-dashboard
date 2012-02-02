#! /bin/bash

URL='http://o11s-dashboard.appspot.com'
NETID='testnetwork'

while getopts "l" opt; do
	case $opt in
		l)
		URL='http://localhost:8080'
		;;
	esac
done

# create this network (OK if it already exists)
curl -s $URL/addnetwork -d "netid=${NETID}"

# create this node (OK if it already exists)
curl -s $URL/addnode -d "netid=${NETID}&macaddr=00:11:22:33:44:55"

# checkin
curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=00:11:22:33:44:55"
[ $? == 0 ] || { echo FAIL; exit -1; }

echo SUCCESS
