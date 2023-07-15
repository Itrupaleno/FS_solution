import os
import time
import json
import queue
import requests


token_flag = None        # Here some initial constants for programm correct work
token = None
nextRetryMs = 1000
orders_queue = queue.deque()

while True:
    if os.path.exists("state.txt"): # state.txt exists only if user complete an
        file = open("state.txt")    # authorization.

        token_flag = file.readline()[11:16]
        if token_flag == "False":
            token_flag = False
        else:
            token_flag = True
        
        token = file.readline()[12:-1] # Get his token here.
        if len(token) == 4:
            token = None
    else:
        token_flag = False
        token = None
        
    if token_flag: # If user complete authorization executes this part
        # Here we send GET request to get orders from flashpay.py for current user in asu_azs.py
        req = requests.request("GET", "http://localhost:8091/api/orders/items",
                            headers={"Authorization": token})
        if req.status_code == 200:# 200 means that server gives as some orders
            print(req.status_code, req.headers["Message"])
            orders = req.json()
            for key in orders:# Here we add orders to our queue
                orders_queue.appendleft(json.dumps(orders[key]))
                nextRetryMs = int(orders[key]["nextRetryMs"])

            if not os.path.exists("orders.txt"):
                file = open("orders.txt", "x")
                file.close()
            
            file = open("orders.txt", "r")
            sended_orders = list()
            for line in file:# We do this to not double the orders in the orders.txt
                sended_orders.append(line[:-1])
            file.close()
            
            file = open("orders.txt", "a") # Write new orders in orders.txt
            for _ in range(len(orders_queue)):
                order = orders_queue.pop()
                if order not in sended_orders:
                    file.write(order + "\n")
            else:
                file.close()
        else:# Executes if we had already accepted orders from server(it doesn't send it again)
            print(req.status_code, req.headers["Message"])
    time.sleep(nextRetryMs / 1000)
    