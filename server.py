#coding: utf-8
import sys
from socket import *
import threading
from datetime import datetime 
import time

client_conn = {} # dictionary records all clients connections in server, format: {user_name: user_conn}
all_clients = {} # dictionary records all clients registered in server, format: {user_name: user_password}
online_clients = {} # dictionary records user online status, format: {user_name: user_password}
client_blocking = {} # dictionary records the blocking status, format: {user: ["all users the key user blocked"]}
server_blocking = {} # dictionary records the server blocking status, format: {user: last_time blocked by server}
client_login_history = {} # dictionary records client last login time, format: {user: last_time user logged in}
offline_messages = {} # dictionary records all offline messages, format: {user: a list of [sender,message]}
time_out = 0    # global time_out variable
block_period = 0 # global block_period


# Pass in a user_name to this function
# Check if this user_name is valid in credentials
def valid_user(user_name):
    global all_clients
    for key in all_clients:
        if key == user_name:
            return True 
    return False

# Pass in the user_name of "sender" and "receiver" to this function
# Check if "sender" is blocked by "receiver" 
def user_blocked(sender,receiver):
    global client_blocking
    for key in client_blocking:
        if key == receiver:
            if sender in client_blocking[key]:
                return True 
    return False

# Pass in a user connection
# Get the user_name of this connection
def get_user(conn):
    global client_conn
    for key in client_conn:
        if client_conn[key] == conn:
            return key 

# Pass in a user_name to this function
# Check if this user is online
def user_online(user_name):
    global online_clients
    for key in online_clients:
        if key == user_name:
            return True
    return False

# Pass in the "sender", "receiver" and the message sender wants to send
# Send the message from sender to receiver
# Assume receiver is valid
def send_message(sender,receiver, message):
    for key in client_conn:
        if key == receiver:
            m = "<{}> {}".format(sender,message)
            try:
                sent = client_conn[key].send(m.encode())
                if sent == 0: # 0 bytes sent
                    raise RuntimeError("Socket connection lost")
            except KeyError:
                pass
            except RuntimeError:
                client_conn[key].close()

# Pass in the message data (a list of strings) and command type (message or broadcast)
# Convert this list of message strings to a single string
# A command type is passed in as broadcast and message 's message data starts from different list index
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

# Pass in the user_name who initiates this function call
# Returns a string of all users currently online exclude the user passed in
# All users are separated by a new line character
# If no users online, "You are the only client online" is returned
def get_online_user(curr_user):
    all_users = "current online users:"
    global online_clients
    for key in online_clients:
        if key != curr_user:
            all_users = all_users + "\n" + key

    if all_users == "current online users:":
        all_users = all_users + '\nYou are the only client online'         
    return all_users 

# Get all registerd clients from the credentials file provided
# Read username and password into all_clients dictionary
def get_all_clients():
    global all_clients
    credentials_file = open("Credentials.txt","r")
    credentials = credentials_file.readlines()
    for user in credentials:
        if '\n' in user:
            # deal with the last '\n' in the file
            user = user.replace('\n','')
        # split the line
        u_name, u_password = user.split(" ")
        all_clients[u_name] = u_password
        # initialize the following two dictionary
        client_blocking[u_name] = []
        offline_messages[u_name] = []

    credentials_file.close()

# Pass in the sender, broadcast message and sender's connection
# Broadcast a message to all the users "online" except itself
# c_conn -> current_connection is used to differentiate itself
# Broadcast message will not be added to offline messages
def broadcast(sender,message,c_conn):
    global client_conn
    flag = False # blocked flag, check if sender is blocked by some receivers
    for key in client_conn:
        if client_conn[key] != c_conn:
            receiver = get_user(client_conn[key])
            if not user_blocked(sender,receiver):
                try:
                    new_message = '<{}> {}'.format(sender,message)
                    sent = client_conn[key].send(new_message.encode())
                    if sent == 0:
                        raise RuntimeError("Socket connection lost")
                except RuntimeError:
                    client_conn[key].close()
            else :
                flag = True
    if flag:
        send_message('server',sender,'Your message could not be delivered to some recipients')

# Pass in a user name and users password
# Check if a user is in the cridentials and if their password matches with user_name
# A string value is returned
# If return == OK -> Authentication Successful
# If return == WRONG_INFO -> Authentication Failed, Wrong username or password
# If return == DUPLICATE -> Authentication Failed, User already logged in
def authentication(user_name, user_password):
    global all_clients
    global online_clients
    for key in all_clients:
        # both user_name and password is checked
        if key == user_name and all_clients[key] == user_password:
            for s_key in online_clients:
                if s_key == user_name and online_clients[s_key] == user_password:
                    return 'DUPLICATE'
            return 'OK'
    return 'WRONG_INFO'

# Pass in a user_name
# Get users connection in server
# Assume user is valid
def get_user_conn(user_name):
    global client_conn
    for key in client_conn:
        if key == user_name:
            return client_conn[key]

