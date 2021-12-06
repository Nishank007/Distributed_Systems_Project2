import socket
import _thread
import time
import random

HOST = '127.0.0.1'
PORT = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
CONNECTIONS = []

lock = None

def convert_to_bytes(string):
    """ A helper function for converting a string into bytes """
    return bytes(string, encoding="ascii")

def request_lock(msg, conn):
    global lock
    number = random.randint(1, 2)
    if lock is None and number == 1:
        print("Locking...")
        conn.send(convert_to_bytes("granted"))

def release_lock(msg, conn):
    global lock
    print("Unlocked")
    lock = None

def wait():
    while len(CONNECTIONS) < 3:
        print("Wating for processes to connect!")
        time.sleep(3)

def main(conn):
    wait()
    print("3 Processes Connected")
    conn.send(convert_to_bytes("start"))
    while True:
        msg = conn.recv(1024).decode()
        if msg:
            if msg == 'request':
                request_lock(msg, conn)
            elif msg == 'release':
                release_lock(msg, conn)
            elif msg == 'bye':
                conn.close()

if __name__ == '__main__':
    f = open("file.txt", "w+")
    f.write("0")
    f.close()
    while True:
        conn, addr = s.accept()
        print("Connected: ", addr)
        CONNECTIONS.append(addr)
        server_thread = _thread.start_new_thread(main, (conn,))
    s.close()