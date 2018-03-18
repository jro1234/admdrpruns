#!/bin/bash


./startdb.sh "$@" & DB_PID=$!

# This won't terminate except from an
# exterior kill such as on aprun container
wait "$DB_PID"
