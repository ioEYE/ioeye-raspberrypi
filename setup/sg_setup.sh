#!/bin/sh

. ../upgrade_params
PKG_VERSION="3"

###################### PERFORM ACTIONS NOW ##################################

/usr/bin/killall monitor.sh || true
/usr/bin/killall instamsg || true

cp ioeye_pi_11.9.0_11.9.0 ${HOME_DIRECTORY}/instamsg


