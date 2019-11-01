import sys
from socket import *
import select

def handle_send(clientSocket):
    user_input = input()
    clientSocket.send(user_input.encode())

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
    while number_tries < 3:
        user_name = input("Username: ")
        password = input("Password: ")
        user_info = user_name + " " + password
        client_socket.send(user_info.encode())
        response = client_socket.recv(1024).decode()
        print(response)
        if response == '<server> Welcome to ZYX chat':
            break
        elif response == '<server> User Already logged in':
            client_socket.close()
            exit(1)
        elif response == '<server> Your session has timed out':
            client_socket.close()
            exit(1)
        else:
            number_tries += 1

    if (number_tries == 3):
        client_socket.close()
        exit(1)

def client_setup(server_ip,server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    login_client(client_socket)

    while True:
        incoming_addr = [client_socket,sys.stdin]
        s = select.select(incoming_addr,[],incoming_addr) 
    
        for sock in s[0]: 
            if sock == client_socket: 
                message = sock.recv(2048).decode()
                if message == '<server> Your session has timed out' or message == '<server> Logout successful':
                    print(message)
                    client_socket.close()
                    exit(1)
                print (message) 
            else: 
                handle_send(client_socket)

if __name__ == "__main__" :
    if (len(sys.argv) != 3):
        print("Usage: {} server_IP server_port".format(sys.argv[0]))
        exit(1)
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_setup(server_ip, server_port)
