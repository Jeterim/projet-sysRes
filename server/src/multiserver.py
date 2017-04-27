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
import records
import tempfile
import ssl
import tempfile
import pickle
from PIL import Image, ImageTk
import ast

# Init Acl
acl = acl.Acl()

# Ouverture sauvegarde des acl
with open('sauvAcl.json', "r") as file:
    content = file.read()
    user = {}
    user = ast.literal_eval(content)

    acl.__setstate__(user)


def initAcl():
    acl.add_roles(['admin', 'doctor', 'psychiatrist', 'physiotherapist', 'nurse'])
    acl.add({
        # Dossiers racine
        'Psy': {'r', 'w', 'x'},
        'kiné': {'r', 'w', 'x'},
        'general': {'r', 'w', 'x'},
        # Dossiers patients
        'Bruce_Lee': {'r', 'w', 'x'},
        'Janine_Michu': {'r', 'w', 'x'},
        'John_Doe': {'r', 'w', 'x'},
        'Yves_Tedescon': {'r', 'w', 'x'},
        # Autre
        'adminAction': {'create', 'edit', 'delete', 'modify'},
    })

    acl.grants({
        'admin': {
            'adminAction': ['create', 'edit', 'delete', 'modify'],
            'general': ['r', 'w', 'x'],
            'Psy': ['r', 'w', 'x'],
            'kiné': ['r', 'w', 'x'],
            'Bruce_Lee': ['r', 'w', 'x'],
            'Janine_Michu': ['r', 'w', 'x'],
            'John_Doe': ['r', 'w', 'x'],
            'Yves_Tedescon': ['r', 'w', 'x']
        },
        'doctor': {
            'general': ['r'],
            'Medecine': {'r', 'w', 'x'},
        },
        'psychiatrist': {
            'general': ['r'],
            'Psy': ['r', 'w', 'x'],
            'Bruce_Lee': ['r', 'w', 'x'],
            'Janine_Michu': ['r', 'w', 'x'],
            'John_Doe': ['r', 'w', 'x'],
            'Yves_Tedescon': ['r', 'w', 'x']
        },
        'physiotherapist': {
            'general': ['r'],
            'kiné': ['r', 'w', 'x'],
        },
        'nurse': {
            'general': ['r'],
            'Psy': ['r', 'x'],
            'Bruce_Lee': ['r', 'x'],
            'Janine_Michu': ['r', 'x'],
            'John_Doe': ['r', 'x'],
            'Yves_Tedescon': ['r', 'x'],
            'kiné': ['r', 'x'],
            'Medecine': ['r', 'x'],
        }

    })


def saveAcl():
    save = acl.__getstate__()
    with open('sauvAcl.json', "w") as file:
        file.write(str(save))

# initAcl() # Si on a besoin d'un reset d'acl
saveAcl()  # Sauvegarde pour les changements importants


