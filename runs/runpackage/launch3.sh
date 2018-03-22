#!/bin/bash


./startclient.sh "$@" & CLIENT_PID=$!

wait "$CLIENT_PID"
