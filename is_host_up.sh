#!/bin/bash

is_host_up() {
    ping=$(ping -q -c 2 $1 2>/dev/null)
    result=$?

    ipaddr=$(host $1 | awk -F"has address" '{print $2}'|sed -e '/^$/d' -e 's/^\ //' | perl -pe 's/\n/\ /'| sed -e 's/\ $//')

    if test $result -eq 0; then
        echo "Host $1 ($ipaddr): responding to ping"
        exit 0
    fi

    if test $result -eq 1; then
        echo "Host $1 ($ipaddr): not responding to ping"
        exit 0
    fi

    echo "Host $1 ($ipaddr): error with ping"
    exit 1
}

is_host_up $1
