FROM registry.suse.com/bci/bci-base:15.5 

RUN zypper -n in tftp && zypper -n in python3 &&  zypper -n in python3-pip && pip install fastapi && pip install uvicorn && mkdir /depot && mkdir /templates

COPY ./main.py /bin/

COPY ./depot /depot
 
COPY ./templates /templates

ENTRYPOINT [ "uvicorn", "bin.main:app", "--reload", "--host", "0.0.0.0", "--port", "8082" ]
