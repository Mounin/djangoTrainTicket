import json
import sys
import threading
import time
import random
from datetime import datetime

import requests
from init_data import *

total_user = 0
user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) Gecko/20100101 Firefox/61.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
]


class User:
    def __init__(self, uuid):
        # 从已经注册好的用户列表中，选取用户
        self.seat_type = None
        self.price = None
        self.trip_id = None
        self.username = USER_CREDETIALS[(int(uuid) % 1000)]
        self.password = self.username
        # 登陆后获取的token
        self.bearer = ""
        # 用户id
        self.user_id = ""
        # 应用入口（ip：端口号）
        self.host = BENCHMARK_HOST
        # 信用卡id
        self.contactid = ""
        # 订单id
        self.orderid = ""
        # 支付订单id
        self.paid_orderid = ""
        # 查询，预定火车票信息的日期，一定要晚于当前时间
        self.departure_date = "2023-2-" + str(random.randint(1, 30))
        # 查询火车票的起始站点
        self.start_station = ""
        # 查询火车票的终止站点
        self.terminal_station = ""
        # 查询火车票的详细查询信息（"from": "shanghai", "to": "suzhou", "trip_id": "D1345", "seat_type": "2", "seat_price": "50.0"）
        self.search_trip = random.choice(TRIP_DATA)

    # 登录，为了获取token，因为一些请求设置了拦截器，只有登陆后（请求数据中带有token）才可以发出。
    def login(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json"}
        response = requests.post(url=self.host + "/api/v1/users/login",
                                 headers=head,
                                 json={
                                     "username": self.username,
                                     "password": self.password})
        try:
            # print(response.text)
            # json.loads(response.text)
            response_as_json = response.json()["data"]
            if response_as_json is not None:
                token = response_as_json["token"]
                self.bearer = "Bearer " + token
                self.user_id = response_as_json["userId"]
        except json.JSONDecodeError:
            pass

    # 查询高铁车票，输入数据在请求体中，获得响应数据为车次信息,如G1234，起终站点信息，如shanghai,nanjing
    def search_GD_ticket(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                'User-Agent': random.choice(user_agent_list)}
        body_start = {
            "startingPlace": self.start_station,
            "endPlace": self.terminal_station,
            "departureTime": self.departure_date
        }
        response = requests.post(
            url=self.host + "/api/v1/travelservice/trips/left",
            headers=head,
            json=body_start)
        if response.json()["data"] is not None:
            for res in response.json()["data"]:
                self.trip_id = res["tripId"]["type"] + res["tripId"]["number"]
                self.start_station = res["startingStation"]
                self.terminal_station = res["terminalStation"]
        # print(self.trip_id, self.start_station, self.terminal_station)

    # 搜索普通火车车次信息
    def search_PT_ticket(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body_start = {
            "startingPlace": self.start_station,
            "endPlace": self.terminal_station,
            "departureTime": self.departure_date
        }
        response = requests.post(
            url=self.host + "/api/v1/travel2service/trips/left",
            headers=head,
            json=body_start)
        if response.json()["data"] is not None:
            res = random.choice(response.json()["data"])
            self.trip_id = res["tripId"]["type"] + res["tripId"]["number"]
            self.start_station = res["startingStation"]
            self.terminal_station = res["terminalStation"]
            self.price = res["priceForConfortClass"]
            self.seat_type = 2
            # return res["tripId"]["type"] + res["tripId"]["number"], res["priceForConfortClass"], res["priceForEconomyClass"]
            # print(self.trip_id, self.start_station, self.terminal_station)

    # 查询要预定火车车次的订餐信息
    def get_foods(self):
        start_station = str(self.start_station).replace(" ", "").lower()
        terminal_station = str(self.terminal_station).replace(" ", "").lower()
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response = requests.get(
            url=self.host + "/api/v1/foodservice/foods/" + self.departure_date + "/" + start_station + "/" + terminal_station + "/" + self.trip_id,
            headers=head)
        resp_data = response.json()
        # print(self.host + "/api/v1/foodservice/foods/" + self.departure_date + "/" + start_station + "/" + terminal_station + "/" + self.trip_id)
        if resp_data["data"]:
            if random.uniform(0, 1) <= 0.5:
                self.food_detail = {"foodType": 2,
                                    "foodName": resp_data["data"]["trainFoodList"][0]["foodList"][0]["foodName"],
                                    "foodPrice": resp_data["data"]["trainFoodList"][0]["foodList"][0]["price"]}
            else:
                self.food_detail = {"foodType": 1,
                                    "foodName":
                                        resp_data["data"]["foodStoreListMap"][start_station][0]["foodList"][
                                            0]["foodName"],
                                    "foodPrice":
                                        resp_data["data"]["foodStoreListMap"][start_station][0]["foodList"][
                                            0]["price"]}
        # print(self.food_detail)
        # print(json.dumps(response.json()))

    # 获取车次信息
    def start_booking(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        # url = self.host + "/client_ticket_book.html?tripId=" + self.search_trip['trip_id'] + "&from=" + self.search_trip['from'] + "&to=" + self.search_trip['to'] + "&seatType=" + self.search_trip['seat_type'] + "&seat_price=" + self.search_trip[
        #     'seat_price'] + "&date=" + departure_date
        response = requests.get(
            url=self.host + "/client_ticket_book.html?tripId=" + str(self.search_trip['trip_id']) + "&from=" +
                str(self.search_trip['from']) + "&to=" + str(self.search_trip['to']) + "&seatType=" +
                str(self.search_trip['seat_type']) + "&seat_price=" + str(self.search_trip[
                                                                              'seat_price']) + "&date=" + str(
                self.departure_date),
            headers=head)
        # print(response)

    # 查看身份信息（ID card ，phone等）
    def select_contact(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response_contacts = requests.get(
            url=self.host + "/api/v1/contactservice/contacts/account/" + self.user_id,
            headers=head)
        # print(self.user_id)
        # print(response_contacts.json())
        response_as_json_contacts = response_contacts.json()["data"]
        # print(json.dumps(response_as_json_contacts))
        if len(response_as_json_contacts) == 0:
            response_contacts = requests.post(
                url=self.host + "/api/v1/contactservice/contacts",
                headers=head,
                json={
                    "name": self.user_id, "accountId": self.user_id, "documentType": "1",
                    "documentNumber": self.user_id, "phoneNumber": "123456"})

            response_as_json_contacts = response_contacts.json()["data"]
            # print(response_as_json_contacts)
            self.contactid = response_as_json_contacts["id"]
        else:
            self.contactid = response_as_json_contacts[0]["id"]
        # print(self.contactid)

    # 车票座位类型服务
    def seat_service(self):
        departure_date = self.departure_date
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        seat_select = {
            "date": departure_date,
            "from": self.start_station,
            "to": self.terminal_station
        }
        response = requests.post(
            url=self.host + "/api/v1/seatservice/seats",
            headers=head,
            json=seat_select)
        # print(response.text)
        # print(response.status_code)

    # 订票+订餐
    def finish_booking_food(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        body_for_reservation = {
            "accountId": self.user_id,
            "contactsId": self.contactid,
            "tripId": self.trip_id,
            "seatType": "2",
            "date": self.departure_date,
            "from": self.start_station,
            "to": self.terminal_station,
            "assurance": "0",
            "foodType": self.food_detail['foodType'],
            "foodName": self.food_detail['foodName'],
            "foodPrice": self.food_detail['foodPrice'],
            "stationName": "",
            "storeName": ""
        }
        response = requests.post(
            url=self.host + "/api/v1/preserveservice/preserve",
            headers=head,
            json=body_for_reservation)
        # print(response.text)
        # print(response.status_code)

    # 只订票，不订餐
    def finish_booking_GD(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        body_for_reservation = {
            "accountId": self.user_id,
            "contactsId": self.contactid,
            "tripId": self.trip_id,
            "seatType": "2",
            "date": self.departure_date,
            "from": self.start_station,
            "to": self.terminal_station,
            "foodType": "",
            "foodName": "",
            "foodPrice": "",
            "assurance": "0",
            "stationName": "",
            "storeName": ""
        }
        response = requests.post(
            url=self.host + "/api/v1/preserveservice/preserve",
            headers=head,
            json=body_for_reservation)
        # print(response.text)
        # print(response.status_code)

    # 普通火车预定（普通火车票无法订餐）
    def finish_booking_PT(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        body_for_reservation = {
            "accountId": self.user_id,
            "contactsId": self.contactid,
            "tripId": self.trip_id,
            "seatType": "2",
            "date": self.departure_date,
            "from": self.start_station,
            "to": self.terminal_station,
            "foodType": "",
            "foodName": "",
            "foodPrice": "",
            "assurance": "0",
            "stationName": "",
            "storeName": ""
        }
        response = requests.post(
            url=self.host + "/api/v1/preserveotherservice/preserveOther",
            headers=head,
            json=body_for_reservation)
        # print(response.text)
        # print(response.status_code)

    # 改签车票
    def rebook(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        if self.seat_type == 3:
            self.seat_type = 2
        else:
            self.seat_type = 2
        body_for_reservation = {
            "loginId": self.user_id,
            "orderId": self.paid_orderid,
            "oldTripId": self.trip_id,
            "tripId": self.trip_id,
            "seatType": self.seat_type,
            "data": self.departure_date
        }
        response = requests.post(
            url=self.host + "/api/v1/rebookservice/rebook",
            headers=head,
            json=body_for_reservation)
        # print(response.text)

    # 选择普通火车订单
    def select_order_PT(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response_order_refresh = requests.post(
            url=self.host + "/api/v1/orderOtherService/orderOther/refresh",
            headers=head,
            json={
                "loginId": self.user_id, "enableStateQuery": "false", "enableTravelDateQuery": "false",
                "enableBoughtDateQuery": "false", "travelDateStart": "null", "travelDateEnd": "null",
                "boughtDateStart": "null", "boughtDateEnd": "null"})
        # status:
        response_as_json = response_order_refresh.json()["data"]
        # for order in response_as_json:
        #     print(order)
        # print(json.dumps(response_order_refresh.json()))
        for orders in response_as_json:
            if orders["status"] == 1:
                self.paid_orderid = orders["id"]
                self.seat_type = orders['seatClass']
                break
        for orders in response_as_json:
            if orders["status"] == 0:
                self.orderid = orders["id"]
                self.price = orders["price"]

    # 搜索高铁动车订单
    def select_order_GD(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        response_order_refresh = requests.post(
            url=self.host + "/api/v1/orderservice/order/refresh",
            headers=head,
            json={
                "loginId": self.user_id, "enableStateQuery": "false", "enableTravelDateQuery": "false",
                "enableBoughtDateQuery": "false", "travelDateStart": "null", "travelDateEnd": "null",
                "boughtDateStart": "null", "boughtDateEnd": "null"})
        # status:
        response_as_json = response_order_refresh.json()["data"]
        # for order in response_as_json:
        #     print(order)
        # print(json.dumps(response_order_refresh.json()))
        for orders in response_as_json:
            if orders["status"] == 1:
                self.paid_orderid = orders["id"]
                self.seat_type = orders['seatClass']
                break
        for orders in response_as_json:
            if orders["status"] == 0:
                self.orderid = orders["id"]
                self.price = orders["price"]

    # print("已支付的订单号：%s" % self.paid_orderid)
    # print("未支付的订单号：%s" % self.orderid)

    # 对已购买的车票进行托运服务
    def consign(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        date = {"orderId": self.orderid, "accountId": self.contactid, "consignee": random.choice(CONSIGNEE),
                "phone": random.choice(PHONE), "weight": random.randint(5, 10)}
        response = requests.put(url=self.host + "/api/v1/consignservice/consigns", headers=head, json=date)
        # print(response.text)

    # 支付未支付订单 车票状态===>paid&not collected
    def pay(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        # print(self.user_id, self.orderid, self.trip_id, self.price)
        response = requests.post(
            url=self.host + "/api/v1/inside_pay_service/inside_payment",
            headers=head,
            json={"userId": self.user_id, "orderId": self.orderid, "tripId": self.trip_id, "price": self.price}
        )
        # print(response.text)

    # 退票
    def cancel(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        cancel = requests.get(
            url=self.host + "/api/v1/cancelservice/cancel/" + self.orderid + "/" + self.contactid,
            headers=head)
        # print(cancel.text)

    # 已支付订单取票 车票状态===>collected
    def collect_ticket(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        collect_ticket = requests.get(
            url=self.host + "/api/v1/executeservice/execute/collected/" + self.paid_orderid,
            headers=head)
        # print(collect_ticket.text)

    # 进站 车票状态===>used
    def enter_station(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json", "Authorization": self.bearer}
        enter_station = requests.get(
            url=self.host + "/api/v1/executeservice/execute/execute/" + self.paid_orderid,
            headers=head)
        # print(enter_station.text)

    # 进入高级搜索页面
    def advanced_search(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json"}
        body_start = {
            "startingPlace": self.start_station,
            "endPlace": self.terminal_station,
            "departureTime": self.departure_date
        }
        response = requests.post(
            url=self.host + "/api/v1/travelplanservice/travelPlan/minStation",
            headers=head,
            json=body_start
        )
        # print(response.text)

    # 执行任务列表，根据方法名定位方法，并执行
    def perform_task(self, name):
        task = getattr(self, name)
        task()


# 用户任务执行方法
def user_tasks(uuid):
    # 登录->选票->订餐->确定->支付->取票->进站
    global total_user
    total_user += 1
    G_user_task = ['login', 'search_GD_ticket', 'get_foods', 'select_contact', 'finish_booking_food', 'select_order_GD',
                   'consign', 'pay', 'select_order_GD', 'collect_ticket', 'enter_station', 'advanced_search']
    # 登录->选票->确定->查询订单->托运->退票
    G_user_task_consign = ['login', 'search_GD_ticket', 'select_contact', 'finish_booking_GD', 'select_order_GD',
                           'consign', 'cancel', 'advanced_search']

    # 登录->选票->确定->支付->查看支付订单->改签
    G_user_task_rebook = ['login', 'search_GD_ticket', 'select_contact', 'finish_booking_GD', 'select_order_GD', 'pay',
                          'select_order_GD', 'rebook', 'cancel']

    ZKT_user_task = ['login', 'search_PT_ticket', 'select_contact', 'finish_booking_PT', 'select_order_PT', 'consign',
                     'pay', 'select_order_PT', 'collect_ticket', 'enter_station']
    ZKT_user_task_consign = ['login', 'search_PT_ticket', 'select_contact', 'finish_booking_PT', 'select_order_PT',
                             'consign', 'cancel', 'advanced_search']
    ZKT_user_task_rebook = ['login', 'search_PT_ticket', 'select_contact', 'finish_booking_PT', 'select_order_PT',
                            'pay', 'select_order_PT', 'rebook', 'cancel']

    G_tourist_task = ['login', 'start_booking', 'search_GD_ticket', 'advanced_search']
    P_tourist_task = ['login', 'start_booking', 'search_PT_ticket', 'advanced_search']
    tasks = random.choice([G_user_task, G_user_task_consign, G_user_task_rebook, ZKT_user_task, ZKT_user_task_consign, G_tourist_task, ZKT_user_task_rebook, P_tourist_task])
    # choice = random.random()
    # if 0 <= choice < 0.4:
    #     tasks = random.choice([G_user_task, G_user_task_consign, G_user_task_rebook])
    # elif 0.4 <= choice < 0.8:
    #     tasks = random.choice([ZKT_user_task, ZKT_user_task_consign, ZKT_user_task_rebook])
    # else:
    #     tasks = random.choice([G_tourist_task, P_tourist_task])
    # tasks = random.choice([G_tourist_task, P_tourist_task])
    API_TASK = ['get_foods', 'get_foods']
    tasks = G_user_task_consign
    # tasks = random.choices([G_user_task, G_user_task_rebook, ZKT_user_task, ZKT_user_task_rebook],
    #                        weights=[0.3, 0.3, 0.2, 0.2])[0]
    # tasks = API_TASK
    # tasks = ['login']
    user = User(uuid)
    # tasks = API_TASK
    # user.start_station = "Shang Hai"
    # user.terminal_station = "Nan Jing"
    # user.trip_id = "Z1234"
    # print(uuid)
    if (tasks == G_user_task) or (tasks == G_user_task_consign) or (tasks == G_user_task_rebook) or (
            tasks == G_tourist_task) or (tasks == API_TASK):
        # stations = random.choice(G_TRAVEL_STATION)
        stations = ["Nan Jing", "Shang Hai"]
        user.start_station = stations[0]
        user.terminal_station = stations[1]
        user.trip_id = "G1234"
    elif (tasks == ZKT_user_task) or (tasks == ZKT_user_task_consign) or (tasks == ZKT_user_task_rebook) or (
            tasks == P_tourist_task):
        stations = random.choice(ZKT_TRAVEL_STATION)
        user.start_station = stations[0]
        user.terminal_station = stations[1]
    print(uuid, "*" * 50, tasks)
    for task in tasks:
        # print(task)
        user.perform_task(task)
        time.sleep(1)


# 开始执行，以多线程方式启动不同的用户去执行任务列表，可以控制用户启动时间间隔，负载运行时间。
def start_load_test(lambd, runtime):
    end_time = time.time() + runtime
    while time.time() < end_time:
        thread = threading.Thread(target=user_tasks, args=(str(total_user),))
        thread.start()
        # print("生成用户"+str(total_user))
        next_arrival = random.expovariate(1 / lambd)
        time.sleep(next_arrival / 1000.0)


if __name__ == '__main__':
    # 用户启动间隔
    # arrival_rate = int(sys.argv[1])
    arrival_rate = 500
    # 负载运行时间
    # runtime = int(sys.argv[2])
    runtime = 1
    start_time = time.time()
    print("开始测试 用户启动间隔-- %s ms, 运行时间--%s s" % (arrival_rate, runtime))
    start_load_test(arrival_rate, runtime)
    print("结束测试时间 %s, 产生的span数 - %s" % (datetime.now(), total_user))
    print("总共用时: ", time.time() - start_time)
    # user_tasks(0)
