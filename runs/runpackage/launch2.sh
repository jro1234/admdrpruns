#!/bin/bash


./startdb.sh "${@:1:2}" & DB_PID=$!

./startclient.sh "${@:2}" & CLIENT_PID=$!

wait "$CLIENT_PID"
sleep 2
kill "$DB_PID"
sleep 10
