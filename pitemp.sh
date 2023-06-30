while true
do
	pitemp=$(vcgencmd measure_temp| cut -d \= -f2 | cut -d \' -f1)
	mosquitto_pub -h 192.168.1.193 -t pitemp -m $pitemp -d

	sleep 300 
done

