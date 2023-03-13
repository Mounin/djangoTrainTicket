# -*- coding: utf-8 -*-
# @Time: 2023/2/21 10:35
# @Author: Lemon_Honvin
# @File: prometheus_api.py
# @Software: PyCharm

import requests
from datetime import datetime
from init_data import PROMETHEUS_HOST, PROMQL, PROMQL_LIST


def prometheus_api(start_time, end_time, service_name):
    # CPU系统态利用率
    cpu_usage_utilization = PROMQL_LIST[0] % (service_name, service_name)
    prometheus_search(start_time, end_time, 'cpu_usage_utilization', cpu_usage_utilization)
    # CPU用户态利用率
    cpu_user_utilization = PROMQL['cpu_user_utilization'] % (service_name, service_name)
    prometheus_search(start_time, end_time, 'cpu_user_utilization', cpu_user_utilization)
    # 内存带宽占用率
    memory_bandwidth_usage = PROMQL['memory_bandwidth_usage'] % (service_name, service_name)
    prometheus_search(start_time, end_time, 'memory_bandwidth_usage', memory_bandwidth_usage)
    # 内存使用量
    memory_usage = PROMQL['memory_usage'] % service_name
    prometheus_search(start_time, end_time, 'memory_usage', memory_usage)
    # 磁盘写入带宽占用率
    disk_write_bandwidth_usage = PROMQL['disk_write_bandwidth_usage'] % service_name
    prometheus_search(start_time, end_time, 'disk_write_bandwidth_usage', disk_write_bandwidth_usage)
    # 磁盘读取带宽占用率
    disk_read_bandwidth_usage = PROMQL['disk_read_bandwidth_usage'] % service_name
    prometheus_search(start_time, end_time, 'disk_read_bandwidth_usage', disk_read_bandwidth_usage)
    # 网络读带宽占用率
    network_read_bandwidth_usage = PROMQL['network_read_bandwidth_usage'] % (service_name, service_name)
    prometheus_search(start_time, end_time, 'network_read_bandwidth_usage', network_read_bandwidth_usage)
    # 网络写带宽占用率
    network_write_bandwidth_usage = PROMQL['network_write_bandwidth_usage'] % (service_name, service_name)
    prometheus_search(start_time, end_time, 'network_write_bandwidth_usage', network_write_bandwidth_usage)


def prometheus_search(start_time, end_time, metric_name, promql):
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
            print(f"\n{'#' * 50}pod_name:{pod_name}{'#' * 50}")

            # 遍历时间序列的值
            for value in values:
                timestamp = datetime.fromtimestamp(value[0])
                metric_value = value[1]
                print(f"pod名称: {pod_name}"
                      f"\t指标名称: {metric_name}"
                      f"\t指标值:{metric_value} "
                      f"\t@ {timestamp}")
    else:
        print("查询Prometheus API失败！")
