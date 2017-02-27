#!/usr/bin/env python

import socket
import time
import getpass
import hashlib

TCP_IP = '127.0.0.1'
TCP_PORT = 6262
BUFFER_SIZE = 2048
MENU = {"LS": "Liste un repertoire",
        "MV": "Se deplacer dans un repertoire", "EXE": "Executer une commande"}


def run():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
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
    tentatives = 3
    access = 0
    while tentatives != 0:
        # login = raw_input("# Login : ")
        login = input("# Login : ")
        passwd = getpass.getpass("# Mot de passe : ")
        # hashage direct du passwd pour ne pas l'envoyer en clair
        pswdhash = hashlib.sha1(passwd.encode('utf-8')).hexdigest()
        # try/except a faire
        print(pswdhash)
        #s.send("{};{}:{}".format("LOGIN", login, pswdhash))
        s.send(bytes("{} {}:{}".format("LOGIN", login, pswdhash), 'utf-8'))
        time.sleep(0.5)
        data = s.recv(BUFFER_SIZE).decode('utf-8')
        print("Le serveur me donne : {}".format(data))
        if data == "granted":
            tentatives = 0
            access = 1
        else:
            tentatives = tentatives - 1
            print(
                "L'autentification a echouee il vous reste {} tentative(s)".format(tentatives))

    val = ""
    while val != "quit" and access == 1:
        print("\n-------------------")
        for menu in MENU:
            print("+ {}       {}".format(menu, MENU[menu]))
        print("-------------------\nTappez quit pour quitter le client\n")
        val = input("Tappez votre commande ")
        s.send(val.encode())
        data = s.recv(BUFFER_SIZE).decode()
        print(data)

        # if val == "LS":
        #     print("Ls a faire")
        #     s.send(b"LS;NULL")
        #     data = s.recv(BUFFER_SIZE).decode()
        #     print("Le serveur me donne : {}".format(data))
        #     listFileS = data.split(", ")
        #     for file in listFileS:
        #         fileS = file.split(";")
        #         print(fileS[0], fileS[1])
        # elif val == "OPEN":
        #     print("OPEN a faire")
        #     fileO = input("Fichier a ouvrir : ")
        #     s.send("OPEN;{}".format(fileO).encode())
        #     data = s.recv(BUFFER_SIZE).decode()
        #     print("Le serveur me donne : {}".format(data))
        # else:
        #     if val != "quit":
        #         print("Commande non reconnue")

    print("Fin du client")
    s.close()

if __name__ == "__main__":
    run()
