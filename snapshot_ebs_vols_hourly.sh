#!/bin/bash

date=`date +'%Y-%m-%d-%H:%M'`
attached_vols=`${EC2_HOME}/bin/ec2-describe-volumes | grep ATTACHMENT | sed -e 's/\t/,/'g` # Need to convert from Tab separeated to comma for loop

for entry in `echo $attached_vols` ; do
    volume=`echo $entry | awk -F"," '{print $2}'`
    #echo $volume
    instance_id=`echo $entry | awk -F"," '{print $3}'`
    instance_ec2_ip=$(dig +short $(${EC2_HOME}/bin/ec2-describe-instances $instance_id | grep INSTANCE | awk '{print $4}'))
    instance_resolved_ip=$(host $1.ec2.newsweek.com | grep "has address" | awk '{print $4}')

    if  [ "$instance_ec2_ip" == "$instance_resolved_ip" ]
        then
            volume_size=$(${EC2_HOME}/bin/ec2-describe-volumes $volume | grep VOLUME | awk '{print $3}')
            #echo $volume_size
            if  [ "$volume_size" == "$2" ]
                then
                    #echo "Instance $1 with instance_id $instance_id with instance_ecp_ip $instance_ec2_ip and instance_resolved_ip $instance_resolved_ip has volume $volume attached"
                    ${EC2_HOME}/bin/ec2-create-snapshot  -d $1-hourly-snap-$date $volume
            fi
    fi
done
