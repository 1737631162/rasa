#!/bin/bash
#export SANIC_WORKERS=1
cd /opt/vbot-intent-task-di
#/bin/bash svn.sh
nohup python3 /opt/vbot-intent-task-di/rasa run actions > /root/out.log 2>/root/error.log &
cd /opt/vbot-intent-task-di/rasa
python3 __main__.py run --enable-api --model models --endpoints endpoints.yml
tail -f /dev/null
