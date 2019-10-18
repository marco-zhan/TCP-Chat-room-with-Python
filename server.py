#coding: utf-8
import sys
from socket import *
from _thread import *

def server_setup(server_port):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('localhost', server_port))
    serverSocket.listen(1)

    while True:
        conn, addr = serverSocket.accept()
        print("Connected with {}:{}".format(addr[0],str(addr[1])))
        start_new_thread(client_thread, (conn,))

# Check if a user is in the cridentials and if their password matches with user_name
# A boolean value is returned
# If true, user_name and password matches, user can successfully log on
# If false, user_name and password does not match
def authentication(user_name, password):
    credentials_file = open("Credentials.txt","r")
    credentials = credentials_file.readlines()
    for user in credentials:
        if '\n' in user:
            user = user.replace('\n','')
        u_name, u_password = user.split(" ")
        if (u_name == user_name and u_password == password):
            return True
    return False

# Create a new thread for client
# This function will call authentication to ask users to log in
# Connectin is closed in log in failed
def client_thread(conn):
    login_user(conn)


def login_user(conn):
    number_tries = 0

    while number_tries < 3:
        client_user_name = conn.recv(1024).decode()
        client_password = conn.recv(1024).decode()
        if (authentication(client_user_name,client_password)):
            conn.send("Welcome to ZYX chat".encode())
            break
        else:
            number_tries += 1
            if (number_tries == 3):
                conn.send("Invalid Username or Password. Your account has been blocked. Please try again later".encode())
                conn.close()
            else:
                conn.send("Invalid Username or Password. Please try again".encode())

if __name__ == "__main__":
    if (len(sys.argv) != 4) :
        print("Usage: {} server_port block_duration timeout".format(sys.argv[0]))
        exit(1)
    server_port = int(sys.argv[1])
    server_setup(server_port)
