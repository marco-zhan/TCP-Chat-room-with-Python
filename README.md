# TCP Chat room with Python

## Introduction
Implementation of a command line based chat room using TCP/IP, written in Python

## Dependencies
- Python 3.7

## What's included
- `server.py` This file contains the server class of the chat room
- `client.py` This file contains the client class of the chat room
- `Credentials.txt` This file contains the credentials of clients

## How to run
<b><font color=red> Note: </font></b> <b>The serve must be run on linux of macOS Operating System, as `select` library cannot be run in Windows cmd. Client class can be run on any OS</b>
1. `python server.py [server_port] [block_duration] [timeout]`
- <b><font color=red> server_ip: </font></b> The serve is set to run on 'localhost' by default, you can change the server IP address in `server.py line 740`
- `server_port:` Port which the server will run on, this should be greater than 8000
- `block_duration:` How long to block the user if they entered wrong credentials three times in a row, in seconds
- `timeout:` How long server will automatically log out clients if no response received, in seconds

1. `python client.py server_ip server_port`
- `server_ip:` IP address where the server is running on
- `server_port:` Port which the server is running on
  
3. `Credentials.txt` This file contains the credentials of the clients, each line contains a client's username and password, seperated by a spcae.

## Command format
<b><font color = red>For all commands, assume sender is A</font></b>
- `message <client> <message>`
  This command will send `<message>` to `<client>`, an error message will be displayed if `<client>` is invalid or has blocked A, an error message will be displayed if `<client>` is A, an error message will be displayed if `<message>` is None. If `<client>` is offline, `<message>` will be stored in offline messages and sent to the `<client>` when `<client>` logs on. `<message>` words are separated by space
 
  `E.g. message B how are you ?`
<br>
- `broadcast <message>`
  This command will broadcast `<message>` to all the clients online, if any client has blocked A, a warning message will be displayed, but it will still broadcast to other clients that has not blocked A. `<message>` words are separated by space

  `E.g. message B how are you ?`
<br>

- `whoelse`
  This command display the names of all clients that are currently online exclude A.
<br>

- `whoelsesince <time>`
  This command will display the names of all clients who were logged in at any time within the past `<time>` seconds excluding A. An error message will be displayed if `<time>` is not a number
  `E.g. whoelsesince 100`
<br>

- `block <client>`
This command will block `<client>`, an error message will be displayed if A has already blocked `<client>` or `<client>` is invalid. `<client>` must not be notified for this. This will block any message `<client>` sends to A
`E.g. block B`
<br>

- `unblock <client>`
This command will unblock `<client>`, an error message will be displayed if `<client>` has never been blocked or `<client>` is invalid. This will remove the effect of blocking
`E.g. unblock B`
<br>

- `logout`
  This command will logout A
<br>

- `startprivate <client>`
  This command will setup a private direct connection from A to `<client>`, an error message will be displayed if `<client>` is invalid, not online, blocked A or self. `<client>` will be notified for the setup of this connection
`E.g. startprivate B`
<br>

- `private <client> <message>`
This command will send `<message>` to `<client>` through the private connection. An error message will be displayed if `<client>` is invalid, not online, self or A has not setup a private connection with `<client>`. `<message>` words are separated by space
`E.g. private B Hello World`
<br>

- `stopprivate <client>`
This command close the private direct connection between A and client, an error message will be displayed if `<client>` is invalid, not online or self. An error message will be displayed if A has never setup a private connection with `<client>`. `<client>` will be notified for the closure of the connection
`E.g. stopprivate B`
<br>

- `register <file> <number_of_chunks>`
This command will register `<file>` to the server and separate the file in `<number_of_chunks>` chunks. An error message will be displayed if this file has already been registered at server or does not exist in client's directory. The system will read the file and calculate the chunk size automatically.
`E.g. register a.txt 5`
<br>

- `searchFile <file>`
This command will display the availability of `<file> ` in the system. An error message will be displayed if `<file>` does not exist in server. The server will reply back with either 'Not available' or 'Available' along with list of online users that have one or more chunks of the requested.
`E.g. searchFile a.txt`
<br>

- `searchChunk <file> <chunk_num>`
This command will display the availability of `<file>`, chunk `<chunk_num>` (can be many chunks separated by space) in the system. An error message will be displayed if `<file>` does not exist in server or chunk does not exist in server. The server will reply back with either 'Not available' or 'Available' along with list of online users that have one or more chunks of the requested.
`E.g. searchChunk text 0 2 3`
<br>

- `download <file> <chunk_num>`
This command will download `<file>` from server, if `<chunk_num>` is not provided, the server will download the whole file if possible. Otherwise, it will download the specific `<chunk_num>` of the `<file>` required. An error message will be displayed if `<file>` has not been registered in server or `<chunk_num>` of `<file>` does not exist in server
`E.g. download a.txt 0 2 3`
<br>

## Improvement
How to identify who sends the message is particularly hard on the client side. I implement a name tag to send together with the message, so client can check this name tag and tell who sends the message. Server uses `<server>` tag when sending, so an obvious issue would be if a user's name is `'server'`, client has no way to differentiate between server and this client. For my program, please avoid using username `'server'`, `'server-p2p'`, `'server-p2p-file'` when testing as these names is used to identify server
It could be better if a receiving buffer is implemented in both server and client side. I sometimes notice I am getting several messages received at the same time. It will be great if server can know when a message is complete and ignore the rest of the message.
Even with many exceptions checking implemented, I believe there are still some assumptions about what command to send. My program can handle CTRL + c logout by client and many other exceptions, but the more error checking implemented, the more stable server and client program will be

## Maintainer
If you have any enquiries on this project or any other questions, please contact me at `yixiao5898@gmail.com`