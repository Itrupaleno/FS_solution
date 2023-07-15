import http.server
import random
import json
import os
import string

if os.path.exists("database.json"): # Download a database of logins-passwords
    f = open("database.json")
    data_base = json.load(f)
    f.close()
else:
    data_base = dict()

class PassHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if "login" in self.path:
            self.user = self.path[self.path.index("login")+6:] # understand the login of the client
        if self.user in data_base:
            self.requested_inf = data_base[self.user] # if client has already called a password programm just give it form database
        else: # This code executes only if server has never gave a password for client
            self.requested_inf = str()
            for n in range(10):                                  # Algorithm of creating client's password
                if n % 4 == 0: 
                    self.requested_inf = self.requested_inf +\
                        random.choice(["!", "?", "$", "#", "&"])
                elif n % 2 == 0:
                    self.requested_inf = self.requested_inf +\
                        str(random.randint(0, 9))
                else:
                    self.requested_inf = self.requested_inf +\
                        random.choice(string.ascii_letters)
            data_base[self.user] = self.requested_inf
        self.send_response(200)                                 # Response to the client request
        self.send_header("Information", str(self.requested_inf))# Password in the header)
        self.end_headers()
        if os.path.exists("database.json"):     # Here server will create actual data_base.json
            os.remove("database.json")
        file = open("database.json", "x")
        json.dump(data_base, file, indent=4)
        file.close()
        return


def main():
    print("Starting serve on port 8080...")
    server_address = ("127.0.0.1", 8080) # Initialize the server "position"
    httpd = http.server.HTTPServer(server_address, PassHandler) # Creating the sever object
    httpd.serve_forever()


main()