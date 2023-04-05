# -*- coding: utf-8 -*-
# @Time: 2023/4/4 17:15
# @Author: Honvin
# @File: serializers.py
# @Software: PyCharm
from pyTrainTicket.models import *
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class PromSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromSingle
        fields = "__all__"


class PromContinueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromContinue
        fields = "__all__"


class TraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trace
        fields = "__all__"


class SpanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Span
        fields = "__all__"


class JaegerMonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = JaegerMonitor
        fields = "__all__"


class JaegerHotMSSerializer(serializers.ModelSerializer):
    class Meta:
        model = JaegerHotMS
        fields = "__all__"
