FROM registry.suse.com/bci/bci-base:15.6 

RUN zypper -n in apache2 && zypper -n in python3 && zypper -n in python3-pip && zypper -n in python3-bcrypt && pip install fastapi && pip install uvicorn && pip install prometheus-client && zypper -n in nfs-client && zypper -n in util-linux

RUN sed 's/^Listen 80 */Listen 84/' -i /etc/apache2/listen.conf

COPY ./main.py /bin/

ENTRYPOINT [ "uvicorn", "bin.main:app", "--reload", "--host", "0.0.0.0", "--port", "8084" ]
