#!/usr/bin/env python
import os
import socket
import time
import getpass
import hashlib
import ssl

TCP_IP = '127.0.0.1'
TCP_PORT = 6262
BUFFER_SIZE = 2048
MENU = {"": ""}


def run():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    context.load_verify_locations(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert/cert.pem"))
    s = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    s.settimeout(4)
    s.connect((TCP_IP, TCP_PORT))
    cert = s.getpeercert()
    print("                    _ _           _ ")
    print(" _ __ ___   ___  __| (_) ___ __ _| |")
    print("| '_ ` _ \ / _ \/ _` | |/ __/ _` | |")
    print("| | | | | |  __/ (_| | | (_| (_| | |")
    print("|_| |_| |_|\___|\__,_|_|\___\__,_|_|")
    print("")
    print("-----------------------------------------------------------------------")
    print("---- Bienvenue sur le service de consultation de dossiers medicaux ----")
    print("-----------------------------------------------------------------------")
    print("Pour y acceder veuillez vous identifier")
    tentatives, access = 3, 0
    while tentatives != 0:
        # login = raw_input("# Login : ")
        login = input("# Login : ")
        passwd = getpass.getpass("# Mot de passe : ")
        # hashage direct du passwd pour ne pas l'envoyer en clair
        pswdhash = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
        # try/except a faire
        print(pswdhash)
        s.send(bytes("{} {}:{}".format("LOGIN", login, pswdhash), 'utf-8'))
        time.sleep(0.5)
        data = s.recv(BUFFER_SIZE).decode('utf-8')
        print("Le serveur me donne : {}".format(data))
        if "granted" in data:
            tentatives = 0
            access = 1
            datae = data.split(';')
            role = datae[1] #attribution du role pour des actions supplémentaires coté client
        else:
            tentatives = tentatives - 1
            print(
                "L'autentification a echouee il vous reste {} tentative(s)"
                .format(tentatives))
    val = ""
    while val != "quit" and access == 1:
        print("-------------------\nTappez quit pour quitter le client\n")
        print(role)
        if role == "admin":
            print("Tu as des acces supplementaires")
            time.sleep(.5)
            euname = input("# Login : ")
            eupasswd = getpass.getpass("# Mot de passe : ")
            eurole = input("# Role : ")
            # hashage direct du passwd pour ne pas l'envoyer en clair
            eupswdhash = hashlib.sha1(eupasswd.encode('utf-8')).hexdigest()
            #s.send(bytes("CREATEUSR {}:{}:{}".format(nuname, nupswdhash, nurole), 'utf-8'))

            s.send(bytes("EDITUSR {}:{}:{}".format(euname, eupswdhash, eurole), 'utf-8'))
            print("envoye")
            data = s.recv(BUFFER_SIZE).decode()
            print("Je recois {}".format(data))
        val = input("Tappez votre commande: > ")
        if val == "quit":
             #Gestion de la déconnexion
            s.send("LOGOUT NULL".encode())
            s.close()
            print("Sayonara !! ")
            break

        s.send(val.encode())
        try:
            if val.startswith('vi') or val.startswith('nano'):
                data = s.recv(BUFFER_SIZE).decode()
                while data:
                    print(data)
                    data = s.recv(BUFFER_SIZE).decode()
            else:
                data = s.recv(BUFFER_SIZE).decode()
                print(data)
        except socket.timeout:
            print("Command has no output")


if __name__ == "__main__":
    run()