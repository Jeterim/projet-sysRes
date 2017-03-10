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
            text="Enter Doctor ID:",
        ).pack()

        self.user_id = tk.StringVar()
        self.ent_id = ttk.Entry(
            self,
            textvariable=self.user_id,
        ).pack()

        self.lbl_passwd = ttk.Label(self, text="Enter password:").pack()

        self.passwd = tk.StringVar()
        self.ent_passwd = ttk.Entry(
            self,
            textvariable=self.passwd,
            show="*"
        ).pack()

    def log_in(self):
        pswdhash = hashlib.sha1(self.passwd.get().encode('utf-8')).hexdigest()
        # try/except a faire
        print(pswdhash)
        self.sock.send(bytes("{} {}:{}".format("LOGIN", self.user_id.get(), pswdhash), 'utf-8'))
        time.sleep(0.5)
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
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


main_app = tk.Tk()
app = LoginApp(master=main_app)
app.mainloop()
