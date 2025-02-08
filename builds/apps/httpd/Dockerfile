FROM registry.suse.com/bci/bci-base:15.6

RUN zypper -n in python3 && zypper -n in python3-pip && zypper -n in python3-bcrypt && pip install fastapi && pip install uvicorn && pip install prometheus_client && mkdir /templates && zypper -n in nfs-client && zypper -n in util-linux && mkdir /srv/uvicorn

COPY ./main.py /bin/

COPY ./templates /templates

ENTRYPOINT [ "uvicorn", "bin.main:app", "--reload", "--host", "0.0.0.0", "--port", "8083" ]
