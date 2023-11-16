import binascii
from datetime import datetime
import json
import random
from socket import *
import time
import threading

last_token_date = datetime(1900, 1, 1, 0, 0)
message_list = []
ip_destiny, last_msg, nickname = "", "", ""
delay = 0
gen_token, receive_token = False, True

SOCKET = socket(AF_INET, SOCK_DGRAM)    # Socket.
TOKEN = "9000"                          # Define the token.
TOKEN_EXCESS = 2                        # Minimum time between tokens.
TOKEN_TIMEOUT = 30                      # Maximum time between tokens.
PORT = 5000                             # Port.
PRINT = True                            # If true, token and package details will be printed.
ERRO = True                             # If true, there will be a probability of error in the crc32.

DARK_STYLE = "\033[1m\33[90m"
END_STYLE = "\033[0m\033[0m"
GLOBAL_STYLE = "\033[1m\33[96m"
HEADER_STYLE = "\033[1m\33[95m"
PRIV_STYLE = "\033[1m\033[94m"
SYSTEM_STYLE = "\033[1m\33[31m"
TEXT_STYLE = "\033[1m\33[37m"
TITLE_STYLE = "\033[1m\33[32m"
WARNING_STYLE = "\033[1m\033[93m"

##############################################################################################################
# Functions:

# This function reads the 'config.json' file to set the initial settings of the node.
def config():
    global ip_destiny, nickname, delay, gen_token
    
    with open("config.json", "r") as f:
        config = json.load(f)
        f.close()
    ip_destiny = str(config["ip_destiny"])
    nickname = str(config["nickname"])
    delay = int(config["delay"])
    gen_token = bool(config["gen_token"])

# A thread executes this function to handle the token. Only executes if 'gen_token' is 'True' in 'config.json'.
def handle_token():
    global last_token_date
    
    time.sleep(0.5)
    # Loop to monitor the token.
    while True:
        # If the token takes too long to arrive:
        if (datetime.now() - last_token_date).total_seconds() >= TOKEN_TIMEOUT:
            # If it is not the first token to be generated:
            if last_token_date != datetime(1900, 1, 1, 0, 0):
                print(SYSTEM_STYLE + "SYSTEM: Token timeout. New token generated." + END_STYLE)
            last_token_date = datetime.now()
            send(TOKEN)
        time.sleep(1)

# This function handles the conversion to crc32. It has by default a probability of inducing an error.
def crc32(msg, generating):
    if ERRO and generating:
        random.seed(a=None, version=2)
        prob = random.uniform(1.0, 10.0)
        if prob <= 2:
            return -1  
    return binascii.crc32(msg.encode()) & 0xFFFFFFFF

