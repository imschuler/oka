#!/usr/bin/env python3

import subprocess, os, shutil, re, json

from typing import Union
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

class Repo(BaseModel):
    ins: Union[str, None] = None
    add: Union[str, None] = None
    drv: Union[str, None] = None

class Request(BaseModel):
    repos: List[Repo]

BASE_DIR="/srv/www/htdocs/_repos/"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

subprocess.run("/usr/sbin/httpd", shell=True, check=True)

app = FastAPI()

@app.post("/{install_id}")
def create_install(install_id: str, request: Request):
    input = request.dict()

    unmount(install_id)
    os.mkdir(BASE_DIR + install_id + "/")

    i = 0
    for repo in input["repos"]:
        i += 1
        repostr = "/repo"
        if i > 1:
            repostr = "/repo" + str(i)
        os.mkdir(BASE_DIR + install_id + repostr)

        url = None 
        for key in [ "ins", "add", "drv" ]:
            if repo[key] != None:
                url = repo[key]

        if repo["add"] != None or repo["ins"] != None:
            if url.startswith("file://"):
                dir = url[len("file://"):]
                os.system("mount -o ro,loop " + dir + " " + BASE_DIR + install_id + repostr) 
            elif url.startswith("nfs://"):
                dir = url[len("nfs://"):]
                os.system("mount -t nfs -o ro " + dir + " " + BASE_DIR + install_id + repostr) 
        else:
            if url.startswith("file://"):
                iso = url[len("file://"):]
                shutil.copy(iso, BASE_DIR + install_id + repostr)

    return { "status": " OK" }

@app.delete("/{install_id}")
def remove_install(install_id: str):

    unmount(install_id)

    return { "status": " OK" }

def unmount(install_id):
    if os.path.exists(BASE_DIR + install_id):
        for child in os.listdir(BASE_DIR + install_id):
            try:
               os.system("umount -l " + BASE_DIR + install_id + "/" + child)
            except:
               pass
    else:
        return

    empty = False
    while not empty:
        for root, dirs, files in os.walk(BASE_DIR + install_id):
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
        for child in os.listdir(BASE_DIR + install_id):
            empty = False
    os.rmdir(BASE_DIR + install_id)
