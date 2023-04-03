# -*- coding: utf-8 -*-
# @Time: 2023/3/6 11:51
# @Author: Honvin
# @File: continue_monitor.py
# @Software: PyCharm

import requests

from pyTest.init_data import PROMETHEUS_HOST
from datetime import datetime
from pyTrainTicket.models import PromContinue


# 进行持续监控
def search_continue_promQL(ms_name, start_time, end_time):
    if ms_name:
        name = ms_name
    else:
        name = 'ts'
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$", name)
    # CPU利用率
    CPU_usage = 'sum by(instance, pod) (rate(container_cpu_usage_seconds_total{pod=~"%s.*"}[1m])) * 100' % name
    res_cpu_usage = continue_monitor('CPU_usage', CPU_usage, start_time, end_time)
    # 内存利用率
    memory_bandwidth_usage = 'sum(container_memory_working_set_bytes{pod=~"%s.*"}) by(namespace, pod, instance) / sum(container_spec_memory_limit_bytes{pod=~"%s.*"}) by(namespace, pod, instance) * 100' % (name, name)
    res_memory_bandwidth_usage = continue_monitor('memory_bandwidth_usage', memory_bandwidth_usage, start_time, end_time)
    # 内存使用量
    memory_usage = 'sum(container_memory_working_set_bytes {pod=~"%s.*"}) by(namespace, pod, instance)' % name
    res_memory_usage = continue_monitor('memory_usage', memory_usage, start_time, end_time)
    # 磁盘写入带宽
    disk_write = 'sum(rate(container_fs_writes_bytes_total{pod=~"%s.*"}[1m])) by(namespace, pod, instance)' % name
    res_disk_write = continue_monitor('disk_write', disk_write, start_time, end_time)
    # 磁盘读取带宽
    disk_read = 'sum(rate(container_fs_reads_bytes_total{pod=~"%s.*"}[1m])) by(namespace, pod, instance)' % name
    res_disk_read = continue_monitor('disk_read', disk_read, start_time, end_time)
    # 网络写入带宽
    net_write = 'sum(rate(container_network_receive_bytes_total{pod=~"%s.*"}[1m])) by(namespace, pod, instance)' % name
    res_net_write = continue_monitor('net_write', net_write, start_time, end_time)
    # 网络读取带宽
    net_read = 'sum(rate(container_network_transmit_bytes_total{pod=~"%s.*"}[1m])) by(namespace, pod, instance)' % name
    res_net_read = continue_monitor('net_read', net_read, start_time, end_time)

    return [
        res_cpu_usage,
        res_memory_bandwidth_usage,
        res_memory_usage,
        res_disk_write,
        res_disk_read,
        res_net_write,
        res_net_read,
        start_time,
        end_time,
    ]


def continue_monitor(metric_name, promql, start_time, end_time):
    # 构造Prometheus API查询URL
    query_url = f"{PROMETHEUS_HOST}/api/v1/query_range?query={promql}"

    # 查询时间范围：Unix时间戳，单位为秒
    start_time_sec = int(start_time.timestamp())
    end_time_sec = int(end_time.timestamp())
    print("时间范围：", start_time, "-", end_time)

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
                time = datetime.fromtimestamp(value[0])
                metric_value = value[1]
                update_database(pod_name, metric_name, metric_value, time)
                print(f"pod名称: {pod_name}"
                      f"\t指标名称: {metric_name}"
                      f"\t指标值:{metric_value} "
                      f"\t@ {time}")
        # print(result)
        return result
    else:
        print("查询Prometheus API失败！")


# 更新数据库
def update_database(pod_name, metric_name, metric_value, time):
    if metric_name == "CPU_usage":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'CPU_usage': metric_value}
        )
    elif metric_name == "memory_bandwidth_usage":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'memory_bandwidth_usage': metric_value}
        )
    elif metric_name == "memory_usage":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'memory_usage': metric_value}
        )
    elif metric_name == "disk_write":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'disk_write': metric_value}
        )
    elif metric_name == "disk_read":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'disk_read': metric_value}
        )
    elif metric_name == "net_write":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'net_write': metric_value}
        )
    elif metric_name == "net_read":
        PromContinue.objects.update_or_create(
            ms_name=pod_name, start_time=time, defaults={'net_read': metric_value}
        )


# graph展示的数据处理
def prom_data_opera():
    # 获取时间序列
    time_all = PromContinue.objects.all().values('start_time')
    time_list = []
    for time in time_all:
        time_list.append(time['start_time'])
    # 去重
    time_list = list(set(time_list))

    # 监控指标
    metric_list = [
        'CPU_usage',
        'memory_bandwidth_usage',
        'memory_usage',
        'disk_write',
        'disk_read',
        'net_write',
        'net_read'
    ]
    # 返回的结果
    result_data_list = []
    for metric in metric_list:
        # 获取数据库中的ms_name
        mss = PromContinue.objects.all().values('ms_name')
        ms_name_list = []
        for name in mss:
            ms_name_list.append(name['ms_name'])
        # 去重
        ms_name_list = list(set(ms_name_list))

        ms_list = []

        for ms in ms_name_list:
            # 获取每个微服务的指标，并按照时间排序
            data_all = PromContinue.objects.filter(ms_name=ms).values(metric).order_by('start_time')
            data_list = []
            for data in data_all:
                data_list.append(data[metric])

            # 处理返回数据
            ms_item = {
                'metric_name': ms,
                'data_list': data_list,
            }
            ms_list.append(ms_item)

        result_data = {
            'metric_name': metric,
            'ms_list': ms_list,
            'time_list': time_list
        }
        result_data_list.append(result_data)

    return result_data_list


