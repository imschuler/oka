FROM registry.suse.com/bci/bci-base:15.6 

RUN zypper -n in dhcp-server && zypper -n in python3 && zypper -n in python3-pip && pip install fastapi && pip install uvicorn && pip install prometheus-client && mkdir /templates

RUN sed 's/^DHCPD_RUN_CHROOTED=.*/DHCPD_RUN_CHROOTED="no"/' -i /etc/sysconfig/dhcpd

COPY ./main.py /bin/

COPY ./templates /templates

ENTRYPOINT [ "uvicorn", "bin.main:app", "--reload", "--host", "0.0.0.0", "--port", "8081" ]
