# -*- coding: utf-8 -*-
# @Time: 2023/2/20 16:22
# @Author: Lemon_Honvin
# @File: jaeger_api.py
# @Software: PyCharm

import json
import math
import requests
import matplotlib
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from prometheus_api import prometheus_api
from init_data import JAEGER_HOST


# 获取jaeger收集到的span数据
def get_span():
    jaeger_api_url = JAEGER_HOST + "/api/traces"

    # 定义查询参数
    params = {
        "limit": 1,
        "service": "ts-rebook-service"
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
            trace_end_time = 0  # trace结束时间
            # 获取trace持续时间
            for span in trace['spans']:
                if span['spanID'] == trace['traceID']:
                    process_id = span['processID']
                    root_service_name = trace['processes'][process_id]['serviceName']
                    trace_duration = span['duration']
                    trace_start_time = datetime.fromtimestamp(span["startTime"] / 1000000)
                    trace_end_time = trace_start_time + timedelta(microseconds=trace_duration)
                    break
            print(f"\n{'=' * 70}"
                  f"\ntraceID:{trace_id}"
                  f"\n开始时间:{trace_start_time}"
                  f"\n结束时间:{trace_end_time}"
                  f"\n持续时间:{trace_duration}"
                  f"\nspan数量:{len(trace['spans'])}"
                  f"\n{'=' * 70}")

            # 获取span相关信息
            for span in trace["spans"]:
                process_id = span['processID']
                span_index = trace["spans"].index(span) + 1  # span数
                span_id = span['spanID']  # spanID
                span_operation_name = span['operationName']  # span操作名称
                service_name = trace['processes'][process_id]['serviceName']  # 服务名称
                span_duration = span['duration']  # span持续时间
                span_start_time = datetime.fromtimestamp(span["startTime"] / 1000000)  # span开始时间
                span_end_time = span_start_time + timedelta(microseconds=span_duration)  # span结束时间
                # 输出标记中的服务名称
                service_path = ""
                for tag in span["tags"]:
                    if tag["key"] == "http.url":
                        url_parts = tag["value"].split("/")
                        # 假设服务路径是第4个元素
                        service_path = url_parts[5]
                print(f"{'-'*41}\n"
                      f"|{'span数:':<12}|{span_index:<26}|\n"
                      f"|{'spanID:':<12}|{span_id:<26}|\n"
                      f"|{'service名称:':<11}|{service_name:<26}|\n"
                      f"|{'service路径:':<11}|{service_path:<26}|\n"
                      f"|{'span操作:':<11}|{span_operation_name:<26}|\n"
                      f"|{'开始时间:':<10}|{span_start_time}|\n"
                      f"|{'结束时间:':<10}|{span_end_time}|\n"
                      f"|{'持续时间:':<10}|{span_duration:<26}|\n"
                      f"{'-'*41}")

                prometheus_api(span_start_time, span_end_time, service_name)

            jaeger_dag(json.dumps(trace), root_service_name)
    else:
        print(f"Failed to get traces from Jaeger: {response.status_code} {response.reason}")


# 绘制微服务路径的有向无环图
def jaeger_dag(trace, root_service_name):
    matplotlib.use("Agg")  # 支持输出矢量图

    trace_data = json.loads(trace)
    root_node_id = trace_data['traceID']

    # 创建graph
    graph = nx.DiGraph()

    for span in trace_data['spans']:
        process_id = span['processID']
        service_name = trace_data['processes'][process_id]['serviceName']
        span_id = span['spanID']
        parent_id = span['references'][0]['spanID'] if span['references'] else None

        # 添加节点
        graph.add_node(span_id, label=service_name)

        # 添加边
        if parent_id:
            graph.add_edge(parent_id, span_id)

    # 获取每个节点到根节点的最短路径长度
    # 根据节点不同，颜色不同：根节点为红色，第一个父节点为蓝色，其余节点为绿色
    depth = nx.shortest_path_length(graph, source=root_node_id)
    node_color = []
    for node in graph.nodes():
        if depth[node] == 0:
            node_color.append('r')
        elif depth[node] == 1:
            node_color.append('b')
        else:
            node_color.append('g')

    # 计算画布大小
    num_nodes = len(graph.nodes)
    fig_width = max(10, 0.5 * num_nodes)
    fig_height = max(10, math.ceil(num_nodes/10))
    plt.figure(figsize=(fig_width, fig_height))

    # 绘图
    pos = nx.spring_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=100, node_color=node_color)
    # 添加标签
    nx.draw_networkx_labels(graph, pos, labels=nx.get_node_attributes(graph, 'label'), font_size=6)
    # 绘制边
    nx.draw_networkx_edges(graph, pos, arrowstyle='->', arrowsize=10)
    plt.axis('off')
    # plt.show()
    # 输出PDF矢量图
    plt.savefig(f"{root_service_name}.pdf", bbox_inches='tight', dpi=300, format='pdf')


if __name__ == '__main__':
    get_span()


