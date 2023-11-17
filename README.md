# Ring-UDP-Chat
By Eduardo Machado Martins, Bernardo Pacheco Fiorini and Nathan dos Reis Ramos de Mello
## Description
This chat operates on a local network in ring topology. The application is designed to use the protocol UDP, allowing the user to send private or global messages. The communication mechanism uses a token that circulates through the ring network. When a machine receives the token and has messages in its send queue, it forwards the first message in the queue to the next machine in the ring and waits for the message to complete a turn around and return to it. Only after the message returns, the machine passes the token for the next machine in the ring. 

When returning a message to the sender, the header may contains ‘naoexiste’, ‘NACK’ or ‘ACK’. For each of these cases the machine must have a different attitude. The sender must, respectively, inform that the destination machine is not on the ring, inform that the message was received with error, or that the message was received successfully. For global messages, the header must contain ‘naoexiste’, and the field containing the destination's nickname must be 'TODOS'. Each machine in the ring allows the entry of new messages any time during execution. Therefore, they have a list of messages to be sent, however this list have a maximum size of 10 messages per node. 

The CRC field in the header is an error control calculation. Thus, if there is an error message, a ‘NACK’ must be returned.  There is a small probability that a node will send an error message, for testing purposes. It also controlled whether there is more than one token on the network, if the tokens arrive too quickly, or if the token is lost if it takes too long to arrives, this monitoring must be done by only one of the machines in the network and must be the one that generates the token for the first time. Some other features ware implemented, such as blocking and releasing token reception at any time and manual generation of a new token at any time.

If a new message starts with '/priv' then a nickname is expected and then a private message.
```
/priv <nickname> <message>
```
If the input is equal to '/block' then the machine will ignore all tokens received and to activate them again, you must use the ‘/free’ command. 
```
/block
```
```
/free
```
The ‘/add’ command sends a new token immediately. 
```
/add
```
Finally, for any other case, it is understood that the input is a global message.
## Dependencies
This applications uses Python and before running, the 'config.json' file must be set as follows.
```
{
    "ip_destiny" : "<ip_destiny>:<port>",
    "nickname"  : "<self_nickname>",
    "delay"     : "<delay_between_messages_in_seconds>",
    "gen_token" : <handle_token>
}
```
Each machine in the network must point to the next machine in the <ip_destiny>:<port> field until they form a ring. Each machine must have a nickname so that private messages can be sent. A delay of a few seconds must be configured between each message. Finally, the last item is a Boolean variable that indicates whether the machine will be responsible for handling the token. This way, only one machine on the network must contain 'true' in this field, the others must contain 'false'.

Finally, depending on the number of connected machines and the configured delay, the constants 'TOKEN_EXCESS' and 'TOKEN_TIMEOUT' must be recalculated.
## Execution
To execute the applications, run the following command:
```
python3 node.py
```
##
<div align="center">  
  <img src="https://media.discordapp.net/attachments/1076157666986049598/1175077246701146212/image.png?ex=6569eaf7&is=655775f7&hm=3a489f0fe324872f391dde3c8591f5d7cdd99477349cdc751eda9cc1134fa177&=&width=376&height=390" alt="Chat preview" /> 
</div>
