import tkinter as tk
from tkinter import ttk
import socket
import hashlib
import time
import ssl
import os

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
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False
        context.load_verify_locations(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert/cert.pem"))
        self.sock = ssl.wrap_socket(socket.socket(
            socket.AF_INET, socket.SOCK_STREAM))
        self.sock.settimeout(4)
        self.sock.connect((TCP_IP, TCP_PORT))

    def create_widgets(self):
        """
        Creation de l'interface graphique
        """
        self.login = tk.Button(
            self, text="Login", command=self.log_in)
        self.login.pack(side="bottom")
        # Login label and field
        self.lbl_id = ttk.Label(
            self,
            text="Enter Doctor ID:").pack()
        self.user_id = tk.StringVar()
        self.ent_id = ttk.Entry(
            self,
            textvariable=self.user_id).pack()
        # Password label and field
        self.lbl_passwd = ttk.Label(self, text="Enter password:").pack()
        self.passwd = tk.StringVar()
        self.ent_passwd = ttk.Entry(
            self,
            textvariable=self.passwd,
            show="*")
        self.ent_passwd.pack(side="bottom")

        self.bind_enter_key()

    def bind_enter_key(self):
        """
        Bind the Return key to call the @log_in() method
        """
        self.login.bind('<Return>', self.log_in)
        self.ent_passwd.bind('<Return>', self.log_in)

    def log_in(self, event=None):
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
            # attribution du role pour des actions supplementaires cote client
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
                               command=self.list_files).pack(side="top")
        self.list = ttk.Treeview(self).pack(side="left")
        self.editor = tk.Text(self, wrap=tk.WORD)
        quote = """HAMLET: To be, or not to be--that is the question:
Whether 'tis nobler in the mind to suffer
The slings and arrows of outrageous fortune
Or to take arms against a sea of troubles
And by opposing end them. To die, to sleep--
No more--and by a sleep to say we end
The heartache, and the thousand natural shocks
That flesh is heir to. 'Tis a consummation
Devoutly to be wished."""
        self.editor.insert(tk.END, quote)
        self.scrollbar = tk.Scrollbar(self)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.config(command=self.editor.yview)

        self.editor.pack(fill=tk.Y)
        self.editor.config(yscrollcommand=self.scrollbar.set)

    def list_files(self):
        """
        Test d'execution d'une commande sur le serveur
        """
        self.sock.send(b"ls")
        time.sleep(0.5)  # Wait for answer from the server
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(data)


main_app = tk.Tk()
main_app.title("Login Dossier Medical")
app = LoginApp(master=main_app)
app.mainloop()
