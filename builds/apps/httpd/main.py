#!/usr/bin/env python3

# expects environment variables
# HTTPD_ID
# NFS_SERVER_IP

import subprocess, os, shutil, re, json, hashlib, socket

from typing import Union
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

BASE_DIR="/srv/uvicorn/"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

class Repo(BaseModel):
    ins: Union[str, None] = None
    add: Union[str, None] = None
    drv: Union[str, None] = None

class Request(BaseModel):
    osid: str
    repos: List[Repo]
    disk: str
    product: Union[str, None] = None 
    root_password: str
    pub_key: str
    packages: List[str]
    locale: str
    httpd_ip_ext: str
    pxe_mac: str

class Interface(BaseModel):
    mac: str
    ip: str

class Message(BaseModel):
    product: Union[str, None] = None 
    serial_number: Union[str, None] = None 
    disk: Union[str, None] = None
    uuid: Union[str, None] = None
    interfaces: List[Interface]
    pxe_bootnum: Union[str, None] = None

app = FastAPI()

@app.get("/{install_id}/{file}")
def get_file(install_id: str, file: str):
    try:
       with open(BASE_DIR + install_id + "/" + file, "r") as f:
          return HTMLResponse(f.read(), status_code=200)
    except:
       pass
    return HTMLResponse("", status_code=404)

@app.put("/{install_id}/{file}")
def create_file(install_id: str, file: str, message: Message):
    input = message.dict()

    with open(BASE_DIR + install_id + "/" + file, "w") as f:
        json.dump(input, f)
    return { "status": " OK" }

@app.post("/{install_id}")
def create_install(install_id: str, request: Request):
    input = request.dict() 

    cleanup(BASE_DIR + install_id + "/")
    os.mkdir(BASE_DIR + install_id + "/")

    prefix = input["osid"].split("_") [0]
    if prefix == "redhat":
        render("/templates/ks.j2", BASE_DIR + install_id + "/ks.cfg", install_id, input)
    elif prefix == "suse":
        render("/templates/autoinst.j2", BASE_DIR + install_id + "/autoinst.xml", install_id, input)

    render("/templates/pre_" + prefix + ".j2", BASE_DIR + install_id + "/pre.sh", install_id, input)
    render("/templates/post_" + prefix + ".j2", BASE_DIR + install_id + "/post.sh", install_id, input)

    return { "status": " OK" }

@app.delete("/{install_id}")
def remove_install(install_id: str):
    cleanup(BASE_DIR + install_id + "/")

    return { "status": " OK" }

def cleanup(dir):
    if not os.path.exists(dir):
        return 

    empty = False
    while not empty:
        for root, dirs, files in os.walk(dir):
            for d in dirs:
                if os.path.islink(os.path.join(root, d)):
                   os.unlink(os.path.join(root, d))
                elif not os.listdir(os.path.join(root, d)):
                   os.rmdir(os.path.join(root, d))
            for f in files:
                if os.path.islink(os.path.join(root, f)):
                   os.unlink(os.path.join(root, f))
                else:
                   os.remove(os.path.join(root, f))

        empty = True
        for child in os.listdir(dir):
            empty = False
    os.rmdir(dir)

def render(in_file, out_file, install_id, input):
    with open(in_file, "r") as f:
        packages = None
        addon_repo = None
        product = None

        skip_line = False

        with open(out_file, "a") as g:
            for line in f:
                if "{% if addon_repo %}" in line:
                    if "sles15" in input["osid"] and "repos" in input:
                        for key in [ "add", "ins" ]:
                            count = 0
                            for repo in input["repos"]:
                                count += 1
                                if addon_repo == None and repo[key] != None:
                                    if count == 1:
                                       addon_repo = "repo"
                                    else:
                                       addon_repo = "repo" + str(count)
                    if addon_repo == None:
                        skip_line = True
                    continue

                if "{% if packages %}" in line:
                    if "packages" in input:
                        packages = ""
                        for package in input["packages"]:
                            if input["osid"].startswith("suse"):
                                packages = packages + "<package>" + package + "</package>\n"
                            else:
                                packages = packages + "\n" + package
                        else:
                            skip_line = True
                    continue

                if "{% if product %}" in line:
                    if "product" in input:
                        product = input["product"]
                    else:
                        skip_line = True
                    continue

                if "{% endif %}" in line:
                    skip_line = False
                    product = None
                    packages = None
                    addon_repo = None
                    continue

                line = re.sub("{{ *osid *}}", input["osid"], line)
                line = re.sub("{{ *disk *}}", input["disk"], line)
                line = re.sub("{{ *root_password *}}", input["root_password"], line)
                line = re.sub("{{ *pub_key *}}", input["pub_key"], line)
                line = re.sub("{{ *locale *}}", input["locale"], line)
                line = re.sub("{{ *install_id *}}", install_id, line)
                line = re.sub("{{ *httpd_ip_ext *}}", input["httpd_ip_ext"], line)
                line = re.sub("{{ *pxe_mac *}}", input["pxe_mac"], line)

                if product != None:
                    line = re.sub("{{ *product *}}", product, line)
                    g.write(line)
                    continue
                if packages != None:
                    line = re.sub("{{ *packages *}}", packages, line)
                    g.write(line)
                    continue
                if addon_repo != None:
                    line = re.sub("{{ *addon_repo *}}", addon_repo, line)
                    g.write(line)
                    continue

                if not skip_line:
                    g.write(line)
