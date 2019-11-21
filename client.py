import sys
from socket import *
import select
import os
import math
import time

incoming_addr = []
peer_in_conns = {}
peer_out_conns = {}
online_status = {}
my_name = None

# Pass in a user name to this function
# Check if client has connection to this user
def have_conn(user_name):
    global peer_out_conns
    for key in peer_out_conns:
        if key == user_name:
            return True
    return False

# Pass in a user_name to this function
# Close peer connection to thsi user
def close_conn(user_name):
    global peer_out_conns
    global my_name
    global incoming_addr
    k = None

    for key in peer_out_conns:
        if key == user_name:
            mesage = "<private> Private connection to <{}> has been closed".format(my_name)
            try:
                peer_out_conns[key].send(mesage.encode())
            except OSError: # if sockek is already closed
                pass
            
            try:
                incoming_addr.remove(peer_out_conns[key])
            except ValueError: # if it is already deleted
                pass
            peer_out_conns[key].close()
            k = key

    # delete client's out connections
    del peer_out_conns[k]

# Pass in a connection to this function
# Get the name of user this connection belongs to
def get_conn_name(conn):
    global peer_out_conns
    for key in peer_in_conns:
        if peer_in_conns[key] == conn:
            return key

# Pass in a message data string list
# Convert it to a single message string
def get_whole_message(message_data):
    message = ""
    for i in range(2,len(message_data)):
        if i == 2:
            message = message + message_data[i]
        else:
            message = message + " " + message_data[i]
    return message

# Pass in a user_name
# Check if this user is online
def user_online(user_name):
    global online_status
    for key in online_status:
        if key == user_name:
            return online_status[key]
    return False

# Pass in the clients socket
# Handle send message
def handle_send(client_socket):
    global peer_out_conns
    global my_name
    user_input = input()
    message_data = user_input.split(" ") # split user input
    command = message_data[0] # extract command

    # only private and stopprivate is handled by client, all other commands are handled by server
    if command == 'private':
        if len(message_data) < 3:
            print("<private> Usage: private <user> <message>")
            return
        receiver = message_data[1]

        if receiver == my_name:
            print("<private> Cannot private self")
            return
        if not have_conn(receiver):
            print("<private> Connection to <{}> has not been setup".format(receiver))
            return

        # get all the message into a string
        message = get_whole_message(message_data)

        m = "<private> <{}> {}".format(my_name,message)
        # send private message to peer
        try:
            sent = peer_out_conns[receiver].send(m.encode())
            if sent == 0:
                raise RuntimeError("Socket connection lost")
        except RuntimeError:
            peer_out_conns[receiver].close()
        return

    # if command is stopprivate
    elif command == 'stopprivate':
        if len(message_data) != 2:
            print("<private> Usage: stopprivate <user>")
            return
        receiver = message_data[1]
        if not have_conn(receiver):
            print("<private> You haven't setup a connection with <{}>".format(receiver))
            return
        close_conn(receiver)
        print("<private> Connection to <{}> has been closed".format(receiver))
        return
        
    elif command == 'download':
        print("Downloading ......")

    # if command is "register"
    elif command == 'register':
        if len(message_data) != 3:
            print("<server> Usage: register <filename> <num_chunks>")
            return
        file_name, num_chunks = message_data[1:] # get the file_name and number of chunks from register message
        
        try: # catch error if num_chunks is not a number
            num_chunks = int(num_chunks)
        except ValueError: # if chunk number is not a number
            print('<server> Usage: register <filename> <num_chunks(int)>')
            return

        if num_chunks == 0:
            print('<server> Number of chunks cannot be 0')
            return

        try:
            file_size = os.stat(file_name).st_size
        except FileNotFoundError:
            print("<server> [{}] No such file or directory".format(file_name))
            return
    
        chunk_size = math.ceil(file_size / num_chunks)
        user_input = user_input + ' ' + str(chunk_size)

    client_socket.send(user_input.encode())

