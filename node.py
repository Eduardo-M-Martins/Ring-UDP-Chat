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
ip_destiny, last_msg, nickname = "", "", ""
delay = 0
gen_token, recieve_token = False, True

SOCKET = socket(AF_INET, SOCK_DGRAM)    # Socket.
TOKEN = "9000"                          # Define o token.
TOKEN_EXCESS = 4                        # Tempo mínimo entre a chegada de Tokens.
TOKEN_TIMEOUT = 30                      # Tempo máximo sem receber Tokens.
PORT = 5000                             # Porta da conexão.
PRINT = True                            # Define se os detalhes do Token e pacotes serão impressos no chat.
ERRO = True                             # Define se o gerador de erros deve estar ativado.

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
# Funções:

# Essa função lê o arquivo 'config.json' para setar as configurações iniciais do nodo.
def config():
    global ip_destiny, nickname, delay, gen_token
    
    with open("config.json", "r") as f:
        config = json.load(f)
        f.close()
    ip_destiny = str(config["ip_destiny"])
    nickname = str(config["nickname"])
    delay = int(config["delay"])
    gen_token = bool(config["gen_token"])

# Uma thread executa essa função para lidar com o token. Só executa se 'gen_token' estiver em 'True' no 'config.json'.
def handle_token():
    global last_token_date
    
    time.sleep(0.25)
    # Loop para monitorar o token.
    while True:
        # Se o token demorar mutio para chegar:
        if (datetime.now() - last_token_date).total_seconds() >= TOKEN_TIMEOUT:
            # Se não é o primeiro a ser gerado token:
            if last_token_date != datetime(1900, 1, 1, 0, 0):
                print(SYSTEM_STYLE + "SYSTEM: Token timeout. New token generated." + END_STYLE)
            last_token_date = datetime.now()
            send(TOKEN)
        time.sleep(1)

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
    global last_token_date, message_list, last_msg, nickname, recieve_token
    
    SOCKET.bind(("0.0.0.0", PORT))
    
    print(HEADER_STYLE + "\n# === === === === === === Port === === === === === === #\n" + END_STYLE)
    print(TITLE_STYLE + "    UDP: " + END_STYLE + DARK_STYLE + str(PORT) + END_STYLE)
    
    # Loop para ficar esperando por pacotes.
    while True:
        try:
            data, _ = SOCKET.recvfrom(1024)
            data = data.decode("utf-8")
            time.sleep(delay)
        
            # Se o pacote for um token:
            if data == TOKEN and recieve_token:
                # Se o tken foi recebido após o tempo mínimo:
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
            
            # Se o pacote for uma menssagem:
            elif data.startswith("7777:"):
                if PRINT: print(WARNING_STYLE + "Package Check: " + data + END_STYLE)
                header = data.split(":")[1].split(";")[0]
                from_nickname = data.split(":")[1].split(";")[1]
                to_nickname = data.split(":")[1].split(";")[2]
                crc = data.split(":")[1].split(";")[3]
                msg = ";".join(data.split(":")[1].split(";")[4:])
                
                # Se a menssagem é para todos:
                if to_nickname == "TODOS":         
                    print(GLOBAL_STYLE + from_nickname + " (global): " + END_STYLE + TEXT_STYLE + msg + END_STYLE)
                    # Se não foi eu que mandei a menssagem:
                    if nickname != from_nickname:       
                        send(data)
                    # Se foi eu que mandei a menssagem:
                    else:                               
                        send(TOKEN)
                
                # Se a menssagem é só para mim:
                elif to_nickname == nickname  and header == "naoexiste": 
                    # Se a menssagem chegou com erro:      
                    if crc != str(crc32(msg, False)):          
                        send("7777:NACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # Se não foi eu que mandei a menssagem:
                    elif nickname != from_nickname:       
                        print(PRIV_STYLE + from_nickname + ": " + END_STYLE + msg)
                        send("7777:ACK;" + from_nickname + ";" + to_nickname + ";" + crc + ";" + msg)
                    # Se foi eu que mandei a menssagem:
                    else:                               
                        print(PRIV_STYLE + from_nickname + ": " + END_STYLE + TEXT_STYLE + msg + END_STYLE)
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
                            send(TOKEN)
                        # Se o outro nó recebeu a menssagem com erro:
                        elif header == "NACK":  
                            last_msg_text = ";".join(last_msg.split(";")[4:])
                            fixed_crc32 = crc32(last_msg_text, False)
                            last_msg = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(fixed_crc32) + ";" + last_msg_text
                            message_list = [last_msg] + message_list
                            print(SYSTEM_STYLE + "SYSTEM: The node '" + to_nickname + "' received the message with error. (msg: " + msg + ")" + END_STYLE)
                            send(TOKEN)
                        # Se o outro nó não existe:
                        elif header == "naoexiste":         
                            print(SYSTEM_STYLE + "SYSTEM: The node '" + to_nickname + "' doesn't exist. (msg: " + msg + ")" + END_STYLE)
                            send(TOKEN)
                            
        except ConnectionResetError:
            pass
        
# Uma thread executa essa função para lidar com o input de mensagens no terminal.             
def handle_input():
    global message_list, nickname, recieve_token
    
    print(HEADER_STYLE + "\n# === === === === === === Chat === === === === === === #" + END_STYLE)
    print(TITLE_STYLE + "   ↓   ↓   ↓   ↓   ↓   ↓        ↓   ↓   ↓   ↓   ↓   ↓\n" + END_STYLE)
    
    # Loop para ficar esperando por input de mensagens.
    while True:
        user_input = input("")
        # Se for uma mensagem privada:
        if user_input.startswith("/priv "):
            to_nickname = user_input.split(" ")[1]
            text = ' '.join(user_input.split(" ")[2:])
            new_message = "7777:naoexiste;" + nickname + ";" + to_nickname + ";" + str(crc32(text, True)) + ";" + text
        # Se for um comando para bloquear o Token:
        elif user_input == "/block":
            if recieve_token: print(SYSTEM_STYLE + "SYSTEM: Token blocked." + END_STYLE)
            recieve_token = False
            continue
        # Se for um comando para liberar o Token:
        elif user_input == "/free":
            if not recieve_token: print(SYSTEM_STYLE + "SYSTEM: Token free." + END_STYLE)
            recieve_token = True
            continue
        # Se for uma comando para forçar um token na rede
        elif user_input == "/add":
            print(SYSTEM_STYLE + "SYSTEM: New token forced." + END_STYLE)
            send(TOKEN)
            continue
        # Se for uma menssagem global:
        else:
            new_message = "7777:naoexiste;" + nickname + ";TODOS;" + str(crc32(user_input, False)) + ";" + user_input
        
        # Se tem espaço na lista de mensagens:
        if len(message_list) < 10:
            message_list.append(new_message)
        # Se não tem espaço na lista de mensagens:
        else:
            print(SYSTEM_STYLE + "SYSTEM: Message list is full. (msg: " + user_input + ")" + END_STYLE)

# Essa função serve para enviar uma mensagem ao nodo referenciado no 'config.json'.
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

time.sleep(0.5)
recive_thread = threading.Thread(target=recive)
recive_thread.start()

time.sleep(0.75)
input_thread = threading.Thread(target=handle_input)
input_thread.start()