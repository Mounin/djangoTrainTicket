# -*- coding: utf-8 -*-
# @Time: 2023/3/13 10:44
# @Author: Honvin
# @File: jaeger_monitor.py
# @Software: PyCharm
import json
import time

import requests
from django.utils import timezone

from django.core import serializers
from pyTrainTicket.models import Trace, Span, JaegerHotMS
from pyTest.init_data import PROMETHEUS_HOST
from datetime import datetime, timedelta
from pyTrainTicket.models import JaegerMonitor


def jaeger_get_monitor():
    # 获取所有的trace
    traces_all = Trace.objects.all()
    traces = []
    for trace in json.loads(serializers.serialize("json", traces_all)):
        traces.append(trace['fields'])

    for trace in traces:
        # 获取traces下的所有span
        trace_id = trace['trace_id']
        spans_all = Span.objects.filter(trace_id=trace_id)
        trace['spansData'] = []
        for span in json.loads(serializers.serialize("json", spans_all)):
            trace['spansData'].append(span['fields'])

        for span in trace['spansData']:
            # 获取对应时间戳的资源利用情况
            span_id = span['span_id']
            ms_name = span['ms_name']
            start_time = span['start_time']
            end_time = span['end_time']
            resourceData = jaeger_monitor_promQL(span_id, ms_name, start_time, end_time)
            print(resourceData)
            span['resourceData'] = [
                {
                    'CPU_usage': 'CPU_usage',
                    'CPU_user': 'CPU_user',
                    'memory_bandwidth_usage': 'memory_bandwidth_usage',
                    'memory_usage': 'memory_usage',
                    'disk_write': 'disk_write',
                    'disk_read': 'disk_read',
                    'net_write': 'net_write',
                    'net_read': 'net_read',
                }
            ]

    return traces


def jaeger_monitor_promQL(span_id, ms_name, start_time, end_time):
    # CPU系统态利用率
    CPU_usage = 'sum(rate(container_cpu_usage_seconds_total{pod=~"%s.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"%s.*"}/100000) by (pod, namespace, job, instance)) * 100 ' % (
    ms_name, ms_name)
    res_cpu_usage = jaeger_monitor('CPU_usage', CPU_usage, span_id, ms_name, start_time, end_time)
    # CPU用户态利用率
    CPU_user = 'sum(rate(container_cpu_user_seconds_total{pod=~"%s.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"%s.*"}/100000) by (pod, namespace, job, instance)) * 100' % (
    ms_name, ms_name)
    res_cpu_user = jaeger_monitor('CPU_user', CPU_user, span_id, ms_name, start_time, end_time)
    # 内存带宽占用率
    memory_bandwidth_usage = 'sum(rate(container_memory_working_set_bytes{container!="POD",pod=~"%s.*"}[5m])) by (pod, container, namespace) / sum(container_spec_memory_limit_bytes{container!="POD",pod=~"%s.*"}) by (pod, container, namespace)' % (
    ms_name, ms_name)
    res_memory_bandwidth_usage = jaeger_monitor('memory_bandwidth_usage', memory_bandwidth_usage, span_id, ms_name, start_time,
                                                  end_time)
    # 内存使用量
    memory_usage = 'sum(container_memory_working_set_bytes{container!="POD",pod=~"%s.*"}) by (namespace, pod, container)' % ms_name
    res_memory_usage = jaeger_monitor('memory_usage', memory_usage, span_id, ms_name, start_time, end_time)
    # 磁盘写入带宽占用率
    disk_write = 'sum(rate(container_fs_writes_bytes_total{pod=~"%s.*"}[5m])) by (pod)' % ms_name
    res_disk_write = jaeger_monitor('disk_write', disk_write, span_id, ms_name, start_time, end_time)
    # 磁盘读取带宽占用率
    disk_read = 'sum(rate(container_fs_reads_bytes_total{pod=~"%s.*"}[5m])) by (pod)' % ms_name
    res_disk_read = jaeger_monitor('disk_read', disk_read, span_id, ms_name, start_time, end_time)
    # 网络写入带宽占用率
    net_write = 'sum by (pod) (irate(container_network_transmit_bytes_total{pod=~"%s.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"%s.*"}) * 8' % (
    ms_name, ms_name)
    res_net_write = jaeger_monitor('net_write', net_write, span_id, ms_name, start_time, end_time)
    # 网络读取带宽占用率
    net_read = 'sum by (pod) (irate(container_network_receive_bytes_total{pod=~"%s.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"%s.*"}) * 8' % (
    ms_name, ms_name)
    res_net_read = jaeger_monitor('net_read', net_read, span_id, ms_name, start_time, end_time)
    return {
        'cpu_usage': res_cpu_usage,
        'cpu_user': res_cpu_user,
        'memory_bandwidth_usage': res_memory_bandwidth_usage,
        'memory_usage': res_memory_usage,
        'disk_write': res_disk_write,
        'disk_read': res_disk_read,
        'net_write': res_net_write,
        'net_read': res_net_read
    }


