 #! /bin/bash

. test_config 

# create this network (OK if it already exists)
curl -s $URL/addnetwork -d "netid=${NETID}"

# create this node (OK if it already exists)
curl -s $URL/addnode -d "netid=${NETID}&macaddr=${MAC}&lat=${LAT}&lng=${LNG}"

# checkin
curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC}"
[ $? == 0 ] || { echo FAIL; exit -1; }

echo PASS