# Pass in client's socket to this function
# Try to login client
def login_client(client_socket):
    global my_name
    number_tries = 0
    user_name = input("Username: ")
    while number_tries < 3:
        password = input("Password: ")
        user_info = user_name + " " + password
        try:
            sent = client_socket.send(user_info.encode())
            if sent == 0:
                raise RuntimeError("Connection to server lost")
        except RuntimeError:
            client_socket.close()
            print("Connection to server lost, please restart program")
            print("Shutting down ......")
            exit(1)
        try:
            response = client_socket.recv(1024).decode()
            if response == '':
                raise RuntimeError("Connection to server lost")
        except RuntimeError:
            client_socket.close()
            print("Connection to server lost, please restart program")
            print("Shutting down ......")
            exit(1)

        print(response)
        # handle response message from server
        if response == '<server> Welcome to ZYX chat\nretrieving offline messages...':
            my_name = user_name
            break
        elif response == '<server> User does not exist':
            client_socket.close()
            exit(1)
        elif response == '<server> User Already logged in':
            client_socket.close()
            exit(1)
        elif response == '<server> Your session has timed out':
            client_socket.close()
            exit(1)
        elif '<server> Your account is blocked due to multiple login failures' in response:
            client_socket.close()
            exit(1)
        else:
            number_tries += 1

    if (number_tries == 3):
        client_socket.close()
        exit(1)

# Pass in the target client's host, port and user_name
# Try to connect to client's p2p socket
def start_private_connection(host,port,to_who):
    global peer_out_conns
    global my_name
    global incoming_addr
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host,int(port)))
    # record this socket
    peer_out_conns[to_who] = sock
    incoming_addr.append(sock)
    # send to the target client my name for recording
    sock.send(my_name.encode())

def handle_send_file(file_name,chunk_num,chunk_size,sock):
    fp = open(file_name, "r")
    fp.seek(chunk_num*chunk_size)
    chunk_content = "<file> {} {} {} ".format(file_name,chunk_num,chunk_size)
    chunk_content = chunk_content + fp.read(chunk_size)
    fp.close()
    sock.send(chunk_content.encode())

def get_file_content(message_data):
    content = ""
    for i in range(4,len(message_data)):
        if i == 4:
            content = content + message_data[i]
        else:
            content = content + " " + message_data[i]
    return content

