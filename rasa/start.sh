#!/bin/bash
#export SANIC_WORKERS=1
nohup python3 rasa run actions > /root/out.log 2>/root/error.log &
cd rasa
python3 __main__.py run --enable-api --model models --endpoints endpoints.yml
tail -f /dev/null
