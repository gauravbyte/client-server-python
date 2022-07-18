

import socket, threading, re
from queue import Queue

HOST = '127.0.0.1'
PORT = 8323
CLIENT_DICT = dict()
BROADCAST_QUEUE = Queue()

lock_clientDict = threading.Lock()
lock_broadcast = threading.Lock()
def help():
    print("AVAILABLE COMMAND")

    print("FORWARD {USERNAME} {message}: send message to username Unicast")
    print("ALL {message} :send message to everyone")
#thread for server response to clients
def serversend() :

    while True:
        cmd = input()
        command = cmd.split(' ')
        if command[0] == 'ALL':
            enqueueMessage(f'SERVER: BROADCAST{cmd[4:]}')
        if command[0] == 'FORWARD':
            lock_clientDict.acquire()
            dest = CLIENT_DICT[command[1]]
            lock_clientDict.release()
            join = ' '.join(command[2:])
            msg = f'UNICAST from SERVER: {join}'.encode()
            dest.send(msg)



def verifyusername(username):
    return username not in CLIENT_DICT

def enqueueMessage(msg):
    lock_broadcast.acquire()
    BROADCAST_QUEUE.put(msg.encode())
    lock_broadcast.release()

def handleCommand(cmd, username, sock):
    command = cmd.split(' ')
    print(f'Received command {command} from {username}')

    # Commands
    if command[0] == 'ALL':
        join = ' '.join(command[1:])
        enqueueMessage(f'BROADCAST from {username} :{join}')
    elif command[0] == 'SEND':
        destname = command[1]
        lock_clientDict.acquire()
        dest = CLIENT_DICT.get(destname)
        lock_clientDict.release()
        if dest is None:
            msg = f'host {destname} does not exist'.encode()
            sock.send(msg)
            return
        join = ' '.join(command[2:])
        msg = f'UNICAST to {destname}: {join}'.encode()
        sock.send(msg)
        msg = f'UNICAST from {username}: {join}'.encode()
        dest.send(msg)

 
def client_thread(sock, address, username):
    while True:
        msg = sock.recv(1024).decode()
        if len(msg) == 0: # Detect abrupt disconnect
            break
        print(address, ' ', username, ':', msg)

        # The / of a command should be 2 characters right of :
        handleCommand(msg, username, sock)
            # continue

        # enqueueMessage(f'{username}: {msg}')

    sock.send('\nGoodbye!'.encode())
    sock.close()
    lock_clientDict.acquire()
    CLIENT_DICT.pop(username)
    lock_clientDict.release()
    print(f'Removed {username} from clientDict')
    return 0

def broadcast_thread():
    # Send all enqueued messages to each client
    while True:
        while not BROADCAST_QUEUE.empty():
            lock_broadcast.acquire()
            msg = BROADCAST_QUEUE.get()
            lock_broadcast.release()

            lock_clientDict.acquire()
            for sock in CLIENT_DICT.values():
                sock.send(msg)
            lock_clientDict.release()

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f'Starting server at {HOST}')
    s.bind((HOST, PORT))

    s.listen(5)

    # Open thread to broadcast to connected clients
    broadcastThread = threading.Thread(target=broadcast_thread, daemon=True)
    broadcastThread.start()

    # Accept connections and open a thread for each one
    while True:
        #Accept connections from within while loop
        username = None
        connection, address = s.accept() 
        connection.settimeout(3)
        username = connection.recv(1024).decode()
        messagelist = username.split(' ')
        username = messagelist[0]
        if(not username.isalnum()):
            connection.send("ERROR 100 Malform Username".encode())
            connection.close()
            continue
        
        if(username in CLIENT_DICT):
            connection.send("ERROR 101 no username registered with".encode())
            connection.close()
            continue
        print(f'New connection: {username}')
        connection.settimeout(None)
        connection.send('ok'.encode()) # Send OK signal
        lock_clientDict.acquire()
        CLIENT_DICT[username] = connection
        lock_clientDict.release()
        # Start a thread for the client.
        t1 = threading.Thread(target=client_thread, args=(connection, address, username), daemon=True)
        t1.start()


if __name__ == '__main__':
    help()
    serverthread = threading.Thread(target=serversend,daemon=True)
    serverthread.start()
    server()