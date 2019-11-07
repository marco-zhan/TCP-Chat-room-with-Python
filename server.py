#coding: utf-8
import sys
from socket import *
import threading
from datetime import datetime 
import time

client_conn = {}
all_clients = {}
online_clients = {}
online_clients_thread = {}
client_blocking = {}
server_blocking = {}
client_login_history = {}
offline_messages = {}
time_out = 0
block_period = 0

# simple function to check if a given user_name is a valid user
def valid_user(user_name):
    global all_clients
    for key in all_clients:
        if key == user_name:
            return True 
    return False

def user_blocked(sender,receiver):
    global client_blocking
    for key in client_blocking:
        if key == receiver:
            if sender in client_blocking[key]:
                return True 
    return False

def get_user(conn):
    global client_conn
    for key in client_conn:
        if client_conn[key] == conn:
            return key 

def user_online(user):
    global online_clients
    for key in online_clients:
        if key == user:
            return True
    return False
# send message to a specified receiver
# assume receiver is valid and connected
def send_message(sender,receiver, message):
    for key in client_conn:
        if key == receiver:
            m = "<{}> {}".format(sender,message)
            client_conn[key].send(m.encode())

def get_whole_message(message_data,command_type):
    message = ""
    if command_type == 'message':
        for i in range(2,len(message_data)):
            if i == 2: 
                message = message + message_data[i]
            else:
                message = message + " " + message_data[i]

    elif command_type == 'broadcast':
        for i in range(1,len(message_data)):
            if i == 1: 
                message = message + message_data[i]
            else:
                message = message + " " + message_data[i]
    return message 

def get_online_user(curr_user):
    all_users = "current online users:"
    global online_clients
    for key in online_clients:
        if key != curr_user:
            all_users = all_users + "\n" + key

    if all_users == "current online users:":
        all_users = all_users + '\nYou are the only client online'         
    return all_users 

    # get all registerd clients from the credentials file provided
# read username + password into all_clients list
def get_all_clients():
    global all_clients
    credentials_file = open("Credentials.txt","r")
    credentials = credentials_file.readlines()
    for user in credentials:
        if '\n' in user:
            user = user.replace('\n','')
        u_name, u_password = user.split(" ")
        all_clients[u_name] = u_password
        client_blocking[u_name] = []
        offline_messages[u_name] = []

# broadcase a message to all the users "online" except itself
# c_conn -> current_connection is used to differentiate itself
def broadcast(sender,message,c_conn):
    global client_conn
    flag = False
    for key in client_conn:
        if client_conn[key] != c_conn:
            receiver = get_user(client_conn[key])
            if not user_blocked(sender,receiver):
                try:
                    new_message = '<{}> {}'.format(sender,message)
                    client_conn[key].send(new_message.encode())
                except:
                    pass
            else :
                flag = True
    if flag:
        send_message('server',sender,'Your message could not be delivered to some recipients')

# Check if a user is in the cridentials and if their password matches with user_name
# A string value is returned
# If return == OK -> Authentication Successful
# If return == WRONG_INFO -> Authentication Failed, Wrong username or password
# If return == DUPLICATE -> Authentication Failed, User already logged in
def authentication(user_name, user_password):
    global all_clients
    global online_clients
    for key in all_clients:
        if key == user_name and all_clients[key] == user_password:
            for s_key in online_clients:
                if s_key == user_name and online_clients[s_key] == user_password:
                    return 'DUPLICATE'
            return 'OK'
    return 'WRONG_INFO'

def user_exist(user_name):
    global all_clients
    for key in all_clients:
        if key == user_name:
            return True 
    return False     

def get_user_conn(user_name):
    global client_conn
    for key in client_conn:
        if key == user_name:
            return client_conn[key]
# handle message received
def receiver_handler(conn,received_message):
    global client_blocking
    message_data = received_message.split(" ")
    command = message_data[0]
    sender = get_user(conn)
    if command == 'message': 
        receiver = message_data[1]
        message = get_whole_message(message_data,'message')
        if not valid_user(receiver):
            send_message('server',sender,'Invalid user specified')
            return 
        if user_blocked(sender,receiver):
            send_message('server',sender,'Your message could not be delivered as the recipient has blocked you')
            return
        if not user_online(receiver):
            offline_messages[receiver].append([sender,message])
            return
        send_message(sender,receiver,message)

    elif command == 'broadcast':
        message = get_whole_message(message_data,'broadcast')
        broadcast(sender,message, conn)
    
    elif command == 'whoelse':
        message = get_online_user(sender)
        send_message('server',sender,message)
    
    elif command == 'whoelsesince':
        since = int(message_data[1])
        message = "online users since " + str(since) + " seconds ago:"
        curr_time = datetime.now()
        for key in client_login_history:
            if key != sender:
                if user_online(key):
                    message = message + '\n' + key 
                else:
                    difference = (curr_time - client_login_history[key]).total_seconds()
                    if difference < since:
                        message = message + '\n' + key 
        if message == "online users since " + str(since) + " seconds ago:":
            message = message + '\n' + 'None'          
        send_message('server',sender,message)

    elif command == 'block':
        block_target = message_data[1]
        if len(message_data) != 2:
            send_message('server',sender,'Usage: block <user>')
            return
        if sender == block_target:
            send_message('server',sender,"Cannot block self")
            return 
        if not valid_user(block_target):
            send_message('server',sender,'Invalid user specified')
            return 
        client_blocking[sender].append(block_target)
        send_message('server',sender,block_target + ' is blocked')

    elif command == 'unblock':
        unblock_target = message_data[1]
        if len(message_data) != 2:
            send_message('server',sender,'Usage: unblock <user>')
            return
        if sender == unblock_target:
            send_message('server',sender,"Cannot unblock self")
            return
        if not valid_user(unblock_target):
            send_message('server',sender,'Invalid user specified')
            return 
        if not user_blocked(unblock_target,sender):
            send_message('server',sender,'Error: ' + unblock_target + ' was not blocked')
            return 
        client_blocking[sender].remove(unblock_target)
        send_message('server',sender,unblock_target + ' is unblocked')
    
    elif command == 'startprivate':
        receiver = message_data[1]
        if sender == receiver:
            send_message('server',sender,'Cannot establish connection with yourself')
            return 
        if not valid_user(receiver):
            send_message('server',sender,'Invalid user specified')
            return 
        if user_blocked(sender,receiver):
            send_message('server',sender,'Connection could not be established as the recipient has blocked you')
            return
        if not user_online(receiver):
            send_message('server',sender,'Recipient is offline')
            return
        host, port = get_user_conn(receiver).getpeername()
        message = "{} {} {}".format(host,port,receiver)
        send_message('server-P2P',sender,message) 
        

    elif command == 'logout':
        try:
            send_message('server',sender,'Logout successful')
            conn.shutdown(SHUT_RDWR)
            conn.close()
            del online_clients[sender]
            del client_conn[sender]
            client_login_history[sender] = datetime.now()
            message = "{} has logged out".format(sender)
            broadcast('server',message,conn)
        except Exception:
             send_message('server',sender, 'Server error, please try again')
    else:
        send_message('server',sender, 'Wrong command format')
        
