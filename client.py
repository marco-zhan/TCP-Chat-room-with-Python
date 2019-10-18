import sys
from socket import *

def client_setup(server_ip,server_port):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((server_ip, server_port))
    login_client(clientSocket)
    while True:
        a = 1


def login_client(clientSocket):
    number_tries = 0
    while number_tries < 3:
        user_name = input("Username: ")
        password = input("Password: ")
        clientSocket.send(user_name.encode())
        clientSocket.send(password.encode())
        response = clientSocket.recv(1024).decode()
        print(response)
        if response == 'Welcome to ZYX chat':
            break
        else:
            number_tries += 1
    if (number_tries == 3):
        clientSocket.close()
        exit(1)

if __name__ == "__main__" :
    if (len(sys.argv) != 3):
        print("Usage: {} server_IP server_port".format(sys.argv[0]))
        exit(1)
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    client_setup(server_ip, server_port)
