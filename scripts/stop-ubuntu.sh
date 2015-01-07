#!/bin/bash

set -e

ctx logger info "Stopping HAProxy"
/etc/init.d/haproxy stop || exit 1
ctx logger info "Stopped HAProxy"
