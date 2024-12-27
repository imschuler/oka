#!/usr/bin/env python3
#
import subprocess, os, shutil, re, ipaddress, signal, socket

from typing import Union
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest

def render(in_file, out_file, args):
    with open(in_file, "r") as f:
        with open(out_file, "a") as g:
            for line in f:
                for k, v in args.items():
                    line = re.sub("{{ *" + k + " *}}", v, line)
                g.write(line)

def insert(in_file, out_file):
    # save a copy of out_file
    bak_file = out_file + ".bak"
    shutil.move(out_file, bak_file)

    begin_marker = "group {"
    
    with open(bak_file, "r") as f:
        with open(out_file, "a") as g:
            for line in f:
                if line.startswith(begin_marker):
                    g.write(line)
                    with open(in_file, "r") as h:
                        for line2 in h:
                            g.write(line2)
                    continue
                g.write(line)
    os.remove(bak_file)

def remove(out_file, mac):
    # save a copy of out_file
    bak_file = out_file + ".bak"
    shutil.move(out_file, bak_file)

    begin_marker = "# START MANAGED BY OKA " + mac
    end_marker = "# END MANAGED BY OKA " + mac

    match = False
    with open(bak_file, "r") as f:
        with open(out_file, "a") as g:
            for line in f:
                if begin_marker in line:
                    match = True
                    continue
                if end_marker in line:
                    match = False 
                    continue
                if not match:
                   g.write(line)
    os.remove(bak_file)

def restart_dhcpd():
    global proc

    if os.path.isfile("/var/run/dhcpd.pid"):
        print("pid file found")
        with open("/var/run/dhcpd.pid", "r") as f:
            for line in f:
                pid = int(line)
                os.kill(pid, signal.SIGTERM) 
            try:
                os.wait()
            except:
                pass
        os.remove("/var/run/dhcpd.pid")
    proc = subprocess.run([ "/usr/sbin/dhcpd" ], shell=True, check=True)
    
os.unsetenv("DHCPD_PORT")

app = FastAPI()

REQUESTS = Counter("oka_dhcp_requests_total", "HTTP Requests", labelnames=["method"])
EXCEPTIONS = Counter("oka_dhcp_errors_total", "HTTP Exceptions", labelnames=["method"])

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest())

@app.post("/")
async def create_root(subnet: str, netmask: str, range_begin: str, range_end: str):

    REQUESTS.labels("post").inc();
    with EXCEPTIONS.labels("post").count_exceptions():
        if os.path.isfile("/var/lib/dhcp/db/dhcpd.leases"):
            return { "status": " OK" }

        render("/templates/dhcpd.j2", "/etc/dhcpd.conf", { "subnet": subnet, "netmask": netmask, "range_begin": range_begin, "range_end": range_end })

        with open("/var/lib/dhcp/db/dhcpd.leases", "w"):
            pass

        restart_dhcpd()
        return { "status": " OK" }

@app.post("/{install_id}")
async def create_base(install_id: str, host: str, osid: str, ip: str, mac: str, shim: Union[str, None] = None, tftpd_ip_ext: Union[str, None] = None):

    REQUESTS.labels("post").inc();
    with EXCEPTIONS.labels("post").count_exceptions():
        if os.path.exists("/tmp/host.conf"):
            os.remove("/tmp/host.conf")

        remove("/etc/dhcpd.conf", mac)

        if not tftpd_ip_ext:
            render("/templates/host_none.j2", "/tmp/host.conf", { "install_id": install_id, "host": host, "osid": osid, "ip": ip, "mac": mac })
        else:
            render("/templates/host_tftp.j2", "/tmp/host.conf", { "install_id": install_id, "host": host, "osid": osid, "ip": ip, "mac": mac, "shim": shim, "tftpd_ip_ext": tftpd_ip_ext })

        insert("/tmp/host.conf", "/etc/dhcpd.conf")

        restart_dhcpd()
        return { "status": " OK" }

@app.delete("/{install_id}")
async def remove_base(install_id: str, mac: str):

    REQUESTS.labels("delete").inc();
    with EXCEPTIONS.labels("delete").count_exceptions():
        remove("/etc/dhcpd.conf", mac)

        restart_dhcpd()
        return { "status": " OK" }
