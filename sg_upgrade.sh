#!/bin/sh

. ./upgrade_params

set -e

cd "${HOME_DIRECTORY}"

touch auto_upgrade
enabled=`cat "auto_upgrade"`
if [ ${enabled} = "0" ]
then
    echo "Upgrade is disabled ... aborting .."
    exit
fi


touch version.txt
rm -f version.txt
wget "${VERSION_URL}"


prev_version=`cat "${HOME_DIRECTORY}/current_version"`
new_version=`cat "version.txt"`
if [ -z "${prev_version}" ]
then
    echo "Current-Version not available ... aborting .."
    exit
fi
if [ -z "${new_version}" ]
then
    echo "New Package-Version not available ... aborting .."
    exit
fi
if [ "${new_version}" -gt "${prev_version}" ]
then
    echo "Upgrade will proceed now ..."
else
    echo "No new version available !!"
    exit
fi


rm -f setup.zip
rm -f setup.zip*
rm -rf setup
wget "${PLATFORM}"
${EXTRACT_COMMAND}

cd setup
chmod 777 ./sg_setup.sh
./sg_setup.sh

echo "${new_version}" > "${HOME_DIRECTORY}/current_version"
${REBOOT_COMMAND}
