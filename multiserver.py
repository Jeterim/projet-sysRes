#!/usr/bin/env python
import hashlib
import os
import socket
import time
import hashlib
import acl
from socketserver import ThreadingMixIn  # Python 3
from threading import Thread
from subprocess import Popen, PIPE, run
import shlex
import tempfile
import ssl

data_dict = {"john" : {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "doctor", "lastCo": "1488482763.272476", "connected":False}};

#Init Acl
acli = acl.Acl()
acli.build_acl('permissions.xml')


class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = ""
        print("[+] New thread started for "+ip+":"+str(port))

    def run(self):
        print("test acces : {}".format(acli.check_access('john', 'general', 'w')))
        while True:
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break
            print("received data:", data)

            args = data.split(None)
            if args[0] == "LOGIN":
                self.connect(args)
            elif args[0] == "LOGOUT": #Gestion de la deconnexion
                self.manageConnexion()
            else:
                # TODO Check if dangerous command
                g = tempfile.TemporaryFile(mode='w+')
                run(args,
                    stdout=g,
                    stdin=conn.makefile('r'),
                    stderr=g)
                g.seek(0)
                conn.send(g.read().encode())
                g.close()

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
            self.username = user
            self.updateTime()
            self.manageConnexion()
            # Check proprement si le login/mdp est correct
            # Check si personne ne s'est connecte avec cet identifiant deja (utiliser une date de co ?)
            print(self.username)
            conn.send(b"granted")
        else:
            conn.send(b"forbidden")
        # conn.send(data)  # echo
        time.sleep(0.5)

    def updateTime(self):
        for user in data_dict.keys():
            if user == self.username:
                print("Hello again")
                print(data_dict[user]['lastCo'])
                data_dict[user]['lastCo'] = time.time()
                print("And now it's {}".format(data_dict[user]['lastCo']))

    def manageConnexion(self):
        for user in data_dict.keys():
            if user == self.username:
                print(data_dict[user]['connected'])
                data_dict[user]['connected'] = not data_dict[user]['connected']
                print("And now it's {}".format(data_dict[user]['connected']))


TCP_IP = '0.0.0.0'
TCP_PORT = 6262
BUFFER_SIZE = 2048  # Normally 1024, but we want fast response

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="cert/cert.pem", keyfile="cert/key.pem")


tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind((TCP_IP, TCP_PORT))
threads = []

while True:
    tcpsock.listen(4)
    print("Waiting for incoming connections...")
    (connstream, (ip, port)) = tcpsock.accept()
    conn = context.wrap_socket(connstream,server_side=True)
    newthread = ClientThread(ip, port)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
