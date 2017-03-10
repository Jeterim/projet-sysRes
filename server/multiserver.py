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
import shelve

data_dict = {"john" : {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "doctor", "lastCo": "1488482763.272476", "connected":False}, "johnA" : {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "admin", "lastCo": "1488482763.272476", "connected":False}};

#Init Acl
acli = acl.Acl()
acli.build_acl('permissions.xml')


class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = ""
        self.role = ""
        print("[+] New thread started for "+ip+":"+str(port))

    def run(self):
        print("test acces : {}".format(acli.check_access('john', 'general', 'w')))
        #base = shelve.open('base', 'c')
        #base['john'] = {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "doctor", "lastCo": "1488482763.272476", "connected":False}
        #base['johnA'] = {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "admin", "lastCo": "1488482763.272476", "connected":False}
        #base.close()
        while True:
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break
            print("received data:", data)

            args = data.split(None)
            if args[0] == "LOGIN":
                self.connect(args)
            elif args[0] == "CREATE":
                print("Mon nom c'est : {}".format(self.username))
                if acli.check_access(self.username, 'administration', 'create'):
                    print("Vous avez les acces pour creer une nouvelle personne")
                    #fonction a appeler pour la creation d'une nouvelle personne (dict + acl)
                    conn.send(b"personne cree")
            elif args[0] == "LOGOUT": #Gestion de la deconnexion
                base2 = shelve.open('base')
                self.manageConnexion(base2)
                base2.close()
            else:
                # TODO Check if dangerous command
                run(args,
                    stdout=conn.makefile('w'),
                    stdin=conn.makefile('r'),
                    stderr=conn.makefile('w'))

    def run_command(self, process, args):
        out, err = process.communicate(input=" ".join(args).encode())
        print("{}; {}".format(out.decode('utf-8'), err))
        conn.send(out)

    def connect(self, args):
        auth = args[1].split(":")
        print("Login : {} Password : {}".format(auth[0], auth[1]))
        successauth = 0
        base2 = shelve.open('base')
        if auth[0] in base2 and base2[auth[0]]["password"] == auth[1]:
            print("it's him")
            successauth = 1
        if successauth == 1:
            print("tg")
            self.username = auth[0]
            self.role = base2[auth[0]]["role"]
            self.updateTime(base2)
            print('et la')
            self.manageConnexion(base2)
            # Check proprement si le login/mdp est correct
            # Check si personne ne s'est connecte avec cet identifiant deja (utiliser une date de co ?)
            print(self.username)
            conn.send("granted;{}".format(base2[auth[0]]["role"]).encode())
        else:
            conn.send(b"forbidden")
        # conn.send(data)  # echo
        time.sleep(0.5)
        base2.close()

    def updateTime(self, base2):
        if self.username in base2:
            print(base2[self.username]["lastCo"])
            base2[self.username]["lastCo"] = time.time()
            print("And now it's {}".format(base2[self.username]["lastCo"]))

    def manageConnexion(self, base2):
        if self.username in base2:
            print(base2[self.username]["connected"])
            base2[self.username]["connected"] = not base2[self.username]["connected"]
            print("And now it's {}".format(base2[self.username]["connected"]))


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