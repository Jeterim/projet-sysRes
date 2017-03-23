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
        self.list = ttk.Treeview(self)
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.list.yview)
        self.list.configure(yscroll=ysb.set)
        self.list.pack(side="left")

        self.editor = tk.Text(self, wrap=tk.WORD)
        self.editor.insert(tk.END, "Empty text")

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.config(command=self.editor.yview)

        self.editor.pack(fill=tk.Y)
        self.editor.config(yscrollcommand=self.scrollbar.set)
        self.populate_tree_view()
        self.list.bind('<ButtonRelease-1>', self.update_editor)

        self.save_button = tk.Button(self, text="Save file",
                                     command=self.save_file).pack(side="bottom")

        self.back_button = tk.Button(self, text="retour", command=self.get_back).pack()

    def save_file(self):
        file_content = self.editor.get("0.0", tk.END)
        print(file_content)
        item_dic = self.get_selected_item(None)
        self.sock.send("Graphique modify {} {}".format(item_dic["text"], len(file_content)).encode())
        time.sleep(0.5)
        self.sock.send(file_content.encode())

    def get_back(self):
        self.sock.send("Graphique chdir ..".encode())
        time.sleep(0.3)
        self.populate_tree_view()

    def populate_tree_view(self):
        """
        Fill the tree-view with list fromt the server
        """
        self.list.delete(*self.list.get_children())
        file_list = self.list_files()
        for file in file_list:
            print(file)
            self.list.insert("", 'end', text=file, open=False)

    def update_editor(self, event):
        """
        Update the text editor whenever another item is selected in the tree view UI
        """
        content = self.get_text_for_item(self.get_selected_item(event))
        if content != "NotFound":
            self.editor.replace("0.0", tk.END, content)

    def get_selected_item(self, event):
        """
        Return the selected item in the tree-view
        """
        current_item = self.list.focus()
        return self.list.item(current_item)

    def get_text_for_item(self, item_dic):
        """
        Return the content of a selected item from the tree view UI.
        """
        self.sock.send("Graphique print {}".format(item_dic["text"]).encode())
        size_of_file = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(size_of_file)
        if size_of_file == "Directory":
            self.populate_tree_view()
        else:
            content = self.sock.recv(int(size_of_file)).decode('utf-8')
            print(content)
            return content

    def list_files(self):
        """
        Test d'execution d'une commande sur le serveur
        """
        self.sock.send(b"Graphique ls")
        # time.sleep(0.5)  # Wait for answer from the server
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(data)
        formatted_list = data.split(',')
        return formatted_list

    def change_directory(self, change_directory):
        self.sock.send(b"Graphique chdir")


main_app = tk.Tk()
main_app.title("Login Dossier Medical")
app = LoginApp(master=main_app)
app.mainloop()
