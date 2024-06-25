# Intro
An install server ( mainly ) for PRIMERGY servers, based on Ansible and Kubernetes

But it may be extended to install Linux on other bare metal servers and virtual machines. 

The project was meant as an exercise to learn Ansible and Kubernetes and since Linux installation is something useful, which is frequently needed, I choose this as the goal.

Currently the Linux distros SLES and RHEL are supported.

A notable feature of the install server is, that it allows to specify post Ansible tasks, that are run after the proper installation.

So, it may be easily extended and adpated to your needs.

An example would be:
```
- name: update to the latest software
  ansible.builtin.package:
    name: "*"
    state: latest

- name: reboot
  ansible.builtin.reboot:
    reboot_timeout: 900
```

# Network Environment

There are basically two environments in which the install server may be used:

- the server is connected to two subnets, one of which has access to the Internet and is configured by DHCP and the other subnet is used for PXE booting the system

![Use Case 1](/images/oka_1.jpg)

- the server is connected to a single subnet, that is statically configured with access to the Internet and may be used for PXE booting as well

![Use Case 2](/images/oka_2.jpg)

The rationale behing this is that, it is difficult to PXE boot in a subnet that already has a DHCP server running

# Installation Notes for the K8s cluster

To run this install server, you need to setup a Kubernetes Cluster.

I have tested using SUSEs K3s distro on SLES 15 SP5.

Take care that k3s puts the load balancers on the proper subnet for PXE booting.

As an example, if your PXE subnet is 203.0.113.0/24 and the K3s cluster has 203.0.113.13 as IP address, set the following 

`node-external-ip: 203.0.113.13`

in `/etc/rancher/k3s/config.yaml`

before launching k3s.

# Setting up the Install Server 

The install server uses Helm to start a Linux installation in a Kubernetes job.

First download the sources of this GitHub project, that also contains three Helm charts.

A PXE subnet must be configured using Helm settings. The details will differ depending on your infrastructure.

Here is an example
```
subnet:
  subnet:                 "192.168.130.0"
  netmask:                "255.255.254.0"
  range_begin:            "192.168.130.100"
  range_end:              "192.168.131.249"
  domain:                 ..
  smt_server:             ..
  smt_fingerprint:        ".."
  proxy_host:             ..
  proxy_port:             ..
```

Note that the last four settings are optional ( SMT server, proxy ).

Each host to be installed must be configured previously and the interfaces to the subnets are specified using the MAC address.

Example:
```
  - host:           kub6
    locale:         en_US.UTF-8
    disk:           /dev/disk/by-id/scsi-35000c50086ed8342
    host_name:      kub6
    timezone:       Europe/Berlin
    pxe:
      ip:           "192.168.131.169"
      mac:          "90:1b:0e:63:ac:7b"
    inet:
      mac:          "90:1b:0e:62:d9:a8"
    irmc:
      ip:           "172.17.31.168"
      user:         ..
      password:     ..
```

As explained above the pxe settings are optional, if you use the inet subnet for PXE boots.

It is important to note, that host and host_name may differ, so you may use different disks on a single PRIMERGY.

The Iso files to be used for installation should be present on the install server and are referenced by a so-called osid.

Here are two examples:

```
- osid:           suse_sles15_5
    repos:          [ { ins: "file:///srv/isos/SLE-15-SP5-Full-x86_64-GM-Media1.iso" } ]
    product:        SLES
    packages:       [ "python3", "sudo", "openssh", "wget" ]

- osid:           redhat_rhel9_2
    repos:          [ { ins: "file:///srv/isos/RHEL-9.2.0-20230414.17-x86_64-dvd1.iso" } ]
    packages:       [ "@^minimal-environment" ]
```

You will need to install Helm version 3 on some machine with access to the k3s cluster.

The basic services and configMaps are installed into the namespace oka-system. This name cannot be changed.

Currently only a single subnet may be configured. The Helm chart oka-apps starts the services and oka-base configures subnet, hosts and osids.

```
# kubectl create namespace oka-system

# helm install apps oka-apps -n oka-system

# helm install base oka-base -n oka-system --values "your values"
```

# Installing a Host 

An installation of one of the hosts configured previously, now basically requires a single helm command. You will, however, need to specify some settings e.g. in a values YAML file :

SUSE:
```
osid:                   suse_sles15_5
host:                   kub6
suse_activation_key:
```
Red Hat:
```
osid:                   redhat_rhel9_2
host:                   kub6
redhat_pool_id:         ..
```

Then run the commands below:

Choose any namespace name ( like you surname ) and create a Kubernetes namespace.

In that namespace credentials are stored as shown below. But recall, that in a non-production environment Kubernetes secrets are often not encrypted.

Post Ansible tasks are optional and if you want to use them, you must create a ConfigMap for the tasks and optionally for variables.

