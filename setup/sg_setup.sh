#!/bin/sh

. ../upgrade_params
PKG_VERSION="2"

###################### PERFORM ACTIONS NOW ##################################

/usr/bin/killall monitor.sh || true
/usr/bin/killall instamsg || true

cp energy-meter_pi_11.9.0_11.9.0 ${HOME_DIRECTORY}/instamsg


