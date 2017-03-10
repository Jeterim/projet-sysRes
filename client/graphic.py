import tkinter as tk
from tkinter import ttk
import socket
import hashlib
import time

TCP_IP = '127.0.0.1'
TCP_PORT = 6262
BUFFER_SIZE = 2048


class LoginApp(tk.Frame):
    """
    Login form UI
    """

    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        self.create_connection()

    def create_connection(self):
        """
        Methode de connection au serveur
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(4)
        self.sock.connect((TCP_IP, TCP_PORT))

    def create_widgets(self):
        """
        Creation de l'interface graphique
        """
        self.login = tk.Button(
            self, text="Login", command=self.log_in).pack(side="bottom")
        self.lbl_id = ttk.Label(
            self,
            text="Enter Doctor ID:").pack()
        self.user_id = tk.StringVar()
        self.ent_id = ttk.Entry(
            self,
            textvariable=self.user_id).pack()
        self.lbl_passwd = ttk.Label(self, text="Enter password:").pack()
        self.passwd = tk.StringVar()
        self.ent_passwd = ttk.Entry(
            self,
            textvariable=self.passwd,
            show="*").pack()

    def log_in(self):
        """
        Authentification sur le serveur
        """
        pswdhash = hashlib.sha1(self.passwd.get().encode('utf-8')).hexdigest()
        self.sock.send(bytes("{} {}:{}".format(
            "LOGIN", self.user_id.get(), pswdhash), 'utf-8'))
        time.sleep(0.5)
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        if "granted" in data:
            tentatives, access = 0, 1
            datae = data.split(';')
            # attribution du role pour des actions supplémentaires coté client
            role = datae[1]
            # Destroy window
            self.change_window()
        else:
            tentatives = tentatives - 1

    def change_window(self):
        """
        Tue la fenetre de login et instancie la fenetre principale
        """
        app_app = tk.Tk()
        app_app.title(" Dossier Medical")
        app = MainApp(self.sock, master=app_app)
        main_app.destroy()
        app.mainloop()


class MainApp(tk.Frame):
    """
    Frame principale de l'application
    """

    def __init__(self, sock, master=None):
        super().__init__(master)
        self.pack()
        self.sock = sock
        self.create_widgets()

    def create_widgets(self):
        """
        Creation de l'interface graphique
        """
        self.login = tk.Button(self, text="list files",
                               command=self.list_files).pack()

    def list_files(self):
        """
        Test d'execution d'une commande sur le serveur
        """
        self.sock.send(b"ls")
        time.sleep(0.5)
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(data)


main_app = tk.Tk()
main_app.title("Login Dossier Medical")
app = LoginApp(master=main_app)
app.mainloop()
