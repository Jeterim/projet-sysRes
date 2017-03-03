#!/usr/bin/env python
import hashlib
import os
import socket
import time
from socketserver import ThreadingMixIn  # Python 3
from threading import Thread
from subprocess import Popen, PIPE, run
import shlex

data_dict = {"john": {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a",
                      "role": "Doctor", "lastCo": "1355563265.81"}}


class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print("[+] New thread started for " + ip + ":" + str(port))

    def run(self):
        while True:
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break
            print("received data:", data)

            args = data.split(None)
            if args[0] == "LOGIN":
                self.connect(args)
            else:
                # # TODO Check if dangerous command
                run(args, stdout=conn.makefile('r'))

    def run_command(self, process, args):
        out, err = process.communicate(input=" ".join(args).encode())
        print("{}; {}".format(out.decode('utf-8'), err))
        conn.send(out)

    def connect(self, args):
        auth = args[1].split(":")
        print("Login : {} Password : {}".format(auth[0], auth[1]))
        successauth = 0
        for user in data_dict:
            if user == auth[0] and data_dict[user]["password"] == auth[1]:
                print("it's him")
                successauth = 1
                break
        if successauth == 1:
            # Check proprement si le login/mdp est correct
            # Check si personne ne s'est connecte avec cet identifiant
            # deja (utiliser une date de co ?)
            conn.send(b"granted")
        else:
            conn.send(b"forbidden")
        # conn.send(data)  # echo
        time.sleep(0.5)


TCP_IP = '0.0.0.0'
TCP_PORT = 6262
BUFFER_SIZE = 2048  # Normally 1024, but we want fast response


tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind((TCP_IP, TCP_PORT))
threads = []

while True:
    tcpsock.listen(4)
    print("Waiting for incoming connections...")
    (conn, (ip, port)) = tcpsock.accept()
    newthread = ClientThread(ip, port)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