def jaeger_monitor(metric_name, promql, span_id, ms_name, start_time, end_time):
    # 构造Prometheus API查询URL
    query_url = f"{PROMETHEUS_HOST}/api/v1/query_range?query={promql}"

    # 查询时间范围：Unix时间戳，单位为秒
    print(start_time, end_time)

    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ')
    print(start_time, end_time)

    start_time_sec = int(start_time.timestamp())
    end_time_sec = int(end_time.timestamp())
    print("时间范围：", start_time, "-", end_time)
    print(start_time_sec, end_time_sec)
    # 查询参数：查询范围和数据采样频率
    params = {
        "start": start_time_sec,
        "end": end_time_sec,
        "step": 1  # 15秒采样一次数据
    }

    # 发送Prometheus API查询请求
    response = requests.get(query_url, params=params)
    # 解析查询结果
    result = response.json()
    print("#####################", result)
    if "data" in result and "result" in result["data"]:
        # 遍历所有时间序列
        for timeseries in result["data"]["result"]:
            values = timeseries["values"]
            # pod_name = timeseries["metric"]["pod"]
            # 遍历时间序列的值
            for value in values:
                # 查询时间
                timestamp = datetime.fromtimestamp(value[0])
                metric_value = value[1]
                update_database(span_id, ms_name, metric_name, metric_value)
        return result
    else:
        print("查询Prometheus API失败！")


# 更新数据库
def update_database(span_id, ms_name, metric_name, metric_value):
    if metric_name == "CPU_usage":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'CPU_usage': metric_value}
        )
    elif metric_name == "CPU_user":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'CPU_user': metric_value}
        )
    elif metric_name == "memory_bandwidth_usage":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'memory_bandwidth_usage': metric_value}
        )
    elif metric_name == "memory_usage":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'memory_usage': metric_value}
        )
    elif metric_name == "disk_write":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'disk_write': metric_value}
        )
    elif metric_name == "disk_read":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'disk_read': metric_value}
        )
    elif metric_name == "net_write":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'net_write': metric_value}
        )
    elif metric_name == "net_read":
        JaegerMonitor.objects.update_or_create(
            span_id=span_id, ms_name=ms_name, defaults={'net_read': metric_value}
        )


# 从数据库中获取资源数据
def get_resource_from_db():
    # 获取所有的trace
    traces_all = Trace.objects.all()
    traces = []
    for trace in json.loads(serializers.serialize("json", traces_all)):
        root_ms_name = trace['fields']['root_ms_name']
        trace_id = trace['fields']['trace_id']
        start_time = trace['fields']['start_time']
        duration = trace['fields']['duration']

        traces.append({
            'root_ms_name': root_ms_name,
            'trace_id': trace_id,
            'start_time': str(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")),
            'duration': str(timedelta(microseconds=duration))
        })

    for trace in traces:
        # 获取traces下的所有span
        trace_id = trace['trace_id']
        spans_all = Span.objects.filter(trace_id=trace_id)
        trace['spansData'] = []
        for span in json.loads(serializers.serialize("json", spans_all)):
            span_id = span['fields']['span_id']
            ms_name = span['fields']['ms_name']
            start_time = span['fields']['start_time']
            end_time = span['fields']['end_time']
            duration = span['fields']['duration']
            trace['spansData'].append({
                'span_id': span_id,
                'ms_name': ms_name,
                'start_time': str(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")),
                'end_time': str(datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")),
                'duration': str(timedelta(microseconds=duration)),
            })

        for span in trace['spansData']:
            # 获取对应时间戳的资源利用情况
            span_id = span['span_id']
            monitor = JaegerMonitor.objects.filter(span_id=span_id)
            resource = json.loads(serializers.serialize("json", monitor))[0]['fields']
            span['resourceData'] = [{
                'CPU_usage': resource['CPU_usage'],
                'CPU_user': resource['CPU_user'],
                'memory_bandwidth_usage': resource['memory_bandwidth_usage'],
                'memory_usage': resource['memory_usage'],
                'disk_write': resource['disk_write'],
                'disk_read': resource['disk_read'],
                'net_write': resource['net_write'],
                'net_read': resource['net_read'],
            }]

    return json.dumps(traces)


# 获取热点微服务
def hot_ms():
    JaegerHotMS.objects.all().delete()
    mss = Span.objects.values_list('ms_name', flat=True).distinct()
    for ms in mss:
        trace_list = []
        traces = Span.objects.filter(ms_name=ms).values_list('trace_id', flat=True)
        for trace in traces:
            if trace not in trace_list:
                trace_list.append(trace)
        JaegerHotMS.objects.update_or_create(
         ms_name=ms, defaults={'num': len(trace_list)}
        )

    hot_data_all = json.loads(serializers.serialize("json", JaegerHotMS.objects.filter()))
    hot_data = []
    for data in hot_data_all:
        hot_data.append(data['fields'])
    return hot_data
