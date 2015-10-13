#!/bin/sh
### BEGIN INIT INFO
# Provides:          scriptname
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO
#
# chkconfig: 98 02
# description: This is a daemon for automatically
# start my service
#
# processname: ioeye
#

prefix=/usr
exec_prefix=/usr
sbindir=/usr/sbin
USER=pi
SCRIPT_LOCATION=/home/pi/Desktop/ioeye.py
SCRIPT_LOG_LOCATION=/var/log/ioeye
START_UP_LOG=${SCRIPT_LOG_LOCATION}/ioeye.log
SHUT_DOWN_LOG=${SCRIPT_LOG_LOCATION}/ioeye.log
IOEYE_PID_FILE=/var/run/ioeye.pid
PROCESS_NAME=ioeye
# Sanity checks.

# so we can rearrange this easily

RETVAL=0

start() {
  echo "Starting ioeye... "
  echo " log location is:" ${START_UP_LOG}
 if [ ! -f $TART_UP_LOG ]; then
    touch $TART_UP_LOG
  fi
  python $SCRIPT_LOCATION > $START_UP_LOG &
  if [ ! -f $IOEYE_PID_FILE ]; then
    touch $IOEYE_PID_FILE
  fi#!/bin/sh
#
#
#
# chkconfig: 98 02
# description: This is a daemon for automatically
# start my service
#
# processname: ioeye
#
#

prefix=/usr
exec_prefix=/usr
sbindir=/usr/sbin
USER=pi
SCRIPT_LOCATION=/home/pi/Desktop/ioeye.py
SCRIPT_LOG_LOCATION=/var/log/ioeye
START_UP_LOG=${SCRIPT_LOG_LOCATION}/ioeye.log
SHUT_DOWN_LOG=${SCRIPT_LOG_LOCATION}/ioeye.log
IOEYE_PID_FILE=/var/run/ioeye.pid
PROCESS_NAME=ioeye
# Sanity checks.

# so we can rearrange this easily

RETVAL=0

start() {
  echo "Starting ioeye... "
  echo " log location is:" ${START_UP_LOG}
 if [ ! -f $TART_UP_LOG ]; then
    touch $TART_UP_LOG
  fi
  python $SCRIPT_LOCATION > $START_UP_LOG &
  if [ ! -f $IOEYE_PID_FILE ]; then
    touch $IOEYE_PID_FILE
  fi
  sleep 5 
  echo $(pgrep -f $PROCESS_NAME) > $IOEYE_PID_FILE
  echo "Done starting ioeye! "
}

stop() {
  echo "Stopping ioeye... "
  echo " log location is:" ${SHUT_DOWN_LOG}
  echo $(pgrep -f $PROCESS_NAME) > $IOEYE_PID_FILE
  echo $(cat $IOEYE_PID_FILE)
  kill -KILL $(cat $IOEYE_PID_FILE)
  rm -rf $IOEYE_PID_FILE
  echo "Done stopping ioeye! "
}

case "$1" in
start)
  if [ ! -f $START_UP_LOG ]; then
    touch $START_UP_LOG
  fi
  start
  ;;
stop)
  if [ ! -f $SHUT_DOWN_LOG ]; then
    touch $SHUT_DOWN_LOG
  fi
  stop
  ;;
status)
  if [ -f $IOEYE_PID_FILE ]; then
    echo "ioeye running, everything is fine."
  fi
  ;;
restart)
  stop
  start
  ;;
condrestart)
  if [ -f /var/lock/subsys/$servicename ]; then
  stop
  start
  fi
  ;;
*)
  echo $"Usage: $0 {start|stop|status|restart|condrestart}"
  ;;

esac
exit $RETVAL
  sleep 5 
  echo $(pgrep -f $PROCESS_NAME) > $IOEYE_PID_FILE
  echo "Done starting ioeye! "
}

stop() {
  echo "Stopping ioeye... "
  echo " log location is:" ${SHUT_DOWN_LOG}
  echo $(pgrep -f $PROCESS_NAME) > $IOEYE_PID_FILE
  echo $(cat $IOEYE_PID_FILE)
  kill -KILL $(cat $IOEYE_PID_FILE)
  rm -rf $IOEYE_PID_FILE
  echo "Done stopping ioeye! "
}

case "$1" in
start)
  if [ ! -f $START_UP_LOG ]; then
    touch $START_UP_LOG
  fi
  start
  ;;
stop)
  if [ ! -f $SHUT_DOWN_LOG ]; then
    touch $SHUT_DOWN_LOG
  fi
  stop
  ;;
status)
  if [ -f $IOEYE_PID_FILE ]; then
    echo "ioeye running, everything is fine."
  fi
  ;;
restart)
  stop
  start
  ;;
condrestart)
  if [ -f /var/lock/subsys/$servicename ]; then
  stop
  start
  fi
  ;;
*)
  echo $"Usage: $0 {start|stop|status|restart|condrestart}"
  ;;

esac
exit $RETVAL
