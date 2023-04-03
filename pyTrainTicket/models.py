from django.db import models


# Create your models here.

class PromSingle(models.Model):
    class Meta:
        db_table = "prom_single_monitor"
    id = models.IntegerField(primary_key=True)
    ms_name = models.CharField(max_length=64)
    CPU_usage = models.CharField(max_length=64)
    memory_bandwidth_usage = models.CharField(max_length=64)
    memory_usage = models.CharField(max_length=64)
    disk_write = models.CharField(max_length=64)
    disk_read = models.CharField(max_length=64)
    net_write = models.CharField(max_length=64)
    net_read = models.CharField(max_length=64)


class PromContinue(models.Model):
    class Meta:
        db_table = "prom_continue_monitor"
    id = models.IntegerField(primary_key=True)
    ms_name = models.CharField(max_length=64)
    CPU_usage = models.CharField(max_length=64)
    memory_bandwidth_usage = models.CharField(max_length=64)
    memory_usage = models.CharField(max_length=64)
    disk_write = models.CharField(max_length=64)
    disk_read = models.CharField(max_length=64)
    net_write = models.CharField(max_length=64)
    net_read = models.CharField(max_length=64)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.CharField(max_length=64)


class Trace(models.Model):
    class Meta:
        db_table = "jaeger_trace"
    id = models.IntegerField(primary_key=True)
    # trace_id = models.CharField(primary_key=True, max_length=255, unique=True)
    trace_id = models.CharField(max_length=255)
    span_number = models.IntegerField()
    root_ms_name = models.CharField(max_length=255)
    duration = models.IntegerField()
    start_time = models.DateTimeField()


class Span(models.Model):
    class Meta:
        db_table = "jaeger_span"
    id = models.IntegerField(primary_key=True)
    # trace = models.ForeignKey(Trace, on_delete=models.CASCADE)
    span_id = models.CharField(max_length=255)
    trace_id = models.CharField(max_length=255)
    # trace_id = models.ForeignKey(Trace, on_delete=models.CASCADE)
    parent_id = models.CharField(max_length=255)
    operation_name = models.CharField(max_length=255)
    ms_name = models.CharField(max_length=255)
    duration = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class JaegerMonitor(models.Model):
    class Meta:
        db_table = "jaeger_monitor"
    id = models.IntegerField(primary_key=True)
    span_id = models.CharField(max_length=255)
    # span_id = models.ForeignKey(Span, on_delete=models.CASCADE)
    ms_name = models.CharField(max_length=255)
    CPU_usage = models.CharField(max_length=255)
    memory_bandwidth_usage = models.CharField(max_length=255)
    memory_usage = models.CharField(max_length=255)
    disk_write = models.CharField(max_length=255)
    disk_read = models.CharField(max_length=255)
    net_write = models.CharField(max_length=255)
    net_read = models.CharField(max_length=255)


class JaegerHotMS(models.Model):
    class Meta:
        db_table = "hot_ms"
    id = models.IntegerField(primary_key=True)
    ms_name = models.CharField(max_length=255)
    num = models.IntegerField()