# Pass in the user's connection and the message received from client
# Do action accordingly
def receiver_handler(conn,received_message):
    global client_blocking
    # split the received message by space
    message_data = received_message.split(" ")
    # Extract first element (this is the command keyword)
    command = message_data[0]
    # Get the sender of this message by sender's connection
    sender = get_user(conn)

    # if command word is "message"
    if command == 'message':
        if len(message_data) < 3: # Wrong messaging format
            send_message('server',sender,"Usage: message <user> <message>")
            return

        receiver = message_data[1]
        if receiver == sender: # Message self
            send_message('server',sender,"Cannot send message to self")
            return

        message = get_whole_message(message_data,'message')
        if message == '': # Message is none
            send_message('server',sender,'Message cannot be none')
            return 

        if not valid_user(receiver): # Invalid user specified
            send_message('server',sender,'Invalid user specified')
            return 

        if user_blocked(sender,receiver): # Sender is blocked by receiver
            send_message('server',sender,'Your message could not be delivered as the recipient has blocked you')
            return

        if not user_online(receiver): # Record to offline message if user is offline
            offline_messages[receiver].append([sender,message])
            return

        send_message(sender,receiver,message)

    # if command word is "broadcast"
    elif command == 'broadcast':
        if len(message_data) < 2: # Wrong broadcast format
            send_message('server',sender,'Usage: broadbast <message>')
            return

        message = get_whole_message(message_data,'broadcast')
        if message == '': # Message is None
            send_message('server',sender,'Message cannot be none')
            return 
        
        broadcast(sender,message, conn)
    
    # if command word is "whoelse"
    elif command == 'whoelse':
        if len(message_data) != 1: # Wrong whoelse formant
            send_message('server',sender,'Usage: whoelse')
            return

        message = get_online_user(sender) # get all online users
        send_message('server',sender,message)
    
    # if command word is "whoelsesince"
    elif command == 'whoelsesince':
        if len(message_data) != 2: # Wrong whoelsesince format
            send_message('server',sender,'Usage: whoelsesince <time>')
            return
        try:
            since = int(message_data[1])
        except ValueError: # if time is not a number
            send_message('server',sender,'Usage: whoelsesince <time (a number)>')
            return

        message = "online users since " + str(since) + " seconds ago:"
        curr_time = datetime.now() # get the current date time
        for key in client_login_history:
            if key != sender:
                if user_online(key): # if user is still online, record it
                    message = message + '\n' + key 
                else: # user is offline
                    difference = (curr_time - client_login_history[key]).total_seconds() # check user's last login time and how long since now
                    if difference < since: # if less than time specified
                        message = message + '\n' + key 

        if message == "online users since " + str(since) + " seconds ago:":
            message = message + '\n' + 'None'      

        send_message('server',sender,message)

    # if command is "block"
    elif command == 'block':
        if len(message_data) != 2: # Wrong block format
            send_message('server',sender,'Usage: block <user>')
            return

        block_target = message_data[1]
        if sender == block_target: # Block self
            send_message('server',sender,"Cannot block self")
            return 

        if not valid_user(block_target): # Block target is invalid
            send_message('server',sender,'Invalid user specified')
            return

        if user_blocked(block_target,sender): # If user has already been blocked
            send_message('server',sender,block_target + " has already been blocked")
            return

        client_blocking[sender].append(block_target) # block user

        send_message('server',sender,block_target + ' is blocked')

    # if command is "unblock"
    elif command == 'unblock':
        if len(message_data) != 2 : # Wrong unblock format
            send_message('server',sender,'Usage: unblock <user>')
            return

        unblock_target = message_data[1]
        if sender == unblock_target: # Unblock self
            send_message('server',sender,"Cannot unblock self")
            return

        if not valid_user(unblock_target): # Unblocked target invalid
            send_message('server',sender,'Invalid user specified')
            return 

        if not user_blocked(unblock_target,sender): # Target is not blocked
            send_message('server',sender,unblock_target + ' was not blocked')
            return 

        client_blocking[sender].remove(unblock_target) # Remove blocking 

        send_message('server',sender,unblock_target + ' is unblocked')
    
    # if command is "startprivate"
    elif command == 'startprivate':
        if len(message_data) != 2: # Wrong startprivate format
            send_message('server',sender,'Usage: startprivate <user>')
            return

        receiver = message_data[1]
        if sender == receiver: # Private self
            send_message('server',sender,'Cannot establish connection with self')
            return 

        if not valid_user(receiver): # Invalid user
            send_message('server',sender,'Invalid user specified')
            return 

        if user_blocked(sender,receiver): # User blocked
            send_message('server',sender,'Connection could not be established as the recipient has blocked you')
            return

        if not user_online(receiver): # User offline
            send_message('server',sender,'Recipient is offline')
            return

        host, port = get_user_conn(receiver).getpeername() # get users host and port
        message = "{} {} {}".format(host,port,receiver)
        send_message('server-P2P',sender,message) 
    
    # if command is "logout"
    elif command == 'logout':
        if len(message_data) != 1: # Wrong logout format
            send_message('server',sender,'Usage: logout')
            return
        try:
            send_message('server',sender,'Logout successful') # send logout message to client
            conn.shutdown(SHUT_RDWR)
            conn.close()
            del online_clients[sender] # set user offline
            del client_conn[sender] # Delete user connection
            client_login_history[sender] = datetime.now()
            message = "{} has logged out".format(sender)
            broadcast('server',message,conn) # broadcast to all other online users
        except Exception:
            send_message('server',sender, 'Server error, please try again')
    
    # Wrong command format
    else:
        send_message('server',sender, 'Wrong command format')

