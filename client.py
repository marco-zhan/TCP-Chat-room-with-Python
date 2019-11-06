import sys
from socket import *
import select

incoming_addr = []

def handle_send(client_socket):
    user_input = input()
    client_socket.send(user_input.encode())

def handle_receive(clientSocket):
    try:
        response = clientSocket.recv(1024).decode()

        if 'has just logged on' in response:
            print(response)
            handle_send(clientSocket)
        else:
            handle_send(clientSocket)
    except:
        pass

def login_client(client_socket):
    number_tries = 0
    user_name = input("Username: ")
    while number_tries < 3: 
        password = input("Password: ")
        user_info = user_name + " " + password
        client_socket.send(user_info.encode())
        response = client_socket.recv(1024).decode()
        print(response)
        if response == '<server> Welcome to ZYX chat\nretrieving offline messages...':
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

def start_connection(host,port):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host,int(port)))
   
    sock.send("HELLO".encode())

def client_setup(server_ip,server_port):
    global incoming_addr

    client_socket = socket(AF_INET, SOCK_STREAM) 
    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    
    client_socket.connect((server_ip, server_port))

    # my_ip, my_port = client_socket.getsockname()
    # print(my_ip)


    # client_socket.bind((my_ip, my_port))

    incoming_addr.append(client_socket)
    incoming_addr.append(sys.stdin)
    
    

    try:
        login_client(client_socket)
    except BrokenPipeError:
        print("Your connection has benn closed")

    while True:
        s = select.select(incoming_addr,[],incoming_addr)
        for sock in s[0]: 
            if sock == client_socket: 
                message = sock.recv(2048).decode()
                if message == '<server> Your session has timed out' or message == '<server> Logout successful':
                    print(message)
                    client_socket.close()
                    exit(1)
                elif '<server-P2P>' in message:
                    host,port = message.split(" ")[1:]
                    try:
                        start_connection(host,port)
                    except error as e:
                        print(e)
                    # print("Connection successful")
     
                else:
                    print (message)

            # elif sock == p2p_sock:
            #     conn, addr = sock.accpet()
            #     message = sock.recv(1024).decode
            #     print(message)
            else: 
                handle_send(client_socket)

if __name__ == "__main__" :
    if (len(sys.argv) != 3):
        print("Usage: {} server_IP server_port".format(sys.argv[0]))
        exit(1)
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_setup(server_ip, server_port)
