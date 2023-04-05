import json
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core import serializers
from rest_framework.response import Response
from pyTrainTicket.models import PromSingle, PromContinue, Trace, Span
from pyTrainTicket.src.jaeger.jaeger_api import jaeger_get_traces_and_span, jaeger_draw_path
from pyTrainTicket.src.jaeger.jaeger_monitor import jaeger_get_monitor, get_resource_from_db, hot_ms
from pyTrainTicket.src.prometheus.continue_monitor import search_continue_promQL, prom_data_opera
from pyTrainTicket.src.prometheus.single_monitor import search_all_promQL
from rest_framework import viewsets, permissions
from pyTrainTicket.serializers import *


# 单点监控
class PromSingleViewSet(viewsets.ModelViewSet):
    queryset = PromSingle.objects.all()
    serializer_class = PromSingleSerializer
    #
    # def get_queryset(self, request):
    #     response = {}
    #     try:
    #         mss = PromSingle.objects.filter()
    #         response['list'] = json.loads(serializers.serialize("json", mss))
    #         response['msg'] = 'success'
    #         response['error_num'] = 0
    #     except Exception as e:
    #         response['msg'] = str(e)
    #         response['error_num'] = 1
    #
    #     return JsonResponse(response)
    #

    def single_monitor(self, request):
        response = {}
        try:
            # 清空原有的数据表
            PromContinue.objects.all().delete()

            response['res'] = search_all_promQL()
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


# 持续监控
class PromContinueViewSet(viewsets.ModelViewSet):
    queryset = PromContinue.objects.all()
    serializer_class = PromContinueSerializer

    def show_continue_mss(self, request):
        response = {}
        try:
            # 清空原有的数据表
            PromContinue.objects.all().delete()

            ms_name = request.GET.get("form[name]")
            start_time = timezone.make_aware(
                datetime.strptime(request.GET.get("form[start_end][0]"), '%Y-%m-%dT%H:%M:%S.%fZ'))
            end_time = timezone.make_aware(
                datetime.strptime(request.GET.get("form[start_end][1]"), '%Y-%m-%dT%H:%M:%S.%fZ'))
            search_continue_promQL(ms_name, start_time, end_time)
            mss = PromContinue.objects.filter()
            response['list'] = json.loads(serializers.serialize("json", mss))
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)

    def show_graph_continue_mss(self, request):
        response = {}
        try:
            res_list = prom_data_opera()
            # mss = PromContinue.objects.filter()
            # response['list'] = json.loads(serializers.serialize("json", res_list))
            response['list'] = res_list
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


# jaeger操作
class TraceViewSet(viewsets.ModelViewSet):
    queryset = Trace.objects.all()
    serializer_class = TraceSerializer

    # 获取traces
    def get_traces(self, request):
        response = {}
        try:
            traces_all = Trace.objects.all()
            traces = []
            for trace in json.loads(serializers.serialize("json", traces_all)):
                traces.append(trace['fields'])
            # for trace in traces:
            #     trace['duration'] = timedelta(microseconds=trace['duration'])
            response['traces'] = traces
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


class SpanViewSet(viewsets.ModelViewSet):
    queryset = Span.objects.all()
    serializer_class = SpanSerializer

    # 获取spans
    def get_spans(self, request):
        response = {}
        try:
            spans_all = Span.objects.all()
            spans = []
            for span in json.loads(serializers.serialize("json", spans_all)):
                spans.append(span['fields'])
            response['spans'] = spans
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


class JaegerMonitorViewSet(viewsets.ModelViewSet):
    queryset = JaegerMonitor.objects.all()
    serializer_class = JaegerMonitorSerializer

    # 绘制有向无环图
    def draw_path(self, request):
        response = {}
        try:
            trace_id = request.GET.get("traceID")
            response['graph_data'], response['critical_data'] = jaeger_draw_path(trace_id)
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            print("不成功访问！", e)
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)

    # 获取jaeger对应时间戳资源利用情况
    def get_monitor(self, request):
        response = {}
        try:
            response['monitor'] = jaeger_get_monitor()
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)

    # 从数据库中获取资源利用情况
    def get_resource(self, request):
        response = {}
        try:
            response['tracesData'] = get_resource_from_db()
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


class JaegerHotMSViewSet(viewsets.ModelViewSet):
    queryset = JaegerHotMS.objects.all()
    serializer_class = JaegerHotMSSerializer

    def get_hot_ms(self, request):
        response = {}
        try:
            hot_data = hot_ms()
            response['hot_data'] = hot_data
            response['msg'] = 'success'
            response['error_num'] = 0
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1

        return JsonResponse(response)


# Create your views here.
# 测试接口
def test(request):
    if request.method == "GET":
        return HttpResponse("GET请求...")
    else:
        return HttpResponse("POST请求...")



# jaeger操作
# 获取traces和spans
def get_traces_and_spans(request):
    response = {}
    try:
        jaeger_get_traces_and_span()
        traces = Trace.objects.filter()
        spans = Span.objects.filter()
        response['traces'] = json.loads(serializers.serialize("json", traces))
        response['spans'] = json.loads(serializers.serialize("json", spans))
        response['msg'] = 'success'
        response['error_num'] = 0
    except Exception as e:
        response['msg'] = str(e)
        response['error_num'] = 1

    return JsonResponse(response)