# A thread executes this function to handle the receipt of packages.
def receive():
    global last_token_date, message_list, last_msg, nickname, receive_token, delay
    
    SOCKET.bind(("0.0.0.0", PORT))
    
    print(HEADER_STYLE + "\n# === === === === === === Port === === === === === === #\n" + END_STYLE)
    print(TITLE_STYLE + "    UDP: " + END_STYLE + DARK_STYLE + str(PORT) + END_STYLE)
    
    # Loop to wait for packages.
    while True:
        try:
            data, _ = SOCKET.recvfrom(1024)
            data = data.decode("utf-8")
            time.sleep(delay)
        
            # If the package is a token:
            if data == TOKEN and receive_token:
                # If the token was received after the minimum time:
                if (datetime.now() - last_token_date).total_seconds() >= TOKEN_EXCESS:
                    last_token_date = datetime.now()
                    if PRINT: print(WARNING_STYLE + "Token Check: " + str(last_token_date.time()) + END_STYLE)
                    if len(message_list) > 0:
                        msg = message_list.pop(0)
                        send(msg)
                    else:
                        send(TOKEN)
                else:
                    print(SYSTEM_STYLE + "SYSTEM: Token arrived too soon. Token ignored." + END_STYLE)
            
            # If the package is a message:
            elif data.startswith("7777:"):
                if PRINT: print(WARNING_STYLE + "Package Check: " + data + END_STYLE)
                header = data.split(":")[1].split(";")[0]
                from_nickname = data.split(":")[1].split(";")[1]
                to_nickname = data.split(":")[1].split(";")[2]
                crc = data.split(":")[1].split(";")[3]
                msg = ";".join(data.split(":")[1].split(";")[4:])
                
                # If the message is for everyone:
                if to_nickname == "TODOS":         
                    print(GLOBAL_STYLE + from_nickname + " (global): " + END_STYLE + TEXT_STYLE + msg + END_STYLE)
                    # If I didn't send the message:
                    if nickname != from_nickname:       
                        send(data)
                    # If I sent the message:
                    else:                               
                        send(TOKEN)
                
                # If the message is just for me:
                elif to_nickname == nickname  and header == "naoexiste":    
                    # If the message arrived with an error:
                    if crc != str(crc32(msg, False)):          
                        send("7777:NACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # If I didn't send the message:
                    elif nickname != from_nickname:       
                        print(PRIV_STYLE + from_nickname + ": " + END_STYLE + msg)
                        send("7777:ACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # If I sent the message:
                    else:                               
                        print(PRIV_STYLE + from_nickname + ": " + END_STYLE + TEXT_STYLE + msg + END_STYLE)
                        send(TOKEN)
                
                # If the message is for another node in the network:
                else:                  
                    # If I didn't send the message:           
                    if nickname != from_nickname:       
                        send(data)
                    # If I sent the message:
                    else:             
                        # If the other node received the message:                  
                        if header == "ACK":                 
                            send(TOKEN)
                        # If the other node received the message with error:
                        elif header == "NACK":  
                            last_msg_text = ";".join(last_msg.split(";")[4:])
                            fixed_crc32 = crc32(last_msg_text, False)
                            last_msg = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(fixed_crc32) + ";" + last_msg_text
                            message_list = [last_msg] + message_list
                            print(SYSTEM_STYLE + "SYSTEM: The node '" + to_nickname + "' received the message with error. (msg: " + msg + ")" + END_STYLE)
                            send(TOKEN)
                        # If the other node doesn't exist:
                        elif header == "naoexiste":         
                            print(SYSTEM_STYLE + "SYSTEM: The node '" + to_nickname + "' doesn't exist. (msg: " + msg + ")" + END_STYLE)
                            send(TOKEN)
                            
        except ConnectionResetError:
            pass
 
# A thread executes this function to handle the input of messages in the terminal.          
def handle_input():
    global message_list, nickname, receive_token
    
    print(HEADER_STYLE + "\n# === === === === === === Chat === === === === === === #" + END_STYLE)
    print(TITLE_STYLE + "   ↓   ↓   ↓   ↓   ↓   ↓        ↓   ↓   ↓   ↓   ↓   ↓\n" + END_STYLE)
    
    # Loop to wait for input of messages.
    while True:
        user_input = input("")
        # If it is a private message:
        if user_input.startswith("/priv "):
            to_nickname = user_input.split(" ")[1]
            text = ' '.join(user_input.split(" ")[2:])
            new_message = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(crc32(text, True)) + ";" + text
        # If it is a command to block the Token:
        elif user_input == "/block":
            if receive_token: print(SYSTEM_STYLE + "SYSTEM: Token blocked." + END_STYLE)
            receive_token = False
            continue
        # If it is a command to free the Token:
        elif user_input == "/free":
            if not receive_token: print(SYSTEM_STYLE + "SYSTEM: Token free." + END_STYLE)
            receive_token = True
            continue
        # If it is a command to force a token on the network:
        elif user_input == "/add":
            print(SYSTEM_STYLE + "SYSTEM: New token forced." + END_STYLE)
            send(TOKEN)
            continue
        # If it is a global message:
        else:
            new_message = "7777:naoexiste;" + nickname + ";TODOS;" + str(crc32(user_input, False)) + ";" + user_input
        
        # If there is space in the message list:
        if len(message_list) < 10:
            message_list.append(new_message)
        # If there is no space in the message list:
        else:
            print(SYSTEM_STYLE + "SYSTEM: Message list is full. (msg: " + user_input + ")" + END_STYLE)

# This function is used to send a message to the node referenced in 'config.json'.
def send(msg):
    global ip_destiny, last_msg
    last_msg = msg
    SOCKET.sendto(msg.encode("utf-8"), (ip_destiny.split(":")[0], int(ip_destiny.split(":")[1])))

##############################################################################################################
# Main:

config()

print(HEADER_STYLE + "\n# === === === === === === Node === === === === === === #\n" + END_STYLE)
print(TITLE_STYLE + "    Nickname: " + END_STYLE + DARK_STYLE + nickname + END_STYLE)
print(TITLE_STYLE + "    IP destiny: " + END_STYLE + DARK_STYLE + ip_destiny + END_STYLE)
print(TITLE_STYLE + "    Message delay: " + END_STYLE + DARK_STYLE + str(delay) + " sec" + END_STYLE)
print(TITLE_STYLE + "    Token generation status: " + END_STYLE + DARK_STYLE + str(gen_token) + END_STYLE)

if gen_token:
    handle_token_thread = threading.Thread(target=handle_token)
    handle_token_thread.start()

time.sleep(0.25)
recive_thread = threading.Thread(target=receive)
recive_thread.start()

time.sleep(0.5)
input_thread = threading.Thread(target=handle_input)
input_thread.start()