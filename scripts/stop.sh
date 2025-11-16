#!/bin/bash

pid_file="/tmp/fake_csaf_server.pid"
if [ -f "$pid_file" ]; then
    pid=$(cat "$pid_file")
    echo "Stopping fake CSAF server with PID $pid..."
    kill "$pid"
    rm "$pid_file"
    echo "Fake CSAF server stopped."
else
    echo "No PID file found. The fake CSAF server is probably not running."
fi
