import os
import queue
import json
import urllib
import requests
import pytimedinput


flag = True # it's for mainloop working
auth_flag = False # just an authorization flag
auth_token = None # here will be token of a fuel station after authorization
state = 0 # The main regulator of programm behaviour

if os.path.exists("state.txt"):# Initialize state.txt here(it needs for orders_getter.py)
    os.remove("state.txt")
state_txt = open("state.txt", "x")
state_txt.write(f"auth_flag: {auth_flag}\n")
state_txt.write(f"auth_token: {auth_token}\n")
state_txt.close()

instruction_link = "https://___________"     # Some constants here.
base_flashpay_link = "http://localhost:8091"
passwd_server_link = "http://localhost:8080/api/auth?login={login}"
flashpay_auth_link = base_flashpay_link + "/api/auth"
flashpay_price_link = base_flashpay_link + "/api/price"
flashpay_config_link = base_flashpay_link + "/api/station"
flashpay_orders_link = base_flashpay_link + "/api/orders/items"

columns_status = {
    "Columns": {
        1: {
            "status": "Free",
        },
        2: {
            "status": "Unavailable",
            "errorMessage": "Column is not availible now.",
        },
        3: {
            "status": "Fueling",
            "litre": 5.67,
            "fuelId": "a92",
            "basePriceFuel": 45.23,
            "sum": 256.45
        },
        4: {
            "status": "Completed",
            "extendedId": "1237hJhuy23ehnkJ003",
            "litre": 34.45,
            "fuelId": "a95",
            "basePriceFuel": 49.12,
            "sum": 1692.18
        }
    }
}

test_config = {
    "StationExtendedId": "00001",
    "Columns": {
        1: {
            "Fuels": [
                "a92",
                "a95",
                "diesel_premium"
            ]
        },
        2: {
            "Fuels": [
                "a92",
                "a95_premium",
                "a98_premium",
                "diesel_premium"
            ]
        }
    }
}
test_plist = {
    "a92": 41.22,
    "a95": 43.87,
    "a95_premium": 55.78
}

base_message = \
"""
How to work with this system:
-- If you want to do an authorization just write this
   command: "authorization"

-- If you want to send a price list of fuel station you should
   write this command: "send price list"

-- If you want to send a configuration of fuel station you should
   write this command: "send configuration"

-- If you want to stop the programm you should write this command:
   "stop"

P.S. input updates every 3 seconds.
"""
cur_orders_queue = queue.deque() # Here will be orders from flashpay,
                                 # sended by orders_getter.py

while flag:
    if state == 0: # state 0 is used when user should give
        print(base_message) # commands for programm
        command = pytimedinput.timedInput("Write your command: ", timeout=3)[0]
        if command == "authorization":
            state = 1
            continue
        elif command == "send price list":
            state = 2
            continue
        elif command == "send configuration":
            state = 3
            continue
        elif command == "stop":  # Delete some not needed data here.(state and orders)
            if os.path.exists("state.txt") and os.path.exists("orders.txt"):
                os.remove("state.txt")
                os.remove("orders.txt")
            elif os.path.exists("orders.txt"):
                os.remove("orders.txt")
            elif os.path.exists("state.txt"):
                os.remove("state.txt")
            flag = False
            print("Stop process finished.")
            continue
        else:
            if os.path.exists("orders.txt"): # Here we check is orders.txt already exists
                file = open("orders.txt", "r")# If it is so we get orders in our programm
                lines = file.readlines()
                lines = list(map(lambda x: x[:-1], lines))
                for order in lines:
                    if order not in cur_orders_queue:
                        cur_orders_queue.appendleft(order)
                if len(cur_orders_queue) != 0: # Here we change our state to 4,
                    state = 4                 # to start orders executing process
                    continue
    elif state == 1: # state 1 --> authorization state all actions for completed authorization
        if auth_flag: # Check has user already been authorized or not.
            print("You has already completed an authorization.")
            answer = input("Do you want to change the user?[y/n]: ")
            if answer == "y" or answer == "Y":
                auth_flag = False # Here we became not authorized
                auth_token = None # because of the user decision
                continue
            else:
                state = 0
                continue
        instruction = input("Do you want do read an instruction?[y/n]: ")
        if instruction == "y" or instruction == "Y":
            print("Follow this link:", instruction_link)
        else:
            print("Ok, then let's start.")
        
        have_pass = input("Have you got a password[y/n]: ")
        if have_pass == "y" or have_pass == "Y":
            print("Ok, then continue.")
        else:
            u_login = input("Write your login to get a password: ")    # Here programm ask user's login
            req = requests.get(str(passwd_server_link).format(login=u_login))# to make an HTTP request to
            if req.status_code == 200:                                       # the password server and generate
                print("All is ok, your password:", req.headers["Information"]) # password for him.
        
        print("Starting the authorization process...")
        login = input("Write your login: ")
        password = input("Write your password: ")
        req = requests.post(flashpay_auth_link, {"login": login, "code": password})# HTTP request to the flashpay 
        print(req.status_code, req.headers["Message"])                             # server to complete authorization
        if req.status_code == 401:                                                 # and get the token
            print("Return to start of authorization. At first get a new password.")
            continue
        elif req.status_code == 404:
            print("Try again.")
            continue
        else:
            print("Authorization was successfully completed.")
            auth_flag = True
            auth_token = req.headers["Authorization"]
            os.remove("state.txt")            # Change state.txt. After that orders_getter
            state_txt = open("state.txt", "x")# will start asking flashpay about orders
            state_txt.write(f"auth_flag: {auth_flag}\n")
            state_txt.write(f"auth_token: {auth_token}\n")
            state_txt.close()
            if os.path.exists("orders.txt"): # If we was changing the user we delete his
                os.remove("orders.txt")      # orders here.
            state = 2
            continue
    elif state == 2:     # state 2 is for sending a price list of current fuel station
        if not auth_flag:
            print("You should complete authorization firstly.")
            state = 0
            continue
        else:
            print("Start sending a price list...")
            req = requests.request(method="POST", url=flashpay_price_link, data=test_plist, headers={"Authorization": auth_token})
            print(req.status_code, req.headers["Message"]) # HTTP request to the flashpay server to send there our price list
            if req.status_code == 200 and req.headers["Configuration"] == "NO":
                print("Price list sended successfully.")                       # This block of code executes when price list
                state = 3                                                      # is on flashpay server, but configuration is not.                       
                continue
            elif req.status_code == 200 and req.headers["Configuration"] == "YES":
                print("Price list sended successfully.")
                state = 0
                continue
            else:
                print("Error during sending a price list.")
                state = 0
                continue
    elif state == 3: # state 3 is for sending current fuel station configuration to the flashpay server
        if not auth_flag:
            print("You should complete authorization firstly.")
            state = 0
            continue
        else:
            print("Start sending a configuration...")
            req = requests.request("POST", flashpay_config_link, json=test_config, headers={"Authorization": auth_token})
            print(req.status_code, req.headers["Message"])
            print("Configuration sended successfully.")
            state = 0
            continue
    elif state == 4: # This code executes when programm get orders.
        print("New orders accepted. Starting filling process.")
        req = requests.request("POST", flashpay_orders_link, json=columns_status, headers={"Authorization": auth_token})
        if req.status_code == 200:
            print("[200]", req.text)
        else:
            print("Error: columns status wasn't sended successfully.")
        state = 0
        continue


        

