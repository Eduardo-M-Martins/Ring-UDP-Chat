import json
import random
import time
import threading
import binascii
from socket import *

ip_destny, nickname, delay, token, gen_token = "", "", 0, -1, False
last_message = ["", ""]
message_list = []
udp_socket = socket(AF_INET, SOCK_DGRAM)

ERRO = True

##############################################################################################################

def config():
    global ip_destny, nickname, delay, gen_token, token, message_list, udp_socket, last_message
    with open("config.json", "r") as f:
        config = json.load(f)
        f.close()
    ip_destny = str(config["ip_destny"])
    nickname = str(config["nickname"])
    delay = int(config["delay"])
    gen_token = bool(config["gen_token"])
    token = -1

def handle_token():
    global ip_destny, nickname, delay, gen_token, token, message_list, udp_socket, last_message
    send("9000")

def crc32(msg, generating):
    if ERRO and generating:
        random.seed(a=None, version=2)
        prob = random.uniform(1.0, 10.0)
        if prob <= 2:
            return -1  
    return binascii.crc32(msg.encode()) & 0xFFFFFFFF

def recive():
    global ip_destny, nickname, delay, gen_token, token, message_list, udp_socket, last_message
    
    port = 5000
    udp_socket.bind(("0.0.0.0", port))
    
    print("\n# === === === === === === Port === === === === === === #\n")
    print("  → UDP: " + str(port))
    
    while True:
        data, _ = udp_socket.recvfrom(1024)
        data = data.decode("utf-8")
        
        if data == "9000":
            token = int(data)
            if len(message_list) > 0:
                msg = message_list.pop(0)
                if msg.startswith("/priv "):
                    to_nickname = msg.split(" ")[1]
                    last_message = [to_nickname, msg]
                    msg = ' '.join(msg.split(" ")[2:])
                    msg = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(crc32(msg, True)) + ";" + msg
                    send(msg)
                else:
                    msg = "7777:naoexiste;" + nickname + ";TODOS;" + str(crc32(msg, True)) + ";" + msg
                    last_message = ["TODOS", msg]
                    send(msg)
            else:
                token = -1
                send("9000")
        
        elif data.startswith("7777:"):
            header = data.split(":")[1].split(";")[0]
            from_nickname = data.split(":")[1].split(";")[1]
            to_nickname = data.split(":")[1].split(";")[2]
            crc = data.split(":")[1].split(";")[3]
            msg = data.split(":")[1].split(";")[4]
            
            if to_nickname == "TODOS":          # Se a menssagem é para todos
                print(from_nickname + " (global): " + msg)
                if nickname != from_nickname:       # Se não foi eu que mandei a menssagem
                    send(data)
                else:                               # Se foi eu que mandei a menssagem
                    token = -1
                    send("9000")
                
            elif to_nickname == nickname  and header == "naoexiste":       # Se a menssagem é só para mim
                if crc != str(crc32(msg, False)):          # Se a menssagem chegou com erro
                    send("7777:NACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                elif nickname != from_nickname:       # Se não foi eu que mandei a menssagem
                    print(from_nickname + ": " + msg)
                    send("7777:ACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                else:                               # Se foi eu que mandei a menssagem
                    print(from_nickname + " (eu): " + msg)
                    token = -1
                    send("9000")
                    
            else:                               # Se a menssagem é para outro nó na rede
                if nickname != from_nickname:       # Se não foi eu que mandei a menssagem
                    send(data)
                else:                               # Se foi eu que mandei a menssagem
                    if header == "ACK":                 # Se o outro nó recebeu a menssagem
                        token = -1
                        send("9000")
                    elif header == "NACK":              # Se o outro nó recebeu a menssagem com erro
                        message_list = [last_message[1]] + message_list
                        print("SYSTEM: O nó '" + to_nickname + "' recebeu a menssagem com erro. (msg: " + msg + ")")
                        token = -1
                        send("9000")
                    elif header == "naoexiste":         # Se o outro nó não existe
                        print("SYSTEM: O nó '" + to_nickname + "' não existe. (msg: " + msg + ")")
                        token = -1
                        send("9000")
                        
def handle_input():
    global ip_destny, nickname, delay, gen_token, token, message_list, udp_socket, last_message
    print("\n# === === === === === === Chat === === === === === === #")
    print("   ↓   ↓   ↓   ↓   ↓   ↓        ↓   ↓   ↓   ↓   ↓   ↓\n")
    
    while True:
        new_message = input("")
        if len(message_list) < 10:
            message_list.append(new_message)
        else:
            print("SYSTEM: Message list is full. (msg: " + new_message + ")")
            
def send(msg):
    global ip_destny, nickname, delay, gen_token, token, message_list, udp_socket, last_message
    time.sleep(delay)
    udp_socket.sendto(msg.encode("utf-8"), (ip_destny.split(":")[0], int(ip_destny.split(":")[1])))

##############################################################################################################

config()

print("\n# === === === === === === Node === === === === === === #\n")
print("  → Nickname: " + nickname)
print("  → IP de destino: " + ip_destny)
print("  → Delay de menssagem: " + str(delay) + " sec")
print("  → Token generation status: " + str(gen_token))

if gen_token:
    token = 9000
    handle_token_thread = threading.Thread(target=handle_token)
    handle_token_thread.start()

time.sleep(0.25)
recive_thread = threading.Thread(target=recive)
recive_thread.start()

time.sleep(0.25)
input_thread = threading.Thread(target=handle_input)
input_thread.start()