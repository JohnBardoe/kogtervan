#!/bin/bash

> /tmp/bot.log # clear log (or create it)

python3 -u bot.py > /tmp/bot.log &

# wait for word Started in log and check if bot is running
while true; do
    if grep -q "Started" /tmp/bot.log; then
	echo "Bot started"
	break
    fi
    #check if bot is running
    if ! ps -ef | grep -v grep | grep -q "bot.py"; then
	echo /tmp/bot.log
	exit 1
    fi
    sleep 1
done
