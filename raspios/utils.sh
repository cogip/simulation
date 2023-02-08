#!/bin/bash

check_vars()
{
    var_names=("$@")
    for var_name in "${var_names[@]}"; do
        if [ -z "${!var_name}" ] ; then
            echo "Error: Variable ${var_name} not defined (in config.env file)"
            exit 1
        fi
    done
    return 0
}

get_robot_id()
{
    ROBOT_ID=${ROBOT_ID:-0}

    if (( $# > 1 ))
    then
        echo "Error: only one argument allowed ($# given)"
        return 1
    fi

    if (( $# == 1 ))
    then
        ROBOT_ID=$1
    fi

    if [[ ${ROBOT_ID} != +([[:digit:]]) ]]
    then
        echo "Error: robot id must be an integer: $1"
        return 1
    fi
    echo ${ROBOT_ID}
}