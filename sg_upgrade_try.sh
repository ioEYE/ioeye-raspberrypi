#!/bin/sh

. ./upgrade_params

if [ -z "${FIRST_PID}" ]
then
    echo "Safe to proceed (stage 1) ..."

    if [ -z "${SECOND_PID}" ]
    then
	    echo "Safe to proceed (stage 2) ..."

    	cd "${HOME_DIRECTORY}"
    	chmod 777 ./sg_upgrade.sh
    	./sg_upgrade.sh &
    else
        echo "An instance of sg_setup.sh already running, bye bye"
    fi
else
    echo "An instance of sg_upgrade.sh already running, bye bye"
fi
