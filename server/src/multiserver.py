#!/usr/bin/env python
import hashlib
import os
import sys
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
import pickle
from PIL import Image, ImageTk

data_dict = {"john": {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "doctor", "lastCo": "1488482763.272476", "connected": False},
             "johnA": {"password": "d6b4e84ee7f31d88617a6b60421451272ebf1a3a", "role": "admin", "lastCo": "1488482763.272476", "connected": False}}

# Init Acl
acli = acl.Acl()
acli.build_acl('permissions.xml')


class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = ""
        self.role = ""
        print("[+] New thread started for " + ip + ":" + str(port))
        # Temporary
        self.original_dir = os.getcwd()
        self.current_dir = os.path.abspath('general')
        self.has_changed_dir = False

    def update_dir(self):
        if self.original_dir != self.current_dir:
            os.chdir(self.original_dir)
        self.has_changed_dir = False

    def run(self):
        print("test acces : {}".format(acli.check_access('john', 'general', 'w')))

        db = records.Database('sqlite:///users.db')
        # if self.has_changed_dir == 0:
        #     os.chdir('general')
        #     self.has_changed_dir = 1

        # Si besoin de re-clean la bdd
        # self.init_db(db)

        rows = db.query('SELECT * FROM persons')
        for _r in rows:
            print(_r.key, _r.name, _r.role, _r.connected, not _r.connected)
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
                if acli.check_access(self.username, 'administration', 'create'):
                    print("Vous avez les acces pour creer une nouvelle personne")

                    # fonction a appeler pour la creation d'une nouvelle
                    # personne (dict + acl)
                    insert = args[1].split(':')

                    if db.query('SELECT key FROM persons WHERE name="{}"'.format(insert[0])).first() == None:
                        print("creation accepted")
                        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected) VALUES(NULL, :name, :password, :role, :lastCo, :connected)',
                                 name=insert[0], password=insert[1], role=insert[2], lastCo=time.time(), connected=False)
                        conn.send(b"personne cree")
                    else:
                        conn.send(b"echec creation")

            elif args[0] == "EDITUSR":
                print("Mon nom c'est : {}".format(self.username))
                if acli.check_access(self.username, 'administration', 'edit'):
                    print("Vous avez les acces pour editer une personne")

                    # fonction a appeler pour la creation d'une nouvelle
                    # personne (dict + acl)
                    edit = args[1].split(':')
                    if db.query('SELECT key FROM persons WHERE name="{}"'.format(edit[0])).first() != None:
                        print("edition accepted")
                        db.query('UPDATE persons SET password=:password, role=:role WHERE name=:name',
                                 password=edit[1], role=edit[2], name=edit[0])
                        conn.send(b"personne updated")
                    else:
                        conn.send(b"echec update")

            elif args[0] == "LOGOUT":  # Gestion de la deconnexion
                self.manageConnexion(db)
            elif args[0] == "Graphique":
                self.graphic_features(args)
            else:
                # TODO Check if dangerous command
                self.execute_command(args)

    def graphic_features(self, args):
        """ treat what is send from the graphic client """
        if args[1] == "modify":
            # Recoit le fichier
            data = conn.recv(int(args[3]) + 1).decode('utf-8')
            print(data)
            path = "{}/{}".format(self.current_dir, args[2])
            print(path)
            with open(path, "w") as file:
                file.writelines(data)
        elif args[1] == "print":
            path = "{}/{}".format(self.current_dir, args[2])
            if os.path.isdir(path):
                self.current_dir = path
                conn.send(b"Directory")
            else:
                try:
                    with open(path, 'r') as file:
                        self.send_file(file)
                except FileNotFoundError:
                    conn.send(b"NotFound")
        elif args[1] == "printimg":
            path = "{}/{}".format(self.current_dir, args[2])
            if os.path.isdir(path):
                self.current_dir = path
                conn.send(b"Directory")
            else:
                try:
                    image = Image.open(path)
                    self.send_img(image)
                except FileNotFoundError:
                    conn.send(b"NotFound")
        elif args[1] == "ls":
            self.list_dir()
        elif args[1] == "chdir":
            if args[2] != "..":
                self.current_dir = os.path.abspath(args[2])
            else:
                tmp_dir = os.path.abspath(
                    os.path.join(self.current_dir, os.pardir))
                if len(tmp_dir.split("/")) > len(self.original_dir.split("/")):
                    self.current_dir = tmp_dir
                    conn.send(b"OK /")
                else:
                    conn.send(b"Err /")
        elif args[1] == "delete":
            file = "{}/{}".format(self.current_dir, args[2])
            print(file)
            os.remove(file)
            conn.send(b"OK")
        elif args[1] == "mkdir":
            os.mkdir(args[2])

    def list_dir(self):
        print("PATH : {}".format(self.current_dir))
        file_list = os.listdir(self.current_dir)
        conn.send(",".join(file_list).encode())

    def send_file(self, file):
        """ Take a file and send it through the socket"""
        file.seek(0, 2)  # Seek end of file
        length = file.tell()
        print(length)
        conn.send(str(length).encode())
        time.sleep(0.5)
        file.seek(0, 0)
        content = file.read()
        print(content)
        conn.send(str(content).encode())

    def send_img(self, file):
        """ Take a img and send it through the socket"""
        imageDict = {'imageFile': file, 'user': 'test'}
        pickleData = pickle.dumps(imageDict)
        taille = sys.getsizeof(pickleData)
        print("Taille : {}".format(taille))
        conn.send(str(taille).encode())
        conn.send(pickleData)
        #conn.send(str(content).encode())

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
        db.query('CREATE TABLE persons (key INTEGER PRIMARY KEY, name TEXT UNIQUE, password text, role text, lastCo text, connected bool)')

        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected) VALUES(:key, :name, :password, :role, :lastCo, :connected)',
                 key="1", name="john", password="d6b4e84ee7f31d88617a6b60421451272ebf1a3a", role="doctor", lastCo="1488482763.272476", connected=False)
        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected) VALUES(:key, :name, :password, :role, :lastCo, :connected)',
                 key="2", name="johnA", password="d6b4e84ee7f31d88617a6b60421451272ebf1a3a", role="admin", lastCo="1488482763.272476", connected=False)

    def run_command(self, process, args):
        out, err = process.communicate(input=" ".join(args).encode())
        print("{}; {}".format(out.decode('utf-8'), err))
        conn.send(out)

    def connect(self, args, db):
        auth = args[1].split(":")
        print("Login : {} Password : {}".format(auth[0], auth[1]))
        row = db.query(
            'SELECT password, role FROM persons WHERE name="{}"'.format(auth[0])).first()
        print("Ma requete me donne : {}".format(row))
        # Trouver un moyen de savoir si ce nom existe avant la condition
        if row and row.password == auth[1]:  # Authentifie
            print("it's him")
            print(row.password, row.role)
            self.username = auth[0]
            self.role = row.role
            self.updateTime(db)
            self.manageConnexion(db)
            # Check proprement si le login/mdp est correct
            # Check si personne ne s'est connecte avec cet identifiant deja
            # (utiliser une date de co ?)
            print(self.username)
            conn.send("granted;{}".format(row.role).encode())
        else:
            conn.send(b"forbidden")
        # conn.send(data)  # echo
        time.sleep(0.5)

    def updateTime(self, db):
        row = db.query('SELECT lastCo FROM persons WHERE name="{}"'.format(
            self.username)).first()
        print(row.lastCo)
        db.query('UPDATE persons SET lastCo=:lastCo WHERE name=:name',
                 lastCo=time.time(), name=self.username)
        row = db.query('SELECT lastCo FROM persons WHERE name="{}"'.format(
            self.username)).first()
        print("And now it's {}".format(row.lastCo))

    def manageConnexion(self, db):
        row = db.query('SELECT connected FROM persons WHERE name="{}"'.format(
            self.username)).first()
        print(row.connected, not row.connected, type(not row.connected))
        db.query('UPDATE persons SET connected=:connected WHERE name=:name',
                 connected=not row.connected, name=self.username)
        row = db.query('SELECT connected FROM persons WHERE name="{}"'.format(
            self.username)).first()
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
