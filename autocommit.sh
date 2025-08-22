#!/bin/bash
# Auto commit + push every 5 minutes until stopped (Ctrl + C)

while true; do
  git add .
  git commit -m "Auto commit on $(date)"
  git push
  echo "✅ Auto commit done at $(date)"
  sleep 3600   # wait 1 hour
done

# bash autocommit.sh

# to run it forever
# nohup bash autocommit.sh &

# to check logs: git log --oneline | head -n 5

# to stop it later
# ps aux | grep autocommit
# You will see something like: nikhil   44705   0.0  bash autocommit.sh
# kill <PID> (Eg. kill 44705)