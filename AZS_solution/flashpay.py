import http.server
import json
import os
import urllib
import hashlib


test_order = {
    "nextRetryMs": 3000,
    "orders": [
        {
            "id": "ca067937c98844a3b0ee2cfc41493e30",
            "dateCreate": "2018-08-24T16:41:25.3593028Z",
            "orderType": "Money",
            "orderVolume": 500,
            "columnId": 2,
            "litre": 12.53,
            "status": "AcceptOrder",
            "fuelId": "a92",
            "priceFuel": 39.88,
            "sum": 499.7,
            "ContractId": "Individual",
            "BonusCardId": 45467879786,
            "BonusCardType": "Shell",
            "BonusCardToken": "JHB3b2yIGBKbg8723bhkBGMJhkg",
            "DiscountStation": {
                "Algoritm": "FixSumPerLitre",
                "Value": 3.0,
                "Total": {
                    "Value": 37.59,
                    "ValueVat": 6.27,
                    "ValueWithOutVat": 31.32
                },
            },
            "PriceFuelStationWithDiscount": {
                "Value": 42.19,
                "Total": {
                    "Value": 462.11,
                    "ValueVat": 77.02,
                    "ValueWithOutVat": 385.09
                },
            }
        }
    ]
}
test_order1 = {
    "nextRetryMs": 3000,
    "orders": [
        {
            "id": "ca067937c98844a3b0ee2cfc41493e30",
            "dateCreate": "2018-08-24T16:41:25.3593028Z",
            "orderType": "Money",
            "orderVolume": 400,
            "columnId": 2,
            "litre": 12.3,
            "status": "AcceptOrder",
            "fuelId": "a92",
            "priceFuel": 40.88,
            "sum": 500,
            "ContractId": "Individual",
            "BonusCardId": 45467879786,
            "BonusCardType": "Shell",
            "BonusCardToken": "JHB3b2yIGBKbg8723bhkBGMJhkg",
            "DiscountStation": {
                "Algoritm": "FixSumPerLitre",
                "Value": 3.0,
                "Total": {
                    "Value": 37.59,
                    "ValueVat": 6.27,
                    "ValueWithOutVat": 31.32
                },
            },
            "PriceFuelStationWithDiscount": {
                "Value": 42.19,
                "Total": {
                    "Value": 462.11,
                    "ValueVat": 77.02,
                    "ValueWithOutVat": 385.09
                },
            }
        }
    ]
}

orders_dict = dict() # Initialize dict of test orders here.
test_orders = list()
test_orders.append(test_order)
test_orders.append(test_order1)
for i in range(len(test_orders)):
    orders_dict[i+1] = test_orders[i]
accepted_tokens = set()

if os.path.exists("reestr.json"):  # Download current state of reestr
    f = open("reestr.json")
    reestr = json.load(f)
    f.close()
else:
    reestr = dict()

