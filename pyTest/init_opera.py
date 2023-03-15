# -*- coding: utf-8 -*-
# @Time: 2023/2/8 15:51
# @Author: Lemon_Honvin
# @File: init_opera.py
# @Software: PyCharm
import time

from admin_api import *
from Train_Ticket_API import *

if __name__ == '__main__':
    # admin_api
    print("测试开始")
    create_users(100)

    print("用户添加完毕！")

    arrival_rate = 200
    # 负载运行时间
    runtime = 30
    start_time = time.time()
    print("开始测试 用户启动间隔-- %s ms, 运行时间--%s s" % (arrival_rate, runtime))
    start_load_test(arrival_rate, runtime)
    print("结束测试时间 %s, 产生的span数 - %s" % (datetime.now(), total_user))
    print("总共用时: ", time.time() - start_time)
