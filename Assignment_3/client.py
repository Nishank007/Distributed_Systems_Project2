import socket
import time
import json
import random

HOST = '127.0.0.1'
PORT = 12345

update_count = 0

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

def convert_to_bytes(string):
    """ A helper function for converting a string into bytes """
    return bytes(string, encoding="ascii")

def update_file():
    print("Updating...")
    with open('file.txt', "r+") as f:
        data = json.loads(f.read())
        count = int(data)
        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()

def main():
    count = 0
    start = s.recv(16).decode()

    while count < 10:
        s.send(convert_to_bytes("request"))

        s.settimeout(1)
        response = ''
        try:
            response = s.recv(16).decode()
        except socket.timeout as e:
            print("No Response! Trying Again")

        if response == "granted":
            time.sleep(1)
            update_file()
            time.sleep(random.randint(1, 3))
            count += 1
            s.send(convert_to_bytes("release"))
    print("Done")
    s.close()

if __name__ == '__main__':
    main()
