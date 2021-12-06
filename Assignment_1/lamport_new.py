"""
 http://net-informations.com/python/net/thread.htm
Project 2
"""
import socket, threading, time
from random import randint

HOST = "127.0.0.1"
PORTS = [60001, 60002, 60003]
PID = None  # Assign PID
PORT = None  # Track of the port this server claimed
local_clock = 0

SEND_CONNECTIONS = []
LISTEN_CONNECTIONS = []

Event_Queue = []  # Track of the order in which events are recieved
Pending_Acks = []  # Track of acknowledgments pending
event_acks = {}  # Track of acknowledgements for each message/event

# Parameters clientsocket, clientAddress for data recieving
class ReceivingThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.clientAddress = clientAddress

    def run(self):
        message = ''
        while True:
            data = self.clientsocket.recv(32)
            message = data.decode()
            if message == 'bye':
                break
            if message[:3] == 'ack':
                process_acks(message)
            else:
                process_event(message)
        print("Client at ", self.clientAddress, " disconnected...")


def pending_acks_deliver(event):
    global Pending_Acks

    event_clock = int(event[-1:])
    for e in Pending_Acks:
        if int(e[-1:]) <= event_clock:
            acknowledge(e)
            Pending_Acks.remove(e)



def acknowledge(event):
    ack = str(PID) + "_" + event
    event_ack_update(ack)
    ack = 'ack_' + str(PID) + "_" + event
    multicast_message(ack)


def ack_attempt(event):
    # example 3.4 PID.timestamp
    global Pending_Acks
    if priority_event_normal(event):
        if event in Pending_Acks:
            Pending_Acks.remove(event)
        acknowledge(event)
    else:
        Pending_Acks.append(event)


def priority_event_normal(event):
    pid = int(event[:1])
    event_clock = int(event[-1:])
    for e in Event_Queue:
        if int(e[-1:]) <= event_clock and int(e[:1]) < pid:
            return False
    return True


def attempt_to_deliver(event):
    """Try to deliver the message given"""
    global Event_Queue, local_clock
    for e in Event_Queue:
        if e in event_acks:
            if len(event_acks[e]) == 2:
                Event_Queue.remove(e)
                print("Deliverd:", e)
                pending_acks_deliver(e)


# Updation of event acknowledgment
def event_ack_update(ack):
    global event_acks
    if len(ack) == 5:
        pid = ack[:1]
        event = ack[2:]
        if event in event_acks:
            event_acks[event].add(pid)
        else:
            event_acks[event] = set(pid)

# Processing acknowledgment
def process_acks(ack):
    acks = ack.split("ack_")
    for i in range(1, len(acks)):
        ack = acks[i]
        extra_event = None
        if len(ack) == 8:  # Handle acks nested with events
            extra_event = ack[-3:]
            ack = ack[:5]
        event = ack[2:5]
        event_ack_update(ack)
        attempt_to_deliver(event)
        if extra_event is not None:
            process_event(extra_event)
            attempt_to_deliver(event)


def process_event(event):
    """Handle an event we received."""
    global Event_Queue, event_acks, local_clock
    extra_ack = None
    if len(event) > 3:
        extra_ack = event[3:]
        event = event[:3]
    Event_Queue.append(event)
    ack_attempt(event)
    if extra_ack is not None:
        process_acks(extra_ack)



def multicast_message(message):
    for conn in SEND_CONNECTIONS:
        conn.send(bytes(message, 'UTF-8'))


def perform_operation():
    global local_clock, Event_Queue
    local_clock += 1  # increment the clock

    event = str(PID) + "." + str(local_clock)

    Event_Queue.append(event)

    multicast_message(event)

# Operations to count the number of undelivered events, acks and pending acknowledgment
def run_operations():
    count = 0
    while count < 3:
        perform_operation()
        count += 1

    time.sleep(5)

    print("Undelivered events: ", Event_Queue)
    print("Undelivered acks: ", event_acks)
    print("Pending_Acks : ", Pending_Acks)

    count = 0
    while count <= 20:
        count += 1
        attempt_to_deliver("random")


def establish_connections():
    ports = list()  # Create a local copy of ports
    for port in PORTS:
        ports.append(port)

    print("Ports before removal", ports)
    print("Ports to be removed", PORT)

    while PORT is None:
        pass  # wait until we know what PORT the process claimed

    ports.remove(PORT)  # Don't send message to ourselves

    while len(SEND_CONNECTIONS) != 2:
        for port in ports:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((HOST, port))
                print("Connected to port", port)
                ports.remove(port)
                SEND_CONNECTIONS.append(client)
            except Exception as e:
                pass  # Do nothing with the connection
        print("trying to connect again in 2 seconds")
        time.sleep(2)

    print("Sender successfully connected to all the processes ", len(SEND_CONNECTIONS))

    """ Starts operations once all connections are established """
    if len(SEND_CONNECTIONS) == 2 and len(LISTEN_CONNECTIONS) == 2:
        print("Will wait 5 secs before starting operations")
        time.sleep(5)
        run_operations()


def start_listener():
    global PID
    global LISTEN_CONNECTIONS
    global PORT
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    for port in PORTS:
        try:
            server.bind((HOST, port))
            print("Listener started at: ", port)
            PORT = port
            port_str = str(port)
            PID = port_str[-1:]  # Use port no. last char to be the PID
            break
        except Exception as e:
            print("Error: ", e)
            pass
    print("PID", PID)
    while len(LISTEN_CONNECTIONS) != 2:
        server.listen(1)
        clientsock, clientAddress = server.accept()
        print("Listener accepted connection from: ", clientAddress)
        LISTEN_CONNECTIONS.append((clientsock, clientAddress))
        newthread = ReceivingThread(clientAddress, clientsock)
        newthread.start()

    print("Listener connected to all 3 processes", len(LISTEN_CONNECTIONS))


start_listener_thread = threading.Thread(target=start_listener, args=())

start_listener_thread.start()
establish_connections()

start_listener_thread.join()
