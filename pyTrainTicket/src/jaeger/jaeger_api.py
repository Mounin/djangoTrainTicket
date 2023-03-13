# -*- coding: utf-8 -*-
# @Time: 2023/3/9 17:18
# @Author: Honvin
# @File: jaeger_api.py
# @Software: PyCharm
import json
import time

import matplotlib
import networkx as nx
import requests
from datetime import datetime, timedelta

from django.core import serializers

from pyTest.init_data import JAEGER_HOST
from pyTrainTicket.models import Trace, Span


def jaeger_get_traces_and_span():
    jaeger_api_url = JAEGER_HOST + "/api/traces"
    # 获取所有的服务请求
    jaeger_get_services_url = JAEGER_HOST + "/api/services"
    res = requests.get(jaeger_get_services_url)
    services = res.json()['data']

    # 获取指定服务的trace
    services_list = ['ts-preserve-service', 'ts-rebook-service', 'ts-travel-plan-service']
    for service in services_list:
        jaeger_search(jaeger_api_url, service)

    # 获取所有的trace（消耗很大）
    # for service in services:
    #     jaeger_search(jaeger_api_url, service)


def jaeger_search(jaeger_api_url, service):
    # 定义查询参数
    start_time = int((time.time() - 3600) * 1000000)  # 一小时前的时间戳
    end_time = int(time.time() * 1000000)  # 当前时间的时间戳
    params = {
        # "start": start_time,
        # "end": end_time,
        "limit": 10,
        "service": service,
        # "lookback": '30m'
    }

    # 发送请求
    response = requests.get(jaeger_api_url, params=params)

    # 处理响应
    if response.status_code == 200:
        traces = response.json().get("data", [])
        print(f"从jaeger得到了 {len(traces)}个trace\n")
        for trace in traces:
            trace_id = trace['traceID']
            root_service_name = ''
            trace_duration = 0  # trace持续时间
            trace_start_time = 0  # trace开始时间
            # 获取trace持续时间
            for span in trace['spans']:
                if span['spanID'] == trace['traceID']:
                    process_id = span['processID']
                    root_service_name = trace['processes'][process_id]['tags'][0]['value']
                    trace_duration = span['duration']
                    trace_start_time = datetime.fromtimestamp(span["startTime"] / 1000000)
                    break
            Trace.objects.update_or_create(
                trace_id=trace_id,
                defaults={
                    'span_number': len(trace['spans']),
                    'root_ms_name': root_service_name,
                    'duration': trace_duration,
                    'start_time': trace_start_time
                }
            )

            # 获取span相关信息
            for span in trace["spans"]:
                process_id = span['processID']
                trace_id = span['traceID']
                parent_id = span['references'][0]['spanID'] if span['references'] else None
                span_id = span['spanID']  # spanID
                span_operation_name = span['operationName']  # span操作名称
                service_name = trace['processes'][process_id]['tags'][0]['value']  # 服务名称
                span_duration = span['duration']  # span持续时间
                # span_duration = datetime.fromtimestamp(span_duration_timestamp)  # span持续时间
                span_start_time = datetime.fromtimestamp(span["startTime"] / 1000000)  # span开始时间
                span_end_time = span_start_time + timedelta(microseconds=span_duration)  # span结束时间
                Span.objects.update_or_create(
                    span_id=span_id,
                    defaults={
                        'trace_id': trace_id,
                        'parent_id': parent_id,
                        'operation_name': span_operation_name,
                        'ms_name': service_name,
                        'duration': span_duration,
                        'start_time': span_start_time,
                        'end_time': span_end_time
                    }
                )
    else:
        print(f"Failed to get traces from Jaeger: {response.status_code} {response.reason}")


# 绘制有向无环图
def jaeger_draw_path(trace_id):
    root_node_id = trace_id
    root_ms_name = json.loads(serializers.serialize("json", Span.objects.filter(span_id=trace_id)))[0]['fields']['ms_name']
    spans_data = json.loads(serializers.serialize("json", Span.objects.filter(trace_id=trace_id)))
    spans = []
    matplotlib.use("Agg")  # 支持输出矢量图
    # 创建graph
    graph = nx.DiGraph()
    for span_data in spans_data:
        spans.append(span_data['fields'])
    for span in spans:
        ms_name = span['ms_name']
        span_id = span['span_id']
        parent_id = span['parent_id']
        span_duration = span['duration']

        # 添加节点
        if span_id == root_node_id:
            graph.add_node(span_id, label=ms_name, name=ms_name, symbolSize=30, category=0)
        elif parent_id == root_node_id:
            graph.add_node(span_id, label=ms_name, name=ms_name, symbolSize=20, category=1)
        else:
            graph.add_node(span_id, label=ms_name, name=ms_name, category=2)

        # 添加边
        if parent_id:
            graph.add_edge(parent_id, span_id, weight=span_duration)

    graph_data = nx.node_link_data(graph)

    graph_data['categories'] = [
        {'name': '根节点'},
        {'name': '第一个子节点'},
        {'name': '其他节点'}
    ]

    # 绘制关键路径
    critical_path = nx.dag_longest_path(graph, weight='weight')
    critical_root_node_id = critical_path[0]
    critical_graph = nx.DiGraph()
    for span in critical_path:
        ms_name = json.loads(serializers.serialize("json", Span.objects.filter(span_id=span)))[0]['fields']['ms_name']
        span_id = span
        parent_id = json.loads(serializers.serialize("json", Span.objects.filter(span_id=span)))[0]['fields']['parent_id']
        span_duration = json.loads(serializers.serialize("json", Span.objects.filter(span_id=span)))[0]['fields']['duration']
        # 添加节点
        if span_id == critical_root_node_id:
            critical_graph.add_node(span_id, label=ms_name, name=ms_name, symbolSize=30, category=0)
        elif parent_id == root_node_id:
            critical_graph.add_node(span_id, label=ms_name, name=ms_name, symbolSize=20, category=1)
        else:
            critical_graph.add_node(span_id, label=ms_name, name=ms_name, category=2)

        # 添加边
        if parent_id:
            critical_graph.add_edge(parent_id, span_id, weight=span_duration)

    critical_data = nx.node_link_data(critical_graph)
    critical_data['categories'] = [
        {'name': '根节点'},
        {'name': '第一个子节点'},
        {'name': '其他节点'}
    ]
    # 转成json格式
    return json.dumps(graph_data), json.dumps(critical_data)

