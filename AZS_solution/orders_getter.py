import os
import time
import json
import queue
import requests


token_flag = None
token = None
nextRetryMs = 1000
orders_queue = queue.deque()

while True:
    if os.path.exists("state.txt"):
        file = open("state.txt")

        token_flag = file.readline()[11:16]
        if token_flag == "False":
            token_flag = False
        else:
            token_flag = True
        
        token = file.readline()[12:-1]
        if len(token) == 4:
            token = None
    else:
        token_flag = False
        token = None
        
    if token_flag:
        req = requests.request("GET", "http://localhost:8091/api/orders/items",
                            headers={"Authorization": token})
        if req.status_code == 200:
            print(req.status_code, req.headers["Message"])
            orders = req.json()
            for key in orders:
                orders_queue.appendleft(json.dumps(orders[key]))
                nextRetryMs = int(orders[key]["nextRetryMs"])

            if not os.path.exists("orders.txt"):
                file = open("orders.txt", "x")
                file.close()
            
            file = open("orders.txt", "r")
            sended_orders = list()
            for line in file:
                sended_orders.append(line[:-1])
            file.close()
            
            file = open("orders.txt", "a")
            for _ in range(len(orders_queue)):
                order = orders_queue.pop()
                if order not in sended_orders:
                    file.write(order + "\n")
            else:
                file.close()
        else:
            print(req.status_code, req.headers["Message"])
    time.sleep(nextRetryMs / 1000)
    