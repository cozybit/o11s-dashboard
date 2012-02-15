 #! /bin/bash
. test_config 
for i in `seq 1 $((LAST_NODE-1))` 
do
	# checkin
	[ $i != 4 -a $i != 7 ] && curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC[i]}&peer=${MAC[i-1]}&peer=${MAC[i+1]}"
	[ $i == 4 ] && curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC[i]}&peer=${MAC[i-1]}&peer=${MAC[i+1]}&peer=${MAC[7]}"
	[ $i == 7 ] && curl -f -s $URL/checkin -d "netid=${NETID}&macaddr=${MAC[i]}&peer=${MAC[i-1]}&peer=${MAC[i+1]}&peer=${MAC[4]}"
done
echo PASS
