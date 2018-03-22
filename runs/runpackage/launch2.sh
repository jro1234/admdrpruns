#!/bin/bash


./startdb.sh "$@" & DB_PID=$!

wait "$DB_PID"
