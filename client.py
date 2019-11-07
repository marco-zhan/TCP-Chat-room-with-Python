import sys
from socket import *
import select

incoming_addr = []
outgoing_addr = []
peer_conns = {}
online_status = {}
my_name = None

def have_conn(user_name):
    global peer_conns
    for key in peer_conns:
        if key == user_name:
            return True
    return False

def get_whole_message(message_data):
    message = ""
    for i in range(2,len(message_data)):
        if i == 2: 
            message = message + message_data[i]
        else:
            message = message + " " + message_data[i]
    return message

def user_online(user_name):
    global online_status
    for key in online_status:
        if key == user_name:
            return online_status[key]
    return False

def handle_send(client_socket):
    global peer_conns
    global my_name
    user_input = input()
    message_data = user_input.split(" ")
    command = message_data[0]
    if command == 'private':
        if len(message_data) < 3:
            print("Wrong command format")
            return
        receiver = message_data[1]
        message = get_whole_message(message_data)
        if not have_conn(receiver):
            print("Connection to ",receiver," has not been setup")
            return
        if not user_online(receiver):
            print(receiver, " is offline")
            return

        m = "<private> <{}> {}".format(my_name,message)
        peer_conns[receiver].send(m.encode())
        return
    client_socket.send(user_input.encode())


def login_client(client_socket):
    global my_name
    number_tries = 0
    user_name = input("Username: ")
    while number_tries < 3: 
        password = input("Password: ")
        user_info = user_name + " " + password
        client_socket.send(user_info.encode())
        response = client_socket.recv(1024).decode()
        print(response)
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

def start_connection(host,port,to_who):
    global peer_conns
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host,int(port)))
    peer_conns[to_who] = sock

def client_setup(server_ip,server_port):
    global incoming_addr
    global outgoing_addr
    global online_status

    client_socket = socket(AF_INET, SOCK_STREAM) 
    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    client_socket.connect((server_ip, server_port))

    my_ip, my_port = client_socket.getsockname()

    p2p_socket = socket(AF_INET, SOCK_STREAM) 
    p2p_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    p2p_socket.bind((my_ip,my_port))
    p2p_socket.listen(1)

    incoming_addr.append(client_socket)
    incoming_addr.append(sys.stdin)
    incoming_addr.append(p2p_socket)

    outgoing_addr.append(client_socket)
    
    try:
        login_client(client_socket)
    except BrokenPipeError:
        print("Your connection has benn closed")

    while True:
        s = select.select(incoming_addr,[],incoming_addr)
        for sock in s[0]: 
            if sock == client_socket: 
                message = sock.recv(2048).decode()
                from_who = message.split(" ")[0]
                if message == '<server> Your session has timed out' or message == '<server> Logout successful':
                    print(message)
                    client_socket.close()
                    exit(1)
                
                elif from_who == '<server>' and 'has logged out' in message:
                    message_data = message.split(" ")
                    who = message_data[1]
                    online_status[who] = False
                    print(message)
                
                elif from_who == '<server>' and 'has just logged on' in message:
                    message_data = message.split(" ")
                    who = message_data[1]
                    online_status[who] = True
                    print(message)

                elif from_who == '<server-P2P>':
                    host,port,to_who = message.split(" ")[1:]
                    try:
                        start_connection(host,port,to_who)
                        print("You are connected to " + to_who)
                    except error as e:
                        print(e)                    
                else:
                    print (message)

            elif sock == p2p_socket:
                conn, addr = sock.accept()
                incoming_addr.append(conn)
               
            elif sock == sys.stdin: 
                handle_send(client_socket)
            
            else:
                message = sock.recv(1024).decode()
                print(message)


if __name__ == "__main__" :
    if (len(sys.argv) != 3):
        print("Usage: {} server_IP server_port".format(sys.argv[0]))
        exit(1)
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_setup(server_ip, server_port)