class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        global orders_dict
        if self.path == "/api/orders/items": # Block of code executes when server should
            if not (self.headers["Authorization"] in accepted_tokens):# give orders to asu_azs.
                self.send_response(200)# Just send orders if user want to get it firstly          
                self.send_header("Message", "Request for giving the orders accepted. Orders sended.")
                self.end_headers()
                self.wfile.write(bytes(json.dumps(orders_dict), "utf-8"))
                accepted_tokens.add(self.headers["Authorization"])# Save information about user (that programm has sended 
            else:                                                 # orders already for this token)
                self.send_response(404)
                self.send_header("Message", "There aren't any new orders.")
                self.end_headers()
        return


    def do_POST(self):
        if self.path == "/api/auth": # This works when user want to do an authorization.
            content_len = int(self.headers["Content-Length"])        # Accept login and password for creating a token
            content = str(self.rfile.read(content_len))              # or for giving a token from reestr.
            content = str(urllib.parse.unquote_plus(content))[2:-1]
            login = content[content.index("login")+6:content.index("&")]
            password = content[content.index("code")+5:]

            if os.path.exists("server_passwd/database.json"):        # Download current state of 
                f = open("server_passwd/database.json")              # data_base(bank of logins-passwords)
                data_base = json.load(f)
                f.close()
            else:
                data_base = dict()

            if (login in data_base) and (data_base[login] == password): # Check the correctness of login and password
                if content in reestr: # If token for this login-password already in reestr
                    token = reestr[content] # server gives it.
                else:
                    token = hashlib.sha256()              # Creating the token(executes only in situations
                    token.update(bytes(content, "utf-8")) # when it's not created)
                    token = token.hexdigest()
                    reestr[content] = token
                    if os.path.exists("reestr.json"):     # Delete the reestr.json and save an actual version.
                        os.remove("reestr.json")
                    file = open("reestr.json", "x")
                    json.dump(reestr, file, indent=4)
                    file.close()
                
                self.send_response(200)                   # Authorization completed successfully.
                self.send_header("Authorization", token)
                self.send_header("Message", "Authorization complete.")
                self.end_headers()
            elif login not in data_base:
                self.send_response(401)                   # Programm didn't find a login(user didn't get a password).
                self.send_header("Message", "Login not found or blocked")
                self.end_headers()
            elif data_base[login] != password:
                self.send_response(404)                   # Wrong password.
                self.send_header("Message", "Wrong password.")
                self.end_headers()
        elif self.path == "/api/price": # This works when user sends a price list of fuel station
            cur_headers = dict(self.headers)
            cur_token = cur_headers["Authorization"]    # getting the authorization token

            content_len = int(self.headers["Content-Length"])
            content = str(self.rfile.read(content_len))
            content = str(urllib.parse.unquote_plus(content))[2:-1]
            price_list = dict([tuple(each.split("=")) for each in content.split("&")]) # interpretated price list(which was sended
                                                                                       
            if os.path.exists("azs_state.json"): # Check is data of fuel stations exists # with http request) as dict.         
                file = open("azs_state.json")
                azs_state_dict = json.load(file) # Download data in our dict
                file.close()
                if cur_token in azs_state_dict: # Check is token already saved in azs_state.json
                    azs_state_dict[cur_token]["price-list"] = price_list # If yes programm just update the price list
                    os.remove("azs_state.json")
                    file = open("azs_state.json", "x")          # Recreating an actual azs_state.json
                    json.dump(azs_state_dict, file, indent=4)
                    file.close()
                else:
                    azs_state_dict[cur_token] = {"price-list": None, "configuration": None} # intialized data for current token
                    azs_state_dict[cur_token]["price-list"] = price_list                    # if it is not in azs_state.json
                    os.remove("azs_state.json")
                    file = open("azs_state.json", "x")         # Recreating an actual azs_state.json
                    json.dump(azs_state_dict, file, indent=4)
                    file.close()
            else:                      # If azs_state.json wasn't created programm will initialize it and create the file.
                azs_state_dict = dict()
                azs_state_dict[cur_token] = {"price-list": None, "configuration": None} 
                azs_state_dict[cur_token]["price-list"] = price_list
                file = open("azs_state.json", "x")
                json.dump(azs_state_dict, file, indent=4)
                file.close()
            
            self.send_response(200)                             # Response that price lis accepted.
            self.send_header("Message", "Price list accepted.")
            if azs_state_dict[cur_token]["configuration"] == None: # Check if configuration is None or not.
                self.send_header("Configuration", "NO")            # If it's None client side will immediatly send it here
            else:                                                  # after our response.     
                self.send_header("Configuration", "YES")
            self.end_headers()
        elif self.path == "/api/station":
            cur_token = self.headers["Authorization"]

            content_len = int(self.headers["Content-Length"])
            content = str(self.rfile.read(content_len))
            content = str(urllib.parse.unquote_plus(content))[2:-1]
            configuration = json.loads(content)

            if os.path.exists("azs_state.json"): # Check is data of fuel stations exists # with http request) as dict.         
                file = open("azs_state.json")
                azs_state_dict = json.load(file) # Download data in our dict
                file.close()
                if cur_token in azs_state_dict: # Check is token already saved in azs_state.json
                    azs_state_dict[cur_token]["configuration"] = configuration # If yes programm just update the price list
                    os.remove("azs_state.json")
                    file = open("azs_state.json", "x")          # Recreating an actual azs_state.json
                    json.dump(azs_state_dict, file, indent=4)
                    file.close()
                else:
                    azs_state_dict[cur_token] = {"price-list": None, "configuration": None} # intialized data for current token
                    azs_state_dict[cur_token]["configuration"] = configuration                    # if it is not in azs_state.json
                    os.remove("azs_state.json")
                    file = open("azs_state.json", "x")         # Recreating an actual azs_state.json
                    json.dump(azs_state_dict, file, indent=4)
                    file.close()
            else:                      # If azs_state.json wasn't created programm will initialize it and create the file.
                azs_state_dict = dict()
                azs_state_dict[cur_token] = {"price-list": None, "configuration": None} 
                azs_state_dict[cur_token]["configuration"] = configuration
                file = open("azs_state.json", "x")
                json.dump(azs_state_dict, file, indent=4)
                file.close()
            
            self.send_response(200)
            self.send_header("Message", "Configuration accepted successfully.")
            self.end_headers()
        elif self.path == "/api/orders/items":
            cur_token = self.headers["Authorization"]

            content_len = int(self.headers["Content-Length"])
            content = str(self.rfile.read(content_len))
            content = str(urllib.parse.unquote_plus(content))[2:-1]
            columns_status = json.loads(content)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes("Columns status accepted successfully.", "utf-8"))
        return


def main():
    print("Starting serving on port 8091...")

    server_address = ("127.0.0.1", 8091) # Initializing server "position"
    httpd = http.server.HTTPServer(server_address, MyHandler) # Creating HTTP server
    httpd.serve_forever()


main()