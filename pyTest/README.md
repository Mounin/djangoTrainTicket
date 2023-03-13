# Train_ticket

## Prometheus监控资源类指标

| **指标类** | **具体指标**                    |
| ---------- | ------------------------------- |
| CPU        | CPU利用率，系统态、用户态利用率 |
| 内存       | 带宽占用率、内存使用量          |
| 磁盘       | 带宽占用率                      |
| 网络       | 读、写带宽占用率                |

### CPU

#### CPU系统态利用率

```bash
sum(rate(container_cpu_usage_seconds_total{pod=~"ts.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"ts.*"}/100000) by (pod, namespace, job, instance)) * 100
```

> 该查询中，使用`sum(rate(container_cpu_usage_seconds_total{pod=~"ts-.*"}[1m])) by (pod)`获取每个容器的总CPU使用时间，再除以`sum(rate(container_cpu_usage_seconds_total{container=~"ts-.*"}[1m])) by (pod, mode="system")`获取每个容器的CPU系统态使用时间，最终乘以100得到CPU系统态利用率。

#### CPU用户态利用率

```bash
sum(rate(container_cpu_user_seconds_total{pod=~"ts.*"}[1m])) by (pod, namespace, job, instance) / (sum(container_spec_cpu_quota{pod=~"ts.*"}/100000) by (pod, namespace, job, instance)) * 100
```

> 上述查询语句中，`container_cpu_user_seconds_total`表示容器用户态CPU使用时间。

### 内存

#### 带宽占用率

```bash
sum(rate(container_memory_working_set_bytes{container!="POD",pod=~"ts-.*"}[5m])) by (pod, container, namespace) / sum(container_spec_memory_limit_bytes{container!="POD",pod=~"ts-.*"}) by (pod, container, namespace)
```

> 解释：该查询首先使用 `rate()` 函数计算在过去 5 分钟内每秒内内存工作集的变化率，然后对每个命名空间、Pod 和容器的内存带宽占用率进行求和。这里 `container_name!="POD"` 用于过滤掉 `POD` 容器，因为它们通常是不需要监控的。

#### 内存使用量

```bash
sum(container_memory_working_set_bytes{container!="POD",pod=~"ts-.*"}) by (namespace, pod, container)
```

解释：该查询对每个命名空间、Pod 和容器的内存使用量进行求和。同样，`container_name!="POD"` 用于过滤掉 `POD` 容器。

### 磁盘

#### 带宽占用率

* 磁盘写入带宽占用率

  ```bash
  sum(rate(container_fs_writes_bytes_total{pod=~"ts-.*"}[5m])) by (pod)
  ```

  > 1. 对于每个匹配到的Pod，计算最近5分钟内`container_fs_writes_bytes_total`指标的速率，并对结果按照Pod名称进行分组
  > 2. 返回每个Pod的磁盘写入带宽占用率

* 磁盘读取带宽占用率

  ```bash
  sum(rate(container_fs_reads_bytes_total{pod=~"ts-.*"}[5m])) by (pod)
  ```

* 同时查询磁盘读写带宽占用率

  ```bash
  sum(rate(container_fs_reads_bytes_total{pod=~"ts-.*"}[5m])) by (pod) + sum(rate(container_fs_writes_bytes_total{pod=~"ts-.*"}[5m])) by (pod)
  ```

  > 这个查询语句将每个匹配到的Pod的磁盘读取带宽占用率和磁盘写入带宽占用率相加，得到总的磁盘带宽占用率。

### 网络

#### 读带宽占用率

```bash
sum by (pod) (irate(container_network_receive_bytes_total{pod=~"ts-.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"ts-.*"}) * 8
```

> `container_network_receive_bytes_total`: 表示容器网络接收的总字节数

#### 写带宽占用率

```bash
sum by (pod) (irate(container_network_transmit_bytes_total{pod=~"ts-.*"}[5m])) / count by (pod) (kube_pod_container_info{pod=~"ts-.*"}) * 8
```

> `container_network_transmit_bytes_total`: 表示容器网络发送的总字节数

我们使用了 pod="微服务名称-.*" 的标签选择器来选择以指定名称开头的 Pod，使用了 count by (pod) (kube_pod_container_info{pod="微服务名称-.*"}) 来计算每个 Pod 中的容器数量，然后将容器数量乘以 8 转换为比特数，最终得到带宽占用率。