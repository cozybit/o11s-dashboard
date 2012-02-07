 #! /bin/bash

. test_config 

for i in `seq 0 ${LAST_NODE}` 
do
	# create this node (OK if it already exists)
	curl -s $URL/addnode -d "netid=${NETID}&macaddr=${MAC[i]}&lat=${LAT[i]}&lng=${LNG[i]}"
	# checkin
	curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC[i]}"
	[ $? == 0 ] || { echo FAIL; exit -1; }
done
echo PASS
