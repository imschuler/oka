#/sur/bin/env sh

# before running the script you should login to docker hub
# podman login docker.io
# As long as no Ansible image from SUSE ia available also
# podman login registry.redhat.io

DOCKER_ACCOUNT=imschuler
VERSION=0.6.1

IID=$(podman build ./apps/dhcpd)
if [ $? != 0 ]
then
  exit -1
fi

IID=$(echo $IID | awk '{ print $NF }')

podman tag $IID $DOCKER_ACCOUNT/oka-dhcpd:$VERSION

podman push $DOCKER_ACCOUNT/oka-dhcpd:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-dhcpd:$VERSION uploaded" 
fi

###
IID=$(podman build ./apps/tftpd)
if [ $? != 0 ]
then
  exit -1
fi

IID=$(echo $IID | awk '{ print $NF }')

podman tag $IID $DOCKER_ACCOUNT/oka-tftpd:$VERSION

podman push $DOCKER_ACCOUNT/oka-tftpd:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-tftpd:$VERSION uploaded" 
fi

###
IID=$(podman build ./apps/httpd)
if [ $? != 0 ]
then
  exit -1
fi

IID=$(echo $IID | awk '{ print $NF }')

podman tag $IID $DOCKER_ACCOUNT/oka-httpd:$VERSION

podman push $DOCKER_ACCOUNT/oka-httpd:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-httpd:$VERSION uploaded" 
fi

###
IID=$(podman build ./apps/isosd)
if [ $? != 0 ]
then
  exit -1
fi

IID=$(echo $IID | awk '{ print $NF }')

podman tag $IID $DOCKER_ACCOUNT/oka-isosd:$VERSION

podman push $DOCKER_ACCOUNT/oka-isosd:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-isosd:$VERSION uploaded" 
fi

###
IID=$(podman build ./jobs/install)
if [ $? != 0 ]
then
  exit -1
fi

IID=$(echo $IID | awk '{ print $NF }')

podman tag $IID $DOCKER_ACCOUNT/oka-install:$VERSION

podman push $DOCKER_ACCOUNT/oka-install:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-install:$VERSION uploaded" 
fi
