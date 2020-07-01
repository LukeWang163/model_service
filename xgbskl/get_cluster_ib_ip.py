#!/usr/bin/env python

from __future__ import print_function
import os
import socket
import time

# import the function from ip_mapper.py
from ip_mapper import get_ip
from ip_mapper import log
from ip_mapper import err


def get_host_by_name(hostname):
    while True:
        try:
            a = socket.gethostbyname(hostname)
            break
        except:
            pass
        time.sleep(1)
    return a


time.sleep(10)


CLUSTER_INFO_ENV = "BATCH_WORKER_HOSTS"
CURRENT_HOST_ENV = "BATCH_CURRENT_HOST"
CLUSTER_SERVER_INFO_ENV = "BATCH_SERVER_HOSTS"
GROUP_NAME = "BATCH_TASKGROUP_NAME"
JOB_ID_ENV = "BATCH_JOB_ID"

CUSTOM_IMAGE_TASK_NUMBER = "DLS_TASK_NUMBER"
CUSTOM_IMAGE_TASK_PREFIX = "BATCH_CUSTOM"
CUSTOM_IMAGE_TASK_SUFFIX = "_HOSTS"

host_list = []
port_list = []

if not (os.path.exists(os.getcwd() + '/ip_mapper.py')):
    err("ip_mapper.py not exist")
    exit(1)

if GROUP_NAME in os.environ:
    local_group_name = os.environ[GROUP_NAME]
    if local_group_name == "server":
        log("Current role is server, exit")
        exit(0)
else:
    err("Can not find batch group name")
    exit(1)

cluster_info_list = ""
if CLUSTER_INFO_ENV in os.environ:
    print("ENV BATCH_WORKER_HOSTS found")
    cluster_info_list = os.environ[CLUSTER_INFO_ENV]
else:
    # custom image case
    if CUSTOM_IMAGE_TASK_NUMBER in os.environ:
        print("ENV DLS_TASK_NUMBER found")
        svc_host_port_list = []
        for index in range(int(os.environ[CUSTOM_IMAGE_TASK_NUMBER])):
            batch_host = CUSTOM_IMAGE_TASK_PREFIX + str(index) + CUSTOM_IMAGE_TASK_SUFFIX
            if batch_host in os.environ:
                svc_host_port = os.environ[batch_host]
                svc_host_port_list.append(svc_host_port)

        if len(svc_host_port_list) > 0:
            cluster_info_list = ','.join(svc_host_port_list)

if cluster_info_list == "":
    err("Can not find the cluster info")
    exit(1)

current_host = os.environ[CURRENT_HOST_ENV]
job_id = os.environ[JOB_ID_ENV]

host_port_list = cluster_info_list.split(',')
for host_port in host_port_list:
    host_port_pair = host_port.split(':')
    host_list.append(host_port_pair[0])
    port_list.append(host_port_pair[1])

current_host_port_pair = current_host.split(':')
current_host_ip = get_host_by_name(current_host_port_pair[0])
current_host_port = current_host_port_pair[1]

env_host_list = []
for each_host in host_list:
    env_host = get_host_by_name(each_host)
    env_host_list.append(env_host)
    log("host name is %s, ip is %s" % (each_host, env_host))

env_host_port_list = []
for i in range(len(env_host_list)):
    env_host_port_list.append(env_host_list[i] + ':' + port_list[i])

network_card_name = os.environ.get('DLS_IPOIB_DEVICE', 'ib0')


command = 'python ip_mapper.py -c %s -H %s -p %s -i %s -l %s -P' % (" ".join(env_host_port_list),
           current_host_ip + ':' + current_host_port, current_host_port, network_card_name, job_id)
print(command)

p = os.popen(command)
new_host_str = p.read()
p.close()
print(new_host_str)

cluster_ip_path = os.getcwd() + '/.cluster_ib_ips'
fp1 = open(cluster_ip_path, 'w+')
fp1.write(new_host_str)
fp1.close()

local_ip_path = os.getcwd() + '/.local_ib_ip'
fp2 = open(local_ip_path, 'w+')
fp2.write(get_ip('ib0'))
fp2.close()
