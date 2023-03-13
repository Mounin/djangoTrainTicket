# -*- coding: utf-8 -*-
# @Time: 2023/3/6 11:51
# @Author: Honvin
# @File: single_monitor.py
# @Software: PyCharm

import requests

from pyTest.init_data import PROMETHEUS_HOST
from datetime import datetime
from pyTrainTicket.models import PromSingle


def search_all_promQL():
    # CPU系统态利用率
    CPU_usage = 'sum(rate(container_cpu_usage_seconds_total{pod=~"ts.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"ts.*"}/100000) by (pod, namespace, job, instance)) * 100 '
    res_cpu_usage = single_monitor('CPU_usage', CPU_usage)
    # CPU用户态利用率
    CPU_user = 'sum(rate(container_cpu_user_seconds_total{pod=~"ts.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"ts.*"}/100000) by (pod, namespace, job, instance)) * 100'
    res_cpu_user = single_monitor('CPU_user', CPU_user)
    # 内存带宽占用率
    memory_bandwidth_usage = 'sum(rate(container_memory_working_set_bytes{container!="POD",pod=~"ts-.*"}[5m])) by (pod, container, namespace) / sum(container_spec_memory_limit_bytes{container!="POD",pod=~"ts-.*"}) by (pod, container, namespace)'
    res_memory_bandwidth_usage = single_monitor('memory_bandwidth_usage', memory_bandwidth_usage )
    # 内存使用量
    memory_usage = 'sum(container_memory_working_set_bytes{container!="POD",pod=~"ts-.*"}) by (namespace, pod, container)'
    res_memory_usage = single_monitor('memory_usage', memory_usage)
    # 磁盘写入带宽占用率
    disk_write = 'sum(rate(container_fs_writes_bytes_total{pod=~"ts-.*"}[5m])) by (pod)'
    res_disk_write = single_monitor('disk_write', disk_write)
    # 磁盘读取带宽占用率
    disk_read = 'sum(rate(container_fs_reads_bytes_total{pod=~"ts-.*"}[5m])) by (pod)'
    res_disk_read = single_monitor('disk_read', disk_read)
    # 网络写入带宽占用率
    net_write = 'sum by (pod) (irate(container_network_transmit_bytes_total{pod=~"ts-.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"ts-.*"}) * 8'
    res_net_write = single_monitor('net_write', net_write)
    # 网络读取带宽占用率
    net_read = 'sum by (pod) (irate(container_network_receive_bytes_total{pod=~"ts-.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"ts-.*"}) * 8'
    res_net_read = single_monitor('net_read', net_read)

    return [
        res_cpu_usage,
        res_cpu_user,
        res_memory_bandwidth_usage,
        res_memory_usage,
        res_disk_write,
        res_disk_read,
        res_net_write,
        res_net_read
    ]


def single_monitor(metric_name, promql):
    # 构造Prometheus API查询URL
    query_url = f"{PROMETHEUS_HOST}/api/v1/query_range?query={promql}"

    # 查询时间范围：Unix时间戳，单位为秒
    end_time_sec = int(datetime.now().timestamp())
    start_time_sec = end_time_sec - 1
    print("时间范围：", datetime.fromtimestamp(start_time_sec), "-", datetime.fromtimestamp(end_time_sec))

    # 查询参数：查询范围和数据采样频率
    params = {
        "start": start_time_sec,
        "end": end_time_sec,
        "step": 15  # 15秒采样一次数据
    }

    # 发送Prometheus API查询请求
    response = requests.get(query_url, params=params)
    # 解析查询结果
    result = response.json()
    if "data" in result and "result" in result["data"]:
        # 遍历所有时间序列
        for timeseries in result["data"]["result"]:
            values = timeseries["values"]
            pod_name = timeseries["metric"]["pod"]
            # 遍历时间序列的值
            for value in values:
                # 查询时间
                timestamp = datetime.fromtimestamp(value[0])
                metric_value = value[1]
                update_database(pod_name, metric_name, metric_value)
                # print(f"pod名称: {pod_name}"
                #       f"\t指标名称: {metric_name}"
                #       f"\t指标值:{metric_value} "
                #       f"\t@ {timestamp}")
        print(result)
        return result
    else:
        print("查询Prometheus API失败！")


# 更新数据库
def update_database(pod_name, metric_name, metric_value):
    if metric_name == "CPU_usage":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'CPU_usage': metric_value}
        )
    elif metric_name == "CPU_user":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'CPU_user': metric_value}
        )
    elif metric_name == "memory_bandwidth_usage":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'memory_bandwidth_usage': metric_value}
        )
    elif metric_name == "memory_usage":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'memory_usage': metric_value}
        )
    elif metric_name == "disk_write":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'disk_write': metric_value}
        )
    elif metric_name == "disk_read":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'disk_read': metric_value}
        )
    elif metric_name == "net_write":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'net_write': metric_value}
        )
    elif metric_name == "net_read":
        PromSingle.objects.update_or_create(
            ms_name=pod_name, defaults={'net_read': metric_value}
        )
