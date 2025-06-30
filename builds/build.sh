#/sur/bin/env sh

# before running the script you should login to docker hub
# podman login docker.io
# As long as no Ansible image from SUSE ia available also
# podman login registry.redhat.io

DOCKER_ACCOUNT=imschuler
VERSION=0.8.2

case $HOSTTYPE in
  aarch64)
    VERSION=arm64-$VERSION
    PLATFORM=linux/arm64
    ;;

  x86_64)
    VERSION=amd64-$VERSION
    PLATFORM=linux/amd64
    ;;
esac



IID=$(podman build --platform=$PLATFORM ./apps/dhcpd)
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
curl -L https://uefi.org/sites/default/files/resources/x64_DBXUpdate.bin -o ./apps/tftpd/depot/revocations.efi

IID=$(podman build --platform=$PLATFORM ./apps/tftpd)
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
IID=$(podman build --platform=$PLATFORM ./apps/httpd)
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
IID=$(podman build --platform=$PLATFORM ./apps/isosd)
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
ansible-builder build -t $DOCKER_ACCOUNT/oka-install:$VERSION -f ./jobs/install/execution-environment.yaml

podman push $DOCKER_ACCOUNT/oka-install:$VERSION
if [ $? == 0 ]
then
  echo "$DOCKER_ACCOUNT/oka-install:$VERSION uploaded" 
fi
