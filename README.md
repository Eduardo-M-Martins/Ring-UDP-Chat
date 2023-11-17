# Ring-UDP-Chat
By Eduardo Machado Martins, Bernardo Pacheco Fiorini and Nathan dos Reis Ramos de Mello
## Description
This chat operates on a local network in ring topology. The application is designed to use the protocol UDP, allowing the user to send private or global messages. The communication mechanism uses a token that circulates through the ring network. When a machine receives the token and has messages in its send queue, it forwards the first message in the queue to the next machine in the ring and waits for the message to complete a turn around and return to it. Only after the message returns, the machine passes the token for the next machine in the ring. When returning a message to the sender, the header may contains ‘naoexiste’, ‘NACK’ or ‘ACK’. For each of these cases the machine must have a different attitude. The sender must, respectively, inform that the destination machine is not on the ring, inform that the message was received with error, or that the message was received successfully. For global messages, the header must contain ‘naoexiste’, and the field containing the destination's nickname must be 'TODOS'. Each machine in the ring allows the entry of new messages any time during execution. Therefore, they have a list of messages to be sent, however this list have a maximum size of 10 messages per node. The CRC field in the header is an error control calculation. Thus, if there is an error message, a ‘NACK’ must be returned.  There is a small probability that a node will send an error message, for testing purposes. It also controlled whether there is more than one token on the network, if the tokens arrive too quickly, or if the token is lost if it takes too long to arrives, this monitoring must be done by only one of the machines in the network and must be the one that generates the token for the first time. Some other features ware implemented, such as blocking and releasing token reception at any time and manual generation of a new token at any time.
## Dependencies
...
## Execution
To execute the applications, run the following command:
```
python3 node.py
```
##
<div align="center">  
  <img src="" alt="Chat preview" /> 
</div>