class ClientThread(Thread):

    def __init__(self, ip, port, ClientSocket):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.client_socket = ClientSocket
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
        db = records.Database('sqlite:///users.db')
        # if self.has_changed_dir == 0:
        #     os.chdir('general')
        #     self.has_changed_dir = 1

        # Si besoin de re-clean la bdd
        # self.init_db(db)

        rows = db.query('SELECT * FROM persons')
        for _r in rows:
            print(_r.key, _r.name, _r.role, _r.connected,
                  not _r.connected, _r.deleted)
        while True:
            data = self.client_socket.recv(2048).decode('utf-8')
            if not data:
                break
            print("received data:", data)

            args = data.split(None)
            print(args)
            if args[0] == "LOGIN":
                self.connect(args, db)
            elif args[0] == "CREATEUSR":
                if acl.check(self.role, 'adminAction', 'create'):
                    print("Vous avez les acces pour creer une nouvelle personne")

                    insert = args[1].split(':')

                    if db.query('SELECT key FROM persons WHERE name=:name', name=insert[0]).first() == None:
                        print("creation accepted")
                        db.query('INSERT INTO persons (key, name, password, role, lastCo, connected, deleted) VALUES(NULL, :name, :password, :role, :lastCo, :connected, :deleted)',
                                 name=insert[0], password=insert[1], role=insert[2], lastCo=time.time(), connected=False, deleted=False)
                        self.client_socket.send(b"personne cree")
                    else:
                        self.client_socket.send(b"echec creation")

            elif args[0] == "EDITUSR":
                print(self.role, acl.check(self.role, 'adminAction', 'edit'))

                print(acl.get_roles())
                if acl.check(self.role, 'adminAction', 'edit'):
                    print("Vous avez les acces pour editer une personne")

                    edit = args[1].split(':')
                    if db.query('SELECT key FROM persons WHERE name=:name and deleted=0', name=edit[0]).first() != None:
                        print("edition accepted")
                        db.query('UPDATE persons SET password=:password, role=:role WHERE name=:name',
                                 password=edit[1], role=edit[2], name=edit[0])
                        self.client_socket.send(b"personne updated")
                    else:
                        self.client_socket.send(b"echec update")

            elif args[0] == "DELUSR":
                if acl.check(self.role, 'adminAction', 'delete'):
                    print("Vous avez les acces pour supprimer une personne")

                    if db.query('SELECT key FROM persons WHERE name=:name and deleted=0', name=args[1]).first() != None and args[1] != self.username:
                        print("deletion accepted")
                        db.query(
                            'UPDATE persons SET deleted=1 WHERE name=:name', name=args[1])
                        self.client_socket.send(b"personne deleted")
                    else:
                        self.client_socket.send(b"echec delete")

            elif args[0] == "MODIFYACL":
                print("Mon nom c'est : {}".format(self.username))
                if acl.check(self.role, 'adminAction', 'modify'):
                    if args[1] == "grant" and (acl.check(args[2], args[3], args[4]) != True):
                        if args[2] in acl.get_roles() and args[3] in acl.get_resources() and args[4] in acl.get_permissions(args[3]):
                            acl.grant(args[2], args[3], args[4])
                            self.client_socket.send(b"grant succeed")
                        else:
                            self.client_socket.send(b"grant failed")
                    elif args[1] == "revoke" and (acl.check(args[2], args[3], args[4]) == True):
                        print("pret pour revoke", acl.get_resources())
                        if args[2] in acl.get_roles() and args[3] in acl.get_resources() and args[4] in acl.get_permissions(args[3]):
                            acl.revoke(args[2], args[3], args[4])
                            self.client_socket.send(b"revoke succeed")
                        else:
                            self.client_socket.send(b"revoke failed")
                else:
                    print("Erreur")
                    self.client_socket.send(
                        b"failed wrong arguments or access")
                saveAcl()
            elif args[0] == "NULLUSR":
                self.client_socket.send(b"no action")

            elif args[0] == "LOGOUT":  # Gestion de la deconnexion
                self.manageConnexion(db)
            elif args[0] == "Graphique":
                self.graphic_features(args)
            else:
                # TODO Check if dangerous command
                # self.execute_command(args)
                print("Commande non reconnue")

    def graphic_features(self, args):
        """ treat what is send from the graphic client """
        if args[1] == "modify":
            # Recoit le fichier
            data = self.client_socket.recv(int(args[3]) + 1).decode('utf-8')
            path = "{}/{}".format(self.current_dir, args[2])
            if acl.check(self.role, os.path.basename(self.current_dir), 'w'):
                with open(path, "w") as file:
                    file.writelines(data)
            else:
                print("Erreur acces")
        elif args[1] == "print":
            path = "{}/{}".format(self.current_dir, args[2])
            if os.path.isdir(path):
                if acl.check(self.role, args[2], 'x'):
                    self.current_dir = path
                    self.client_socket.send(b"Directory")
                else:
                    self.client_socket.send(b"AccessError")
            else:
                if acl.check(self.role, os.path.basename(self.current_dir), 'r'):
                    try:
                        with open(path, 'r') as file:
                            self.send_file(file)
                    except FileNotFoundError:
                        self.client_socket.send(b"NotFound")
                else:
                    print("Erreur acces")
                    self.client_socket.send(b"AccessError")
        elif args[1] == "printimg":
            path = "{}/{}".format(self.current_dir, args[2])
            if os.path.isdir(path):
                self.current_dir = path
                self.client_socket.send(b"Directory")
            else:
                if acl.check(self.role, os.path.basename(self.current_dir), 'r'):
                    try:
                        image = Image.open(path)
                        self.send_img(image)
                    except FileNotFoundError:
                        self.client_socket.send(b"NotFound")
                else:
                    print("Erreur acces")
                    self.client_socket.send(b"AccessError")
        elif args[1] == "ls":
            self.list_dir()
        elif args[1] == "chdir":
            print("Le dir {}".format(args[2]))
            if args[2] != "..":
                if acl.check(self.role, os.path.basename(args[2]), 'x'):
                    self.current_dir = os.path.abspath(args[2])
                else:
                    print("Erreur Acces")
            else:
                tmp_dir = os.path.abspath(
                    os.path.join(self.current_dir, os.pardir))
                if len(tmp_dir.split("/")) > len(self.original_dir.split("/")):
                    self.current_dir = tmp_dir
                    self.client_socket.send(b"OK /")
                else:
                    self.client_socket.send(b"Err /")
        elif args[1] == "delete":
            file = "{}/{}".format(self.current_dir, args[2])
            print(file)
            if acl.check(self.role, os.path.basename(args[2]), 'w'):
                if os.path.isdir(file):
                    if os.listdir(file) == []:
                        os.removedirs(file)
                    else:
                        self.client_socket.send(
                            "Error directory not empty".encode())
                else:
                    os.remove(file)
                    self.client_socket.send(b"OK")
                acl.revoke_all(self.role, args[2])
                saveAcl()
            else:
                self.client_socket.send(b"AccessError")
        elif args[1] == "mkdir":
            if acl.check(self.role, args[2], 'w'):
                path = "{}/{}".format(self.current_dir, args[2])
                os.mkdir(path)
                self.client_socket.send("OK".encode())

                acl.add({
                    args[2]: {'r', 'w', 'x'},
                })
                acl.grants({
                    self.role: {
                        args[2]: ['r', 'w', 'x']
                    },
                    'admin': {
                        args[2]: ['r', 'w', 'x']
                    }
                })
                saveAcl()
            else:
                print("Erreur Acces")
        elif args[1] == "touch":
            if acl.check(self.role, args[2], 'w'):
                path = "{}/{}".format(self.current_dir, args[2])
                file = open(path, 'w+')
                self.client_socket.send("OK".encode())
            else:
                self.client_socket.send("AccessError".encode())

    def list_dir(self):
        print("PATH : {}".format(self.current_dir))
        file_list = os.listdir(self.current_dir)
        print(file_list)
        if file_list == []:
            self.client_socket.send("Empty".encode())
        else:
            self.client_socket.send(",".join(file_list).encode())

    def send_file(self, file):
        """ Take a file and send it through the socket"""
        file.seek(0, 2)  # Seek end of file
        length = file.tell()
        print(length)
        self.client_socket.send(str(length).encode())
        if length > 0:
            time.sleep(0.5)
            file.seek(0, 0)
            content = file.read()
            print(content)
            self.client_socket.send(str(content).encode())

    def send_img(self, file):
        """ Take a img and send it through the socket"""
        imageDict = {'imageFile': file, 'user': 'test'}
        pickleData = pickle.dumps(imageDict)
        taille = sys.getsizeof(pickleData)
        print("Taille : {}".format(taille))
        self.client_socket.send(str(taille).encode())
        self.client_socket.send(pickleData)
        # self.client_socket.send(str(content).encode())

    def execute_command(self, args):
        """
        Execute a command from the client on the server and send output to client
        """
        temp_file = tempfile.TemporaryFile(mode='w+')
        run(args,
            stdout=temp_file,
            stdin=self.client_socket.makefile('r'),
            stderr=temp_file)
        temp_file.seek(0)
        self.client_socket.send(temp_file.read().encode())
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
        self.client_socket.send(out)

    def connect(self, args, db):
        auth = args[1].split(":")
        print("Login : {} Password : {}".format(auth[0], auth[1]))
        row = db.query(
            'SELECT password, role FROM persons WHERE name=:name and deleted=0', name=auth[0]).first()

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
            print(self.role, acl.check(self.role, 'general', 'r'))
            self.client_socket.send("granted;{}".format(row.role).encode())
        else:
            self.client_socket.send(b"forbidden")
        # self.client_socket.send(data)  # echo
        time.sleep(0.5)

    def updateTime(self, db):
        row = db.query(
            'SELECT lastCo FROM persons WHERE name=:name and deleted=0', name=self.username).first()
        print(row.lastCo)
        db.query('UPDATE persons SET lastCo=:lastCo WHERE name=:name',
                 lastCo=time.time(), name=self.username)
        row = db.query(
            'SELECT lastCo FROM persons WHERE name=:name and deleted=0', name=self.username).first()
        print("And now it's {}".format(row.lastCo))

    def manageConnexion(self, db):
        row = db.query(
            'SELECT connected FROM persons WHERE name=:name and deleted=0', name=self.username).first()
        print(row.connected, not row.connected, type(not row.connected))
        db.query('UPDATE persons SET connected=:connected WHERE name=:name',
                 connected=not row.connected, name=self.username)
        row = db.query(
            'SELECT connected FROM persons WHERE name=:name and deleted=0', name=self.username).first()

        print("And now it's {} / {}".format(row.connected, type(row.connected)))


if len(sys.argv) == 2:
    TCP_PORT = int(sys.argv[1])
else:
    TCP_PORT = 6262

TCP_IP = '0.0.0.0'
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
    newthread = ClientThread(ip, port, conn)
    newthread.start()
    threads.append(newthread)

for t in threads:
    t.join()
