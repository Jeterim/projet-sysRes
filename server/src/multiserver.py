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
import ast

#Init Acl
acl = acl.Acl()

# Ouverture sauvegarde des acl
with open('sauvAcl.json', "r") as file:
    content = file.read()
    user = {}
    user = ast.literal_eval(content)

    acl.__setstate__(user)



# initAcl() # Si on a besoin d'un reset d'acl
# saveAcl() # Sauvegarde pour les changements importants

def saveAcl():
    save = acl.__getstate__()
    print(save)
    with open('sauvAcl.json', "w") as file:
        file.write(str(save))

def initAcl():
    acl.add_roles(['admin', 'doctor', 'employee'])
    acl.add({
        'general': {'r', 'w', 'x'},
        'adminAction': {'create', 'edit', 'delete'},
    })

    acl.grants({
    'admin': {
        'adminAction': ['create', 'edit', 'delete'],
    },
    'doctor': {
        'general': ['x']
    }
})

class ClientThread(Thread):

    def __init__(self, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.username = ""
        self.role = ""
        print("[+] New thread started for "+ip+":"+str(port))
        # Temporary
        self.original_dir = os.getcwd()
        self.current_dir = os.path.abspath('general')
        self.has_changed_dir = False

    def update_dir(self):
        if self.original_dir != self.current_dir:
            os.chdir(self.original_dir)
        self.has_changed_dir = False

    def run(self):
        db = records.Database('sqlite:///users.db')
        # if self.has_changed_dir == 0:
        #     os.chdir('general')
        #     self.has_changed_dir = 1


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
        """ treat what is send from the graphic client """
        if args[1] == "modify":
            data = conn.recv(int(args[3]) + 1).decode('utf-8') # Recoit le fichier
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
        elif args[1] == "ls":
            self.list_dir()
        elif args[1] == "chdir":
            if args[2] != "..":
                self.current_dir = os.path.abspath(args[2])
            else:
                self.current_dir = os.path.abspath(os.path.join(self.current_dir, os.pardir))

    def list_dir(self):
        print("PATH : {}".format(self.current_dir))
        file_list = os.listdir(self.current_dir)
        conn.send(",".join(file_list).encode())

    def send_file(self, file):
        """ Take a file and send it through the socket"""
        file.seek(0, 2) # Seek end of file
        length = file.tell()
        print(length)
        conn.send(str(length).encode())
        time.sleep(0.5)
        file.seek(0, 0)
        content = file.read()
        print(content)
        conn.send(str(content).encode())

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
            print(self.role, acl.check(self.role, 'general', 'r'))
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