You may install as many systems as you like from that namespace, but they will share credentials and post Ansible tasks, until you modify them. 

Note that the secret and configMap are not part of the Helm release and hence will not be removed from the namespace if you uninstall the release.

The names for the ConfigMaps ansible-vars and ansible-tasks and secret access is fixed, while the name of the namespace ( kodaira in the example ) is arbitrary.

```
# kubectl create namespace kodaira

# kubectl create secret generic access -n kodaira --from-file=id_rsa="..." --from-file=pub_key="..." --from-file=certificate="..." \
                                                  --from-literal=root_password="..." --from-literal=redhat_username="..." --from-literal=redhat_password="..." \
                                                  --from-literal=email_addr="..."

# kubectl create configMap ansible-tasks -n kodaira --from-file=ansible-tasks="..."

# kubectl create configMap ansible-vars -n kodaira --from-file=ansible-vars="..."

# cd oka/charts

# helm install "your release name" oka-install -n kodaira --values "your values"
```
On the installed system, after the installation is complete, you may login as root or ansible user via SSH and the SSH keypair above may be used to to so.

Login as root user with the configured password is also possible.


# Post Ansible Tasks

As mentioned above, this install server makes it easy to run post installation tasks written in Ansible.

This is demonstrated here by running a standard Hello World task.

In general, three files are needed: one with Ansible variables, one with tasks and one with templates.

The ConfigMaps must be in the same namespace the installer job will be run and the names are fixed:

```
ansible-vars
ansible-tasks
ansible-templates
```

The files for variables and tasks must have the extension .yaml and are included in alphabetical order, if several of them are in the configMaps.

```
# cat hello.yaml 
message: "Hello World"

# cat 01-hello.yaml 
- name: print message
  debug:
    var: message

# kubectl create configmap ansible-vars --from-file=hello.yaml -n kodaira

# kubectl create configmap ansible-tasks --from-file=01-hello.yaml -n kodaira
```

Run the install job then and view the output using kubectl logs command:
```
TASK [include Ansible variables] ***********************************************
task path: /depot/step_9.yml:22
ok: [node1] => (item=/depot/ansible-vars/hello.yaml) => {
    "ansible_facts": {
        "message": "Hello World"
    },
    "ansible_included_var_files": [
        "/depot/ansible-vars/hello.yaml"
    ],
    "ansible_loop_var": "item",
    "changed": false,
    "item": "/depot/ansible-vars/hello.yaml"
}

TASK [import post Ansible tasks] ***********************************************
task path: /depot/step_9.yml:28
included: /depot/ansible-tasks/01-hello.yaml for node1 => (item=/depot/ansible-tasks/01-hello.yaml)

TASK [print message] ***********************************************************
task path: /depot/ansible-tasks/01-hello.yaml:1
ok: [node1] => {
    "message": "Hello World"
}
```
# Creating your own osid Identifiers

The installations discussed so far, work in general, but in a professional environment you might have more demanding requirements, that may be solved using OEM drivers-

For the supported SLES and RHEL distros, Fujitsu has released OEM drivers that you find for download on https://support.ts.fujitsu.com .

Using the ISO images from there, you may include the drivers during the installation and define you own osids.

```
- osid:           redhat_rhel8_8_oem
  repos:          [ { ins: "file:///srv/isos/RHEL-8.8.0-20230411.3-x86_64-dvd1.iso" },
                  { drv: "file:///srv/isos/i40e-2.23.17-1.el8.8-000.x86_64.iso" },
                  { drv: "file:///srv/isos/igb-5.14.16-1.el8.8-000.x86_64.iso" } ]
  packages:       [ "@^minimal-environment" ]
```
This is based on the Driver Update features in SLES and RHEL ( dud or inst.dd parameters ) during installation.

# Known Issues

- properly initiating the first PXE boot still needs to be improved - until then help yourself with a suitable boot menu
- only a single subnet may be configured currently
- the limitation to PRIMERGY servers should be lifted ( virtual machines should be supported as well )
- more configuration options for the root filesystem should be provided ( LVM, MD, etc. )
- SMT servers are no longer state of the art - RMT is the successor
- there should be a way to blacklist drivers
# Troubleshooting

Depending on the infrastructure, it may happen that rebooting the systems takes a lot of time. 

In that case it may be a good idea to check the boot order or login to the console to see what the system is waiting for.  

Also the inital PXE boot of the server will often require manual intervention.

# Side Remarks

- running Ansible tasks in Kubernetes jobs is a perfect match, since Ansible tasks are idempotent and Kubernetes automatically repeats failed jobs
- air gapped installations are currently not supported
- The project is named after Kiyoshi Oka, a Japanese mathematician. Kunihiko Kodaira was a well-known mathematician as well.
