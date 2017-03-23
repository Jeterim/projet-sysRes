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
import records
import tempfile
import ssl
import tempfile

import miracle

data_dict = {"john" : {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "doctor", "lastCo": "1488482763.272476", "connected":False}, "johnA" : {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "admin", "lastCo": "1488482763.272476", "connected":False}};

#Init Acl
#acli = acl.Acl()
#acli.build_acl('permissions.xml')
acl = miracle.Acl()
acl.add_roles(['admin', 'doctor', 'employee'])
acl.add({
    'general': {'r', 'w', 'x'},
    'adminAction': {'create', 'edit', 'delete'},
})
print(acl.check('admin', 'adminAction', 'edit'))
acl.grant('admin', 'adminAction', 'create')
acl.grant('admin', 'adminAction', 'edit')
acl.grant('admin', 'adminAction', 'delete')
print(acl.check('admin', 'adminAction', 'edit'))

save = acl.__getstate__()
print(save)




class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = ""
        self.role = ""
        print("[+] New thread started for "+ip+":"+str(port))

    def run(self):
        db = records.Database('sqlite:///users.db')

        #Si besoin de re-clean la bdd
        #self.init_db(db)

        rows = db.query('SELECT * FROM persons')
        for _r in rows:
            print(_r.key, _r.name, _r.role, _r.connected, not _r.connected, _r.deleted)
        while True:
            data = conn.recv(2048).decode('utf-8')
            if not data:
                break
            print("received data:", data)

            args = data.split(None)
            print(args)
            if args[0] == "LOGIN":
                self.connect(args, db)
            elif args[0] == "CREATEUSR":
                print("Mon nom c'est : {}".format(self.username))
                if acl.check(self.role, 'adminAction', 'create'):
                    print("Vous avez les acces pour creer une nouvelle personne")

                    #fonction a appeler pour la creation d'une nouvelle personne (dict + acl)
                    insert = args[1].split(':')

                    if db.query('SELECT key FROM persons WHERE name="{}"'.format(insert[0])).first() == None:
                        print("creation accepted")
                        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected, deleted) VALUES(NULL, :name, :password, :role, :lastCo, :connected, :deleted)',
                            name=insert[0], password=insert[1], role=insert[2], lastCo=time.time(), connected=False, deleted=False)
                        conn.send(b"personne cree")
                    else:
                        conn.send(b"echec creation")

            elif args[0] == "EDITUSR":
                print("Mon nom c'est : {}".format(self.username))
                print(self.role, acl.check(self.role, 'adminAction', 'edit'))
                print(acl.get_roles())
                if acl.check(self.role, 'adminAction', 'edit'):
                    print("Vous avez les acces pour editer une personne")

                    #fonction a appeler pour la creation d'une nouvelle personne (dict + acl)
                    edit = args[1].split(':')
                    if db.query('SELECT key FROM persons WHERE name="{}" and deleted=0'.format(edit[0])).first() != None:
                        print("edition accepted")
                        db.query('UPDATE persons SET password=:password, role=:role WHERE name=:name',
                            password=edit[1], role=edit[2], name=edit[0])
                        conn.send(b"personne updated")
                    else:
                        conn.send(b"echec update")

            elif args[0] == "DELUSR":
                print("Mon nom c'est : {}".format(self.username))
                if acl.check(self.role, 'adminAction', 'delete'):
                    print("Vous avez les acces pour supprimer une personne")

                    #fonction a appeler pour la creation d'une nouvelle personne (dict + acl)
                    if db.query('SELECT key FROM persons WHERE name="{}" and deleted=0'.format(args[1])).first() != None and args[1] != self.username:
                        print("deletion accepted")
                        db.query('UPDATE persons SET deleted=1 WHERE name="{}"'.format(args[1]))
                        conn.send(b"personne deleted")
                    else:
                        conn.send(b"echec delete")
            elif args[0] == "NULLUSR":
                conn.send(b"no action")

            elif args[0] == "LOGOUT": #Gestion de la deconnexion
                self.manageConnexion(db)
            elif args[0] == "Graphique":
                self.graphic_features(args)
            else:
                # TODO Check if dangerous command
                self.execute_command(args)

    def graphic_features(self, args):
        if args[1] == "modify":
            print("je suis la ")
            data = conn.recv(int(args[3]) + 1).decode('utf-8')
            print(data)
            with open(args[2], "w") as file:
                file.writelines(data)

    def execute_command(self, args):
        """
        Execute a command from the client on the server and send output to client
        """
        temp_file = tempfile.TemporaryFile(mode='w+')
        run(args,
            stdout=temp_file,
            stdin=conn.makefile('r'),
            stderr=temp_file)
        temp_file.seek(0)
        conn.send(temp_file.read().encode())
        temp_file.close()

    def init_db(self, db):
        db.query('DROP TABLE IF EXISTS persons')
        db.query('CREATE TABLE persons (key INTEGER PRIMARY KEY, name TEXT UNIQUE, password text, role text, lastCo text, connected bool, deleted bool)')

        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected, deleted) VALUES(:key, :name, :password, :role, :lastCo, :connected, :deleted)',
                    key="1", name="john", password="d6b4e84ee7f31d88617a6b60421451272ebf1a3a", role="doctor", lastCo="1488482763.272476", connected=False, deleted=False)
        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected, deleted) VALUES(:key, :name, :password, :role, :lastCo, :connected, :deleted)',
                    key="2", name="johnA", password="d6b4e84ee7f31d88617a6b60421451272ebf1a3a", role="admin", lastCo="1488482763.272476", connected=False, deleted=False)

    def run_command(self, process, args):
        out, err = process.communicate(input=" ".join(args).encode())
        print("{}; {}".format(out.decode('utf-8'), err))
        conn.send(out)

    def connect(self, args, db):
        auth = args[1].split(":")
        print("Login : {} Password : {}".format(auth[0], auth[1]))
        row = db.query('SELECT password, role FROM persons WHERE name="{}" and deleted=0'.format(auth[0])).first()
        print("Ma requete me donne : {}".format(row))
        #Trouver un moyen de savoir si ce nom existe avant la condition 
        if row and row.password == auth[1]: #Authentifie
            print("it's him")
            print(row.password, row.role)
            self.username = auth[0]
            self.role = row.role
            self.updateTime(db)
            self.manageConnexion(db)
            # Check proprement si le login/mdp est correct
            # Check si personne ne s'est connecte avec cet identifiant deja (utiliser une date de co ?)
            print(self.username)
            conn.send("granted;{}".format(row.role).encode())
        else:
            conn.send(b"forbidden")
        # conn.send(data)  # echo
        time.sleep(0.5)

    def updateTime(self, db):
        row = db.query('SELECT lastCo FROM persons WHERE name="{}" and deleted=0'.format(self.username)).first()
        print(row.lastCo)
        db.query('UPDATE persons SET lastCo=:lastCo WHERE name=:name', lastCo=time.time(), name=self.username)
        row = db.query('SELECT lastCo FROM persons WHERE name="{}" and deleted=0'.format(self.username)).first()
        print("And now it's {}".format(row.lastCo))

    def manageConnexion(self, db):
        row = db.query('SELECT connected FROM persons WHERE name="{}" and deleted=0'.format(self.username)).first()
        print(row.connected, not row.connected, type(not row.connected))
        db.query('UPDATE persons SET connected=:connected WHERE name=:name', connected=not row.connected, name=self.username)
        row = db.query('SELECT connected FROM persons WHERE name="{}" and deleted=0'.format(self.username)).first()
        print("And now it's {} / {}".format(row.connected, type(row.connected)))


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
    conn = context.wrap_socket(connstream, server_side=True)
    newthread = ClientThread(ip, port)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()