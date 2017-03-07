#!/usr/bin/env python

import socket
import time
import getpass
import hashlib
import pyOpenSSL
import ssl 

TCP_IP = '127.0.0.1'
TCP_PORT = 6262
BUFFER_SIZE = 2048
MENU = {"LS":"Liste un repertoire", "MV":"Se deplacer dans un repertoire", "EXE":"Executer une commande"}

def run():
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    context.load_verify_locations("/etc/ssl/certs/cert.pem")
    connstream = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    connstream.connect((TCP_IP, TCP_PORT))
    cert = connstream.getpeercert()
    print ("                    _ _           _ ")
    print (" _ __ ___   ___  __| (_) ___ __ _| |")
    print ("| '_ ` _ \ / _ \/ _` | |/ __/ _` | |")
    print ("| | | | | |  __/ (_| | | (_| (_| | |")
    print ("|_| |_| |_|\___|\__,_|_|\___\__,_|_|")
    print ("")
    print ("-----------------------------------------------------------------------")
    print ("---- Bienvenue sur le service de consultation de dossiers medicaux ----")
    print ("-----------------------------------------------------------------------")
    print ("Pour y acceder veuillez vous identifier")
    tentatives = 3
    access = 0
    while tentatives != 0:
        #login = raw_input("# Login : ")
        login = input("# Login : ")
        passwd = getpass.getpass("# Mot de passe : ")
        pswdhash = hashlib.sha1(passwd.encode('utf-8')).hexdigest() #hashage direct du passwd pour ne pas l'envoyer en clair
        #try/except a faire
        print(pswdhash)
        #s.send("{};{}:{}".format("LOGIN", login, pswdhash))
        connstream.send(bytes("{};{}:{}".format("LOGIN", login, pswdhash), 'utf-8'))
        time.sleep(0.5)
        data = connstream.recv(BUFFER_SIZE).decode('utf-8')
        print ("Le serveur me donne : {}".format(data))
        if data == "granted":
            tentatives = 0
            access = 1
        else:
            tentatives = tentatives - 1
            print ("L'autentification a echouee il vous reste {} tentative(s)".format(tentatives))




    val = ""
    while val != "quit" and access == 1:
        print ("\n-------------------")
        for menu in MENU:
            print ("+ {}       {}".format(menu, MENU[menu]))
        print ("-------------------\nTappez quit pour quitter le client\n")
        val = input("Tappez votre commande ")

        if val == "LS":
            print ("Ls a faire")
            connstream.send(b"LS;NULL")
            data = connstream.recv(BUFFER_SIZE).decode()
            print ("Le serveur me donne : {}".format(data))
            listFileS = data.split(", ")
            for file in listFileS:
                fileS = file.split(";")
                print (fileS[0], fileS[1])
        elif val == "OPEN":
            print ("OPEN a faire")
            fileO = input("Fichier a ouvrir : ")
            connstream.send("OPEN;{}".format(fileO).encode())
            data = connstream.recv(BUFFER_SIZE).decode()
            print ("Le serveur me donne : {}".format(data))
        else:
            if val != "quit":
                print ("Commande non reconnue")

    print ("Fin du client")
    connstream.close()

if __name__ == "__main__":
    run()
