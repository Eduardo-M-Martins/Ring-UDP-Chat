##############################################################################################################

# Eduardo Martins, Bernardo Fiorini e Nathan Mello 

##############################################################################################################
# Imports, variáveis e constantes globais:

import binascii
from datetime import datetime
import json
import random
from socket import *
import time
import threading

last_token_date = datetime(1900, 1, 1, 0, 0)
message_list = []
ip_destny, last_msg, nickname = "", "", ""
delay, token = 0, -1
gen_token = False

SOCKET = socket(AF_INET, SOCK_DGRAM)
TOKEN = "9000"
TOKEN_EXCESS = 2
TOKEN_TIMEOUT = 15
PORT = 5000
ERRO = True

##############################################################################################################
# Funções:

# Essa função lê o arquivo 'config.json' para setar as configurações iniciais do nodo.
def config():
    global ip_destny, nickname, delay, token, gen_token
    
    with open("config.json", "r") as f:
        config = json.load(f)
        f.close()
    ip_destny = str(config["ip_destny"])
    nickname = str(config["nickname"])
    delay = int(config["delay"])
    gen_token = bool(config["gen_token"])
    token = -1

# Uma thread executa essa função para lidar com o token. Só executa se 'gen_token' estiver em 'True' no 'config.json'.
def handle_token():
    global last_token_date
    
    # Loop para monitorar o token.
    while True:
        # Se o token demorar mutio para chegar:
        if (datetime.now() - last_token_date).total_seconds() >= TOKEN_TIMEOUT:
            # Se não é o primeiro a ser gerado token:
            if last_token_date != datetime(1900, 1, 1, 0, 0):
                print("SYSTEM: Token timeout. New token generated.")
            last_token_date = datetime.now()
            send(TOKEN)
        time.sleep(TOKEN_TIMEOUT/2)

# Essa função lida com a conversão para crc32. Possui por padrão uma probabilidade de induzir um erro.
def crc32(msg, generating):
    if ERRO and generating:
        random.seed(a=None, version=2)
        prob = random.uniform(1.0, 10.0)
        if prob <= 2:
            return -1  
    return binascii.crc32(msg.encode()) & 0xFFFFFFFF

# Uma thread executa essa função para lidar com o recebimento de pacotes.
def recive():
    global last_token_date, message_list, last_msg, nickname, token
    
    SOCKET.bind(("0.0.0.0", PORT))
    
    print("\n# === === === === === === Port === === === === === === #\n")
    print("  → UDP: " + str(PORT))
    
    # Loop para ficar esperando por pacotes.
    while True:
        try:
            data, _ = SOCKET.recvfrom(1024)
            data = data.decode("utf-8")
        
            # Se o pacote for um token:
            if data == TOKEN:
                last_token_date = datetime.now()
                token = TOKEN
                if len(message_list) > 0:
                    msg = message_list.pop(0)
                    send(msg)
                else:
                    token = -1
                    send(TOKEN)
            
            # Se o pacote for uma menssagem:
            elif data.startswith("7777:"):
                header = data.split(":")[1].split(";")[0]
                from_nickname = data.split(":")[1].split(";")[1]
                to_nickname = data.split(":")[1].split(";")[2]
                crc = data.split(":")[1].split(";")[3]
                msg = data.split(":")[1].split(";")[4]
                
                # Se a menssagem é para todos:
                if to_nickname == "TODOS":         
                    print(from_nickname + " (global): " + msg)
                    # Se não foi eu que mandei a menssagem:
                    if nickname != from_nickname:       
                        send(data)
                    # Se foi eu que mandei a menssagem:
                    else:                               
                        token = -1
                        send(TOKEN)
                
                # Se a menssagem é só para mim:
                elif to_nickname == nickname  and header == "naoexiste": 
                    # Se a menssagem chegou com erro:      
                    if crc != str(crc32(msg, False)):          
                        send("7777:NACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # Se não foi eu que mandei a menssagem:
                    elif nickname != from_nickname:       
                        print(from_nickname + ": " + msg)
                        send("7777:ACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # Se foi eu que mandei a menssagem:
                    else:                               
                        print(from_nickname + " (eu): " + msg)
                        token = -1
                        send(TOKEN)
                
                # Se a menssagem é para outro nó na rede:
                else:                  
                    # Se não foi eu que mandei a menssagem:             
                    if nickname != from_nickname:       
                        send(data)
                    # Se foi eu que mandei a menssagem:
                    else:             
                        # Se o outro nó recebeu a menssagem:                  
                        if header == "ACK":                 
                            token = -1
                            send(TOKEN)
                        # Se o outro nó recebeu a menssagem com erro:
                        elif header == "NACK":  
                            last_msg_text = last_msg.split(";")[4]
                            fixed_crc32 = crc32(last_msg_text, False)
                            last_msg = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(fixed_crc32) + ";" + last_msg_text
                            message_list = [last_msg] + message_list
                            print("SYSTEM: O nó '" + to_nickname + "' recebeu a menssagem com erro. (msg: " + msg + ")")
                            token = -1
                            send(TOKEN)
                        # Se o outro nó não existe:
                        elif header == "naoexiste":         
                            print("SYSTEM: O nó '" + to_nickname + "' não existe. (msg: " + msg + ")")
                            token = -1
                            send(TOKEN)
                            
        except ConnectionResetError:
            pass
        
# Uma thread executa essa função para lidar com o input de mensagens no terminal.             
def handle_input():
    global message_list, nickname
    
    print("\n# === === === === === === Chat === === === === === === #")
    print("   ↓   ↓   ↓   ↓   ↓   ↓        ↓   ↓   ↓   ↓   ↓   ↓\n")
    
    # Loop para ficar esperando por input de mensagens.
    while True:
        user_input = input("")
        # Se for uma mensagem privada:
        if user_input.startswith("/priv "):
            to_nickname = user_input.split(" ")[1]
            text = ' '.join(user_input.split(" ")[2:])
            new_message = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(crc32(text, True)) + ";" + text
        # Se for uma menssagem global:
        else:
            new_message = "7777:naoexiste;" + nickname + ";TODOS;" + str(crc32(user_input, True)) + ";" + user_input
        
        # Se tem espaço na lista de mensagens:
        if len(message_list) < 10:
            message_list.append(new_message)
        # Se não tem espaço na lista de mensagens:
        else:
            print("SYSTEM: Message list is full. (msg: " + user_input + ")")

# Essa função serve para enviar uma mensagem ao nodo referenciado no 'config.json'.
def send(msg):
    global ip_destny, last_msg, delay
    time.sleep(delay)
    last_msg = msg
    SOCKET.sendto(msg.encode("utf-8"), (ip_destny.split(":")[0], int(ip_destny.split(":")[1])))

##############################################################################################################
# Main:

config()

print("\n# === === === === === === Node === === === === === === #\n")
print("  → Nickname: " + nickname)
print("  → IP de destino: " + ip_destny)
print("  → Delay de menssagem: " + str(delay) + " sec")
print("  → Token generation status: " + str(gen_token))

if gen_token:
    handle_token_thread = threading.Thread(target=handle_token)
    handle_token_thread.start()

time.sleep(0.25)
recive_thread = threading.Thread(target=recive)
recive_thread.start()

time.sleep(0.25)
input_thread = threading.Thread(target=handle_input)
input_thread.start()