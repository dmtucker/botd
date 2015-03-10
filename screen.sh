#!/usr/bin/env sh
USAGE="usage: $(basename "$0") [cfg ...]"
[ "$#" -lt "1" ] && echo "$USAGE"
for cfg in "$@"
do
    if [ -e "$cfg" ]
    then
        printf "Generating $cfg... "
        screen -dS "$(basename "$cfg")" -m "$(dirname "$0")/botd.py" "$cfg"
        echo 'done'
        sleep 2
    else
        echo "$cfg does not exist."
    fi 
done

