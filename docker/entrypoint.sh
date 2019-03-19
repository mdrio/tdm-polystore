#!/bin/bash

set -euo pipefail
[ -n "${DEBUG:-}" ] && set -x

function onshutdown {
    hdfs --daemon stop datanode
    hdfs --daemon stop namenode
}

trap onshutdown SIGTERM SIGINT

function log() {
    echo -e "${@}" >&2
}

# Hadoop shell scripts assume USER is defined
export USER="${USER:-$(whoami)}"

# allow HDFS access from outside the container
sed -i s/localhost/${HOSTNAME}/ /opt/hadoop/etc/hadoop/core-site.xml

log "Formatting namenode..."
hdfs namenode -format -force

log "Starting namenode"
hdfs --daemon start namenode

sleep 30
log "Starting datanode"
hdfs --daemon start datanode

log "Waiting for hdfs to come out of safe mode"
timeout 30 bash -c -- 'hdfs dfsadmin -safemode wait' || \
    hdfs dfsadmin -safemode leave

tail -f /opt/hadoop/logs/hadoop-${USER}-{datanode,namenode}-${HOSTNAME}.log

onshutdown