# Pass in a client name, client password and client connection
# Update server data
def update_server(client_name, client_password, connection):
    global online_clients
    global client_conn
    online_clients[client_name] = client_password
    client_conn[client_name] = connection
    client_login_history[client_name] = datetime.now()
    message = client_name + " has just logged on"
    # Broadcast presense message
    broadcast('server',message,connection)

# Pass in a user_name
# Check if this user is blocked by server
def is_server_blocking(user_name):
    global server_blocking
    global block_period
    for key in server_blocking:
        if key == user_name: # if user has blocked history
            difference = (datetime.now() - server_blocking[key]).total_seconds()
            if difference > block_period:
                del server_blocking[key] # avoid recheck 
                return [False,0] 
            else:
                return [True,(int)(block_period - difference)] 
    return [False,0]

# Pass in a user_name
# Get all this user's offline messages
def send_offline_message(user_name):
    global offline_messages
    m = "Offline messages are shown below"
    for key in offline_messages: # Get all offline messages
        if key == user_name:
            for message_pair in offline_messages[key]:
                sender, message = message_pair
                m = m + '\n' + '<{}> '.format(sender) + message 
            offline_messages[key] = []
    if m != "Offline messages are shown below":
        send_message('server',user_name,m)
    else:
        send_message('server',user_name,'You have no offine messages')

# Pass in a connection
# Log in user by calling the authentication function
# Act accordingly to the return from authentication
def login_user(conn):

    number_tries = 0 # count number of tries 

    while number_tries < 3:
        try:
            client_login = conn.recv(1024).decode() # Get the login info from client
            if client_login == '': # Connection lost
                raise RuntimeError("Socket connection lost")

        except RuntimeError: # catch connection lost, close socket
            conn.shutdown(SHUT_RDWR)
            conn.close()
            break

        client_name, client_password = client_login.split(" ")[:2] # Assue client message contain user_name password
        
        if (not valid_user(client_name)): # Client name is invalid, break out
            conn.send('<server> User does not exist'.encode())
            conn.close()
            break 

        user_blocked, time_left = is_server_blocking(client_name)

        if user_blocked: # if user is blocked by server, break out
            message = '<server> Your account is blocked due to multiple login failures. Please try again in {} seconds'.format(time_left)
            conn.send(message.encode())
            conn.close()
            break 

        auth_response = authentication(client_name,client_password) # authenticate user

        if (auth_response == 'OK'): # Log in successful
            update_server(client_name,client_password,conn)
            send_message('server',client_name, 'Welcome to ZYX chat\nretrieving offline messages...')
            time.sleep(3)
            send_offline_message(client_name) # Get user offline messages
            break

        elif (auth_response == 'DUPLICATE'): # Duplicate login, break out
            conn.send('<server> User Already logged in'.encode())
            break 

        else: # Wrong password
            number_tries += 1
            if (number_tries == 3):
                message = '<server> Invalid Username or Password. Your account has been blocked. Please try again in {} seconds'.format(block_period)
                conn.send(message.encode())
                server_blocking[client_name] = datetime.now()
                conn.close()
            else:
                conn.send('<server> Invalid Password. Please try again'.encode())

# Pass in a user connection
# Create a new thread for client
# Handle user login by calling login_user
def client_thread(conn):
    global time_out
    conn.settimeout(time_out) # Set a timeout for this connection
    
    try:
        login_user(conn)
    except timeout: # if user timeout in login
        conn.send('<server> Your session has timed out'.encode())
        user = get_user(conn)
        message = "{} has logged out".format(user)
        broadcast('server',message,conn)
        conn.shutdown(SHUT_RDWR)
        conn.close()
        return

    while True:
        try:
            received_message = conn.recv(1024).decode()
            if (received_message == ''):
                raise RuntimeError("Sockets connection broken")

            # pass received message to receive_handler
            receiver_handler(conn,received_message)
            
                
        except timeout: # user timeout 
            conn.send('<server> Your session has timed out'.encode())
            user = get_user(conn)
            message = "{} has logged out".format(user)
            broadcast('server',message,conn)
            del online_clients[user]
            del client_conn[user]
            client_login_history[user] = datetime.now()
            conn.shutdown(SHUT_RDWR)
            conn.close()
            break

        except RuntimeError:
            conn.send('<server> Lost connection to server'.encode())
            user = get_user(conn)
            message = "{} has logged out".format(user)
            broadcast('server',message,conn)
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
    serverSocket.bind(('192.168.0.9', server_port))
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

    # get variable from command line
    server_port = int(sys.argv[1])
    time_out = int(sys.argv[2])
    block_period = int(sys.argv[3])

    server_setup(server_port)
