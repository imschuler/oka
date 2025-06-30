#!/usr/bin/env python3

import subprocess, os, shutil, re, socket, urllib.error, urllib.request

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union
from typing import List
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest

class Repo(BaseModel):
    ins: Union[str, None] = None
    add: Union[str, None] = None
    drv: Union[str, None] = None

class Request(BaseModel):
    osid: str
    repos: List[Repo]
    httpd_ip_ext: str

BASE_DIR="/srv/tftpboot/"

TFTPD_CMD="in.tftpd -s -l -u root " + BASE_DIR

subprocess.run(TFTPD_CMD, shell=True, check=True)

app = FastAPI()

REQUESTS = Counter("oka_tftp_requests_total", "HTTP Requests", labelnames=["method"])
EXCEPTIONS = Counter("oka_tftp_errors_total", "HTTP Exceptions", labelnames=["method"])

@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest())

@app.post("/{install_id}")
async def create_base(install_id: str, request: Request):

    REQUESTS.labels("post").inc();
    with EXCEPTIONS.labels("post").count_exceptions():
        input = request.dict()

        if os.path.exists(BASE_DIR + install_id):
            shutil.rmtree(BASE_DIR + install_id)

        download(install_id)

        is_x64 = os.path.exists("/depot/bootx64.efi") or os.path.exists("/depot/BOOTX64.efi")
        prefix = input["osid"].split("_")[0]
        os.mkdir(BASE_DIR + install_id)

        if is_x64:
            os.makedirs(BASE_DIR + install_id + "/pxelinux/pxelinux.cfg")
            shutil.copy("/depot/syslinux-tftpboot-6.04-0.20.el9/tftpboot/pxelinux.0", BASE_DIR + install_id + "/pxelinux/")
            shutil.copy("/depot/syslinux-tftpboot-6.04-0.20.el9/tftpboot/ldlinux.c32", BASE_DIR + install_id + "/pxelinux/")

            if prefix == "suse":
                shutil.copy("/depot/linux", BASE_DIR + install_id + "/pxelinux/")
                shutil.copy("/depot/initrd", BASE_DIR + install_id + "/pxelinux/")
            elif prefix == "redhat":
                shutil.copy("/depot/vmlinuz", BASE_DIR + install_id + "/pxelinux/")
                shutil.copy("/depot/initrd.img", BASE_DIR + install_id + "/pxelinux/")

        os.mkdir(BASE_DIR + install_id + "/efi")
        if prefix == "suse":
            if is_x64:
                shutil.copy("/depot/bootx64.efi", BASE_DIR + install_id + "/efi/")
            else:
                shutil.copy("/depot/bootaa64.efi", BASE_DIR + install_id + "/efi/")
            shutil.copy("/depot/grub.efi", BASE_DIR + install_id + "/efi/")
        elif prefix == "redhat":
            if is_x64:
                shutil.copy("/depot/BOOTX64.EFI", BASE_DIR + install_id + "/efi/")
                shutil.copy("/depot/grubx64.efi", BASE_DIR + install_id + "/efi/")
            else:
                shutil.copy("/depot/BOOTAA64.EFI", BASE_DIR + install_id + "/efi/")
                shutil.copy("/depot/grubaa64.efi", BASE_DIR + install_id + "/efi/")

        shutil.copy("/depot/revocations.efi", BASE_DIR + install_id + "/efi/")

        if prefix == "suse":
            shutil.copy("/depot/linux", BASE_DIR + install_id + "/efi/")
            shutil.copy("/depot/initrd", BASE_DIR + install_id + "/efi/")
        elif prefix == "redhat":
            shutil.copy("/depot/vmlinuz", BASE_DIR + install_id + "/efi/")
            shutil.copy("/depot/initrd.img", BASE_DIR + install_id + "/efi/")

        if is_x64:
            render("/templates/default_" + prefix + ".j2", BASE_DIR + install_id + "/pxelinux/pxelinux.cfg/default", install_id, input)
        render("/templates/grub_" + prefix + ".j2", BASE_DIR + install_id + "/efi/grub.cfg", install_id, input)

        return { "status": " OK" }

@app.delete("/{install_id}")
async def remove_base(install_id: str):

    REQUESTS.labels("delete").inc();
    with EXCEPTIONS.labels("delete").count_exceptions():
        if os.path.exists(BASE_DIR + install_id):
            shutil.rmtree(BASE_DIR + install_id)

        return { "status": " OK" }

def render(in_file, out_file, install_id, input):
    with open(in_file, "r") as f:
        with open(out_file, "a") as g:
            for line in f:
                line = re.sub("{{ install_id }}", install_id, line)
                line = re.sub("{{ osid }}", input["osid"], line)
                line = re.sub("{{ httpd_ip_ext }}", input["httpd_ip_ext"], line)
                count = 0
                for repo in input["repos"]:
                    count += 1 
                    if repo["drv"] != None:
                        url = repo["drv"]
                        if url.startswith("file://"):
                            file = url[len("file://"):]
                            line = re.sub("inst.repo=([^ ]+)", r"inst.repo=\1 inst.dd=\1--", line)
                            line = re.sub("install=([^ ]+)", r"install=\1 dud=\1--", line)
                            line = re.sub("repo--", "repo" + str(count) + "/" + os.path.basename(file), line)
                line = re.sub(" dud=([^ ]+)", r" dud=\1 insecure=1", line, 1)
                g.write(line)

def download(install_id):

    for path in [ "boot/x86_64/loader/linux", "boot/x86_64/loader/initrd", "boot/aarch64/initrd", "boot/aarch64/linux", "images/pxeboot/initrd.img", "images/pxeboot/vmlinuz", "EFI/BOOT/grub.efi", "EFI/BOOT/bootx64.efi", "EFI/BOOT/grubx64.efi", "EFI/BOOT/BOOTX64.EFI", "EFI/BOOT/bootaa64.efi", "EFI/BOOT/BOOTAA64.EFI", "EFI/BOOT/grubaa64.efi" ]:
         
        url = "_repos/" + install_id + "/repo/" + path 
        basename = os.path.basename(path) 
        if os.path.exists("/depot/" + basename):
            os.unlink("/depot/" + basename)

        with open("/depot/" + basename, "wb") as f:
            try:
                content = urllib.request.urlopen("http://isosd/" + url).read()
                f.write(content)
            except urllib.error.URLError as error:
                print(str(error)) 

        if os.stat("/depot/" + basename).st_size == 0:
           os.unlink("/depot/" + basename)
