 #! /bin/bash
. test_config 

for i in `seq 1 $((LAST_NODE-1))` 
do
	# checkin
	curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC[i]}&peer=${MAC[i-1]}&peer=${MAC[i+1]}"
	[ $? == 0 ] || { echo FAIL; exit -1; }
done
echo PASS
