#!/bin/bash

cd ~/palr-web-service;

if [[ -a server_pid.txt ]]; then
    kill -9 $(cat server_pid.txt)
fi

git pull origin master

nohup python herokurunserver.py > log.log 2> error.log &

echo $! > server_pid.txt
