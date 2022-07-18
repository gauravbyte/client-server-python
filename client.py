
import sys, socket, threading, time

HOST = '127.0.0.1'
PORT = 8323

def help():
    print("AVAILABLE COMMAND")
    print("REGISTER {USERNAME}: to register")
    print("SEND {USERNAME} {message}: send message to username Unicast")
    print("ALL {message} :send message to everyone")


stdout_lock = threading.Lock()

def buildCommand(nick, cmd):
    return f'{nick}: /{cmd}'

def listen(sock, HOST, PORT):
    while True:
        data = sock.recv(1024).decode()
        stdout_lock.acquire()
        sys.stdout.write('\r\033[K' + data)
        sys.stdout.flush()
        sys.stdout.write('\n')
        stdout_lock.release()

def client(sock, nick='Default'):
    print('Sending nickname...')
    sock.send(nick.encode())
    print('Waiting for REGISTERED signal...')
    response = sock.recv(1024).decode()

    if response != 'ok':
        print(response)
        return

    print('\nConnected Successfully!\n') 
    t1 = threading.Thread(target=listen, args=(sock, HOST, PORT), daemon=True)
    t1.start()
    
    while True:
        message = input()  # take input
        stdout_lock.acquire()
        sys.stdout.write('\033[F\033[K')
        stdout_lock.release()
        sock.send(message.encode())
        if message.endswith('later'):
            break

    print('Quitting...')
    sock.close()  # close the connection
    quit(0)

if __name__ == '__main__':
    help()
    nick = str(input('Enter USERNAME: '))

    s = socket.socket()
    s.connect((HOST, PORT))

    client(sock=s, nick=nick)