def update_server(client_name, client_password, connection):
    global online_clients
    global client_conn
    online_clients[client_name] = client_password
    client_conn[client_name] = connection
    client_login_history[client_name] = datetime.now()
    message = client_name + " has just logged on"
    broadcast('server',message,connection)

def is_server_blocking(username):
    global server_blocking
    global block_period
    for key in server_blocking:
        if key == username:
            difference = (datetime.now() - server_blocking[key]).total_seconds()
            if difference > block_period:
                return [False,0] 
            else:
                return [True,(int)(block_period - difference)] 
    return [False,0]

def send_offline_message(user_name):
    global offline_messages
    m = "Offline messages are shown below"
    for key in offline_messages:
        if key == user_name:
            for message_pair in offline_messages[key]:
                sender, message = message_pair
                m = m + '\n' + '<{}> '.format(sender) + message 
            offline_messages[key] = []
    if m != "Offline messages are shown below":
        send_message('server',user_name,m)
    else:
        send_message('server',user_name,'You have no offine messages')

# log in user by calling the authentication function
# act accordingly to the return from authentication
def login_user(conn):

    number_tries = 0

    while number_tries < 3:
        client_login = conn.recv(1024).decode()
        client_name, client_password = client_login.split(" ")[:2]
        if (not user_exist(client_name)):
            conn.send('<server> User does not exist'.encode())
            conn.close()
            break 
        user_blocked, time_left = is_server_blocking(client_name) 
        if user_blocked:
            message = '<server> Your account is blocked due to multiple login failures. Please try again in {} seconds'.format(time_left)
            conn.send(message.encode())
            conn.close()
            break 
        auth_response = authentication(client_name,client_password)
        if (auth_response == 'OK'):
            update_server(client_name,client_password,conn)
            send_message('server',client_name, 'Welcome to ZYX chat\nretrieving offline messages...')
            time.sleep(3)
            send_offline_message(client_name)
            break
        elif (auth_response == 'DUPLICATE'):
            conn.send('<server> User Already logged in'.encode())
            break  
        else:
            number_tries += 1
            if (number_tries == 3):
                conn.send('<server> Invalid Username or Password. Your account has been blocked. Please try again later'.encode())
                server_blocking[client_name] = datetime.now()
                conn.close()
            else:
                conn.send('<server> Invalid Password. Please try again'.encode())

# Create a new thread for client
# Handle user login by calling login_user
def client_thread(conn):
    global time_out
    conn.settimeout(time_out)

    try:
        login_user(conn)
    except timeout:
        conn.send('<server> Your session has timed out'.encode())
        conn.shutdown(SHUT_RDWR)
        conn.close()
        return

    while True:
        try:
            received_message = conn.recv(1024).decode()
            receiver_handler(conn,received_message)
        except timeout:
            conn.send('<server> Your session has timed out'.encode())
            user = get_user(conn)
            del online_clients[user]
            del client_conn[user]
            client_login_history[user] = datetime.now()
            conn.shutdown(SHUT_RDWR)
            conn.close()
            break
        except OSError:
            pass

# setup the server, continuously listen 
def server_setup(server_port):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind(('localhost', server_port))
    serverSocket.listen(1)
    get_all_clients()


    while True:
        try:
            conn, addr = serverSocket.accept()
            print("Connected with {}:{}".format(addr[0],str(addr[1])))
            c_thread = threading.Thread(target = client_thread, args = (conn,))
            c_thread.daemon = True
            c_thread.start()
        except BrokenPipeError:
            pass

if __name__ == "__main__":
    if (len(sys.argv) != 4) :
        print("Usage: {} server_port block_duration timeout".format(sys.argv[0]))
        exit(1)

    server_port = int(sys.argv[1])
    time_out = int(sys.argv[2])
    block_period = int(sys.argv[3])

    server_setup(server_port)
