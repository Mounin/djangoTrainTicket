import json
import random
import string
import time
import requests
from numpy.random import randint
from init_data import USER_CREDETIALS, PHONE, BENCHMARK_HOST

def random_string_generator():
    len = randint(8, 10)
    random_string = ''.join([random.choice(string.ascii_letters) for n in range(len)])
    return random_string


class AdminActions:
    def __init__(self):
        # 管理员账号密码
        self.admin_user = "admin"
        self.admin_pwd = "222222"
        # 应用主页（IP:端口号）
        self.host = BENCHMARK_HOST
        # token（登陆后获取）
        self.bearer = self.admin_login()
        self.user_credentials = []

    # 管理员登录
    def admin_login(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json"}
        response = requests.post(url=self.host + "/api/v1/users/login",
                                 headers=head,
                                 json={
                                     "username": self.admin_user,
                                     "password": self.admin_pwd
                                 })
        return "Bearer " + response.json()["data"]["token"]

    # 获取当前用户信息
    def get_users(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.get(url=self.host + "/api/v1/adminuserservice/users",
                                headers=head,
                                )
        return response.json()["data"]

    # 删除指定用户，userid为用户id
    def delete_user(self, userid):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.delete(url=self.host + "/api/v1/adminuserservice/users/" + userid, headers=head)
        # print(response.text)

    # 删除所有用户
    def delete_all_user(self):
        users = self.get_users()
        for user in users:
            self.delete_user(user["userId"])

    # 创建用户，即注册用户，counts为创建用户的数量，用户名随机生成，密码与用户名一致。USER_CREDETIALS[i]为随机生成的用户名列表。
    def create_users(self, counts):
        for i in range(counts):
            username = USER_CREDETIALS[i]
            payload = {"userName": username, "password": username, "gender": str(random.choice([1, 2])), "email": username + "@abc.com",
                       "documentType": "1", "documentNum": random.choice(PHONE)}
            head = {"Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": self.bearer}
            response = requests.post(url=self.host + "/api/v1/adminuserservice/users",
                                     headers=head,
                                     json=payload)
            if response.json()["status"] == 1:
                self.user_credentials.append(username)
                # print(response.text)
                print("%s添加成功，剩余添加用户数量:%s" % (username, str(counts-i)))
        # print(self.user_credentials)

    # 获得所有订单信息
    def get_all_orders(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.get(url=self.host + "/api/v1/adminorderservice/adminorder",
                                headers=head,
                                )
        return response.json()["data"]

    # 删除指定订单（订单id,火车车次）
    def delete_orders(self, orderid, trainNumber):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.delete(
            url=self.host + "/api/v1/adminorderservice/adminorder/" + orderid + "/" + trainNumber,
            headers=head)
        # print(response.text)

    # 删除所有订单
    def delete_all_orders(self):
        orders = self.get_all_orders()
        for order in orders:
            self.delete_orders(order['id'], order['trainNumber'])

    # 获得托运信息
    def get_contacts(self):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.get(url=self.host + "/api/v1/contactservice/contacts",
                                headers=head,
                                )
        return response.text

    # 删除指定托运信息
    def delete_contact(self, id):
        head = {"Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self.bearer}
        response = requests.delete(
            url=self.host + "/api/v1/contactservice/contacts/" + id,
            headers=head)
        print(response.text)


def admin_api_test():
    admin_api = AdminActions()
    admin_api.delete_all_orders()


def delete_all_orders():
    admin_api = AdminActions()
    admin_api.delete_all_orders()


# 注册用户，管理员登录->创建用户
def create_users(count):
    admin_api = AdminActions()
    print("管理员登录成功，开始添加用户~")
    admin_api.create_users(count)
    print(admin_api.user_credentials)


if __name__ == '__main__':
    # 创建1000个用户
    create_users(500)

