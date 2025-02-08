#/sur/bin/env sh

# before running the script you should login to docker hub
# podman login docker.io

DOCKER_ACCOUNT=imschuler
VERSION=0.8.1

for ITEM in oka-dhcpd oka-tftpd oka-httpd oka-isosd oka-install
do

  podman manifest create $DOCKER_ACCOUNT/$ITEM:$VERSION

  podman pull $DOCKER_ACCOUNT/$ITEM:amd64-$VERSION

  podman manifest add $DOCKER_ACCOUNT/$ITEM:$VERSION $DOCKER_ACCOUNT/$ITEM:amd64-$VERSION

  podman pull $DOCKER_ACCOUNT/$ITEM:arm64-$VERSION

  podman manifest add $DOCKER_ACCOUNT/$ITEM:$VERSION $DOCKER_ACCOUNT/$ITEM:arm64-$VERSION

  podman manifest push $DOCKER_ACCOUNT/$ITEM:$VERSION
  if [ $? == 0 ]
  then
    echo "$ITEM pushed"
  fi
done