# Pass in the server ip and server port to this function
# Set up the client
def client_setup(server_ip,server_port):
    global incoming_addr
    global online_status
    global peer_in_conns
    global peer_out_conns

    # Create client socket, set to reuse address
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    # Connect to server
    client_socket.connect((server_ip, server_port))

    # Get client's ip and port after connected to server
    my_ip, my_port = client_socket.getsockname()

    # Create p2p socket, set to reuse address
    p2p_socket = socket(AF_INET, SOCK_STREAM)
    p2p_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # bind socket to its ip and port and listen
    p2p_socket.bind((my_ip,my_port))
    p2p_socket.listen(1)

    # incoming address of client (Windows does not support sys.stdin)
    incoming_addr.append(client_socket)
    incoming_addr.append(sys.stdin)
    incoming_addr.append(p2p_socket)

    try:
        login_client(client_socket)

    except BrokenPipeError:
        print("Your connection has benn closed")

    while True:
        # socket select is used to deal with blocking
        s = select.select(incoming_addr,[],incoming_addr)
        for sock in s[0]: # all incoming addresses
            if sock == client_socket: # if it is the socket connected to server -> handle message received from server
                try:
                    message = sock.recv(2048).decode()
                    if message == '':
                        raise RuntimeError("Socket connection lost")
                except RuntimeError:
                    client_socket.close()
                    p2p_socket.close()
                    print("Connection to server lost, please restart program")
                    print("Shutting down ......")
                    exit(1)

                # all message received will be in format "<sender> <message>"
                from_who = message.split(" ")[0]

                # if server sends back timeout of logout successful message, close sockets, exit program
                if message == '<server> Your session has timed out' or message == '<server> Logout successful':
                    print(message)
                    client_socket.close()
                    p2p_socket.close()
                    exit(1)

                # handle logout message sender by server
                # update client's online status dictionary about this user
                elif from_who == '<server>' and 'has logged out' in message:
                    print(message)
                    message_data = message.split(" ")
                    who = message_data[1] # this position is the user_name send from server
                    online_status[who] = False  
                    if have_conn(who):
                        print('<private> Private connection to <{}> has been shutted down'.format(who))
                        close_conn(who)
                        
                # handle log on message from server
                # update client's online status dictionary about this user
                elif from_who == '<server>' and 'has just logged on' in message:
                    message_data = message.split(" ")
                    who = message_data[1]
                    online_status[who] = True
                    print(message)

                # special p2p resposne message from server, it has a special tag from the server
                # It has format '<server-P2P> user's_host user's_port' user_name'
                elif from_who == '<server-P2P>':
                    host,port,to_who = message.split(" ")[1:]
                    online_status[to_who] = True
                    if have_conn(to_who):
                        print("<private> Private connection to <{}> has already been setup".format(to_who))
                    else :
                        try:
                            start_private_connection(host,port,to_who)
                            print("<private> Private connection to <{}> has been setup".format(to_who))
                        except error as e:
                            print(e)

                # special p2p resposne message from server, it has a special tag from the server
                # It has format '<server-P2P-file> user's_host user's_port' user_name file_user_requesting chunk_num and chunk_size
                elif from_who == '<server-P2P-file>':
                    host, port, to_who, file_name, chunk_num, chunk_size = message.split(" ")[1:]
                    online_status[to_who] = True
                    if not have_conn(to_who): # set up a connection with this client no p2p connections between these two clients
                        try:
                            start_private_connection(host,port,to_who)
                            print("<private> Private connection to <{}> has been setup".format(to_who))
                            time.sleep(2)
                        except error as e:
                            print(e)
                    # send a requst message to this client, format: <request> file_name, chunk_number, chunk_size
                    message = '<request> {} {} {}'.format(file_name, chunk_num, chunk_size)
                    peer_out_conns[to_who].send(message.encode())

                # other normal messages just print
                else:
                    print (message)

            elif sock == p2p_socket: # if socket is p2p socket
                conn, addr = sock.accept() # accpet connection
                try:
                    from_who = conn.recv(2048).decode()
                    if from_who == '':
                        raise RuntimeError("Socket connection to peer lost")
                except RuntimeError:
                    conn.close()
                    conn.shutdown(SHUT_RDWR)
                
                # record this incoming connection to client
                peer_out_conns[from_who] = conn
                incoming_addr.append(conn)

                print("<private> <{}> has setup a private connection with you".format(from_who))

            elif sock == sys.stdin: # if socket is stdin, handle message typed in
                handle_send(client_socket)

            else:   # this is some sockets connected to different clients
                try:
                    message = sock.recv(1024).decode()
                    if message == '':
                        raise RuntimeError("Socket connection to peer lost")
                except RuntimeError:
                    sock.close()
                    incoming_addr.remove(sock)
                except OSError:
                    sock.close()

                message_data = message.split(" ")

                if  message == '<private> Private connection to <{}> has been closed'.format(from_who):
                    sock.close()
                    incoming_addr.remove(sock)
                    print(message)

                elif message_data[0] == '<request>':
                    file_name, chunk_num, chunk_size = message_data[1:]
                    chunk_num = int(chunk_num)
                    chunk_size = int(chunk_size)
                    handle_send_file(file_name,chunk_num,chunk_size,sock)
                
                elif message_data[0] == '<file>':
                    time.sleep(5)
                    content = get_file_content(message_data)
                    file_name, chunk_num, chunk_size = message_data[1:4]
                    chunk_num = int(chunk_num)
                    chunk_size = int(chunk_size)
                    if not os.path.exists(file_name):
                        fp = open(file_name,"w")
                        fp.close()
                    fp = open(file_name,"r+")
                    fp.seek(chunk_num*chunk_size)
                    fp.write(content)
                    fp.close()
                    message = 'registerChunk {} {} {}'.format(my_name,file_name,chunk_num)
                    client_socket.send(message.encode())

                else:
                    # print message received from these p2p connections
                    print(message)


if __name__ == "__main__" :
    if (len(sys.argv) != 3):
        print("Usage: {} server_IP server_port".format(sys.argv[0]))
        exit(1)

    # get command line variables
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_setup(server_ip, server_port)
