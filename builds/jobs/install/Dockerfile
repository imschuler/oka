FROM registry.redhat.io/ansible-automation-platform/ee-minimal-rhel9:2.16.5-2

# COPY ./certificate.pem /etc/pki/ca-trust/source/anchors/

RUN update-ca-trust && mkdir /depot && ansible-galaxy collection install ansible.posix && ansible-galaxy collection install community.general && ansible-galaxy collection install ansible.netcommon && python3 -m pip install pyghmi && python3 -m pip install netaddr && python3 -m pip install jmespath

COPY ./depot /depot

WORKDIR /depot

ENTRYPOINT ansible-playbook -vvv step_${JOB_COMPLETION_INDEX}.yml
