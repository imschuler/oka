#!/usr/bin/env sh

NAMESPACE=kodaira
export NAMESPACE

kubectl create configmap ansible-vars -n $NAMESPACE --from-file=vars.yaml

(cd tasks; kubectl create configmap ansible-tasks -n $NAMESPACE --from-file=01-containerd.yaml  --from-file=02-cni.yaml  --from-file=03-kubelet.yaml --from-file=04-other.yaml)

(cd templates; kubectl create configmap ansible-templates -n $NAMESPACE --from-file=proxy.j2 --from-file=chrony.j2)
