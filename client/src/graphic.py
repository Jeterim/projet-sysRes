"""
Client graphique du projet de Systeme et Reseaux

Authors : Jérémy Petit, David Neyron, Quentin Laplanche
"""
import tkinter as tk
from tkinter import ttk, PhotoImage
from PIL import Image, ImageTk
from tkinter import tix
import socket
import hashlib
import time
import ssl
import os
import sys
import pickle

TCP_IP = '0.0.0.0'
TCP_PORT = 6262
BUFFER_SIZE = 2048

HELP = "-----------------------\n|Commandes disponibles:|\n----------------------- \n- ls ou list : permet de lister les fichiers du répertoire courant. \n- edit ou vi : Permet d'afficher/editer un fichier\n\t Une fois dans le mode edition, taper: \n\t- save ou :w pour sauvegarder et quitter le mode \n\t- quit ou :q pour quitter sans sauvegarder vos modifications \n- cd vous permettra de changer de répertoire\n- mkdir vous permettra de créer un dossier \n- touch vous permettra de creer un fichier \n\n\t Attention certaines de ces commandes necessites des droits particuliers, distribues en fonction de votre role \n\n Taper help pour revoir cette aide\n"


class LoginApp(tk.Frame):
    """
    Login form UI
    """

    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        if len(sys.argv) == 3:
            self.server_ip = sys.argv[1]
            self.port = int(sys.argv[2])
        else:
            self.server_ip = '0.0.0.0'
            self.port = 6262
        self.create_connection()
        self.tentative = 2
        self.acces = 0

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
        self.sock.connect((self.server_ip, self.port))

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
        if self.tentative <= 0:
            self.quit()
        pswdhash = hashlib.sha1(self.passwd.get().encode('utf-8')).hexdigest()
        self.sock.send(bytes("{} {}:{}".format(
            "LOGIN", self.user_id.get(), pswdhash), 'utf-8'))
        data = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        if "granted" in data:
            datae = data.split(';')
            # attribution du role pour des actions supplementaires cote client
            role = datae[1]
            # Destroy window
            self.change_window(self.user_id.get(), role)
        else:
            self.tentative = self.tentative - 1

    def change_window(self, username, role):
        """
        Tue la fenetre de login et instancie la fenetre principale
        """
        # app_app = tk.Tk()
        # app_app.title(" Dossier Medical")
        # app = MainApp(self.sock, master=app_app)
        # main_app.destroy()
        # app.mainloop()
        app = MainApp(self.sock, master=nb)
        nb.add(app, text="Main Window")
        nb.forget(0)

        term = TermApp(self.sock, master=nb, username=username, role=role)
        nb.add(term, text="Console")


class TermApp(tk.Frame):

    def __init__(self, sock, master=None, username='Doe', role=None):
        super().__init__(master)
        self.pack()
        self.editing = False
        self.username = username
        self.filename = 'none'
        self.role = role
        self.sock = sock
        self.create_widgets()

    def create_widgets(self):

        self.editor = tk.Text(self, wrap=tk.WORD)
        self.editor.configure(state='normal')
        self.editor.insert(
            tk.END, HELP)
        if self.role == "admin":
            self.editor.insert(
                tk.END, "\n-------------------------------------------------------\n Les commandes de gestion des utilsateurs sont disponibles : \n- adduser \n- deluser \n- edituser \n- modifyacl\n")
        self.editor.configure(state='normal')
        self.editor.pack(fill=tk.X)
        # self.editor.bind("<Insert>", self.insert_all)

        self.txt = tk.StringVar()
        self.txt.set("{}@Dossier-medical> ".format(self.username))
        self.rootEntry = tk.Entry(self, textvariable=self.txt)
        self.rootEntry.configure(state='normal')
        self.rootEntry.pack(side="bottom", fill=tk.X)
        self.rootEntry.bind("<Return>", self.cycle_text)

    def cycle_text(self, arg=None):
        line = self.txt.get()
        prompt, command = line.split('> ')
        self.txt.set("{}@Dossier-medical> ".format(self.username))
        if not(self.editing):
            if self.role == "admin":
                line = command.split(None)
                if command.startswith("adduser") and len(line) == 4:
                    self.add_user(line)
                elif command.startswith("edtuser") and len(line) == 4:
                    self.edit_user(line)
                elif command.startswith("deluser") and len(line) == 2:
                    self.delete_user(line)
                elif command.startswith("modifyacl") and len(line) == 5:
                    self.modify_acl(line)
                elif command.startswith("adduser") or command.startswith("edtuser") or command.startswith("deluser") or command.startswith("modifyacl"):
                    self.editor.replace(
                        "0.0", tk.END, "Usage : \nadduser <login> <password> <role> \nedtuser <login> <password> <role> \ndeluser <login> \nmodifyacl <action>(grant, revoke) <role> <ressource> <permission>(r, w, x)\n")

            if command.startswith("list") or command.startswith("ls"):
                self.execute_ls(prompt, command)
            elif command.startswith("edit") or command.startswith("vi") or command.startswith("open"):
                self.edit(command, prompt)
            elif command.startswith("cd"):
                instruction, target = command.split(None)
                if target == "..":
                    self.get_back(command, prompt)
                else:
                    self.chdir(command, prompt)
            elif command.startswith("delete") or command.startswith("rm"):
                self.delete(command, prompt)
            elif command.startswith("mkdir"):
                instruction, target = command.split(None)
                self.sock.send("Graphique mkdir {}".format(target).encode())
                response = self.sock.recv(BUFFER_SIZE).decode()
                if response != 'OK':
                    self.editor.replace(
                        "0.0", tk.END, "{} folder created".format(target))
            elif command.startswith("touch"):
                instruction, target = command.split(None)
                self.sock.send("Graphique touch {}".format(target).encode())
                response = self.sock.recv(BUFFER_SIZE).decode()
                if response == 'OK':
                    self.editor.replace(
                        "0.0", tk.END, "{} file created".format(target))
                else:
                    self.editor.replace(
                        "0.0", tk.END, "Error creating {}".format(target))
            elif command.startswith("help"):
                self.editor.replace("0.0", tk.END, HELP)
        else:
            if command.startswith("save") or command.startswith(":w"):
                self.save_file()
                self.editing = False
                self.filename = 'empty'
            elif command.startswith("quit") or command.startswith(":q"):
                self.editing = False
                self.filename = 'empty'

    def modify_acl(self, line):
        """
        Only for admin
        Edit files ACL
        """
        self.sock.send(bytes("MODIFYACL {} {} {} {}".format(
            line[1], line[2], line[3], line[4]), 'utf-8'))

    def delete_user(self, line):
        """
        Only for admin.
        Delete any user
        """
        self.sock.send(bytes("DELUSR {}".format(line[1]), 'utf-8'))

    def edit_user(self, line):
        """
        Edit informations on one user.
        """
        pswdhash = hashlib.sha1(
            line[2].encode('utf-8')).hexdigest()
        self.sock.send(bytes("EDITUSR {}:{}:{}".format(
            line[1], pswdhash, line[3]), 'utf-8'))

    def add_user(self, line):
        """
        Create a new user with the specified role.
        """
        pswdhash = hashlib.sha1(
            line[2].encode('utf-8')).hexdigest()
        self.sock.send(bytes("CREATEUSR {}:{}:{}".format(
            line[1], pswdhash, line[3]), 'utf-8'))

    def save_file(self):
        """
        Write the content of the file on the server
        """
        file_content = self.editor.get("0.0", tk.END)
        print(file_content)
        print(sys.getsizeof(file_content))
        self.sock.send("Graphique modify {} {}".format(
            self.filename, sys.getsizeof(file_content)).encode())
        time.sleep(0.5)
        self.sock.send(file_content.encode())

    def execute_ls(self, prompt, command):
        """
        Handle the ls command
        """
        values = self.list_files()
        print(values)
        self.editor.replace(
            "0.0", tk.END, "{}> {}\n{}".format(prompt, command, values))

    def get_back(self, command, prompt):
        """
        Handle the cd .. command
        """
        instruction, target = command.split(None)
        self.sock.send("Graphique chdir ..".encode())
        msg = self.sock.recv(BUFFER_SIZE).decode()
        if msg.startswith("OK"):
            self.editor.replace("0.0", tk.END, "cd into {}".format(target))
        else:
            print("Tu n'as le droit de remonter encore")

    def chdir(self, command, prompt):
        """
        Allow user to change directory on the server's filesystem
        """
        instruction, target = command.split(None)
        self.sock.send("Graphique print {}".format(target).encode())
        size_of_file = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(size_of_file)
        if size_of_file == "Directory":
            self.editor.replace("0.0", tk.END, "cd into {}".format(target))
            # time.sleep(1)
            # self.editor.replace("0.0", tk.END, "{}".format(prompt))
        elif size_of_file == "AccessError":
            pass
        else:
            content = self.sock.recv(int(size_of_file)).decode('utf-8')
            print(content)
            self.editor.replace(
                "0.0", tk.END, "{}> {} \nError {} is not a directory".format(prompt, command, content))

    def edit(self, command, prompt):
        """
        launch editor mode if a file is given.
        if a directory has been given, cd into it.
        """
        instruction, target = command.split(None)
        self.sock.send("Graphique print {}".format(target).encode())
        size_of_file = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(size_of_file)
        if size_of_file == "Directory":
            self.editor.replace(
                "0.0", tk.END, "{}{} is a directory, so I've cd you into it".format(prompt, target))
        elif size_of_file == "AccessError":
            self.editor.replace(
                "0.0", tk.END, "{} You can't access{}".format(prompt, target))
        else:
            content = self.sock.recv(int(size_of_file)).decode('utf-8')
            print(content)
            self.editing = True
            self.filename = target
            self.editor.replace(
                "0.0", tk.END, "{}".format(content))
            # page1.pop

    def delete(self, command, prompt):
        """
        delete a file or a directory
        """
        instruction, target = command.split(None)
        self.sock.send("Graphique delete {}".format(target).encode('utf-8'))
        # time.sleep(0.2)
        msg = self.sock.recv(BUFFER_SIZE).decode()
        if not(msg.startswith("OK")):
            self.editor.replace(
                "0.0", tk.END, "{} Error deleting {}".format(prompt, target))

    def list_files(self):
        """
        Test d'execution d'une commande sur le serveur
        """
        self.sock.send(b"Graphique ls")
        return "\n".join(self.sock.recv(BUFFER_SIZE).decode('utf-8').split(','))


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
        self.list = ttk.Treeview(self)
        ysb = ttk.Scrollbar(self, orient='vertical', command=self.list.yview)
        self.list.configure(yscroll=ysb.set)
        self.list.pack(side="left")

        image = Image.open("lenna.gif")
        photo = ImageTk.PhotoImage(image, master=self)

        self.img = tk.Label(self, image=photo)
        self.img.image = photo
        self.img.pack()

        self.editor = tk.Text(self, wrap=tk.WORD)
        self.editor.insert(tk.END, " ")

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.config(command=self.editor.yview)

        self.editor.pack(fill=tk.Y)
        self.editor.config(yscrollcommand=self.scrollbar.set)
        self.populate_tree_view()
        self.list.bind('<ButtonRelease-1>', self.update_editor)

        self.save_button = tk.Button(self, text="Save file",
                                     command=self.save_file).pack(side="bottom")

        self.back_button = tk.Button(
            self, text="retour", command=self.get_back).pack()
        self.context_menu = tk.Menu(self, tearoff=0)
        tk.Button(self, text="Delete", command=self.delete_item).pack()

    def delete_item(self):
        """
        Delete the currently selected item in the tree view list
        """
        current_item = self.list.focus()
        if current_item:
            real_item = self.list.item(current_item)
            print(real_item["text"])
            self.sock.send("Graphique delete {}".format(
                real_item["text"]).encode('utf-8'))
            # time.sleep(0.2)
            msg = self.sock.recv(BUFFER_SIZE).decode()
            if msg.startswith("OK"):
                self.list.delete(current_item)
                print('Delete Boum !')

    def save_file(self):
        """
        Write the content of the file on the server
        """
        file_content = self.editor.get("0.0", tk.END)
        print(file_content)
        item_dic = self.get_selected_item(None)
        self.sock.send("Graphique modify {} {}".format(
            item_dic["text"], sys.getsizeof(file_content)).encode())
        time.sleep(0.5)
        self.sock.send(file_content.encode())

    def get_back(self):
        """
        Allow to cd .. and refresh the tree view
        """
        self.sock.send("Graphique chdir ..".encode())
        time.sleep(0.3)
        msg = self.sock.recv(BUFFER_SIZE).decode()
        if msg.startswith("OK"):
            self.populate_tree_view()
        else:
            print("Tu n'as le droit de remonter encore")

    def populate_tree_view(self, event=None):
        """
        Fill the tree-view with list fromt the server
        """
        print("Refresh tree view")
        self.list.delete(*self.list.get_children())
        file_list = self.list_files()
        for file in file_list:
            print(file)
            self.list.insert("", 'end', text=file, open=False)

    def update_editor(self, event):
        """
        Update the text editor whenever another item is selected in the tree view UI
        """
        txt = self.get_selected_item(event)
        _, ext = os.path.splitext(txt['text'])
        print("extension : {}".format(ext))
        if ext == ".gif":
            print("c'est une image")
            content = self.get_img_for_item(self.get_selected_item(event))
            # image = Image.open(content)
            photo = ImageTk.PhotoImage(content, master=self)
            self.img.image = photo
            self.img.config(image=photo)
            self.editor.replace("0.0", tk.END, "")
            self.editor.config(height=0)
        else:
            print("c'est un texte")
            content = self.get_text_for_item(self.get_selected_item(event))
            if content != "NotFound":
                countVar = 0
                self.editor.config(height=24)
                self.editor.replace("0.0", tk.END, content)
                # implementer une recherche
                print(self.editor.search("ceinture", "1.0",
                                         stopindex="end", count=countVar))

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
        elif size_of_file == "AccessError":
            # affichage erreur acl ?
            return "NotFound"
        elif size_of_file == "NotFound":
            return ''
        elif size_of_file != "Directory" and int(size_of_file) > 0:
            content = self.sock.recv(int(size_of_file)).decode('utf-8')
            print(content)
            return content
        else:
            return ''

    def get_img_for_item(self, item_dic):
        """
        Return the content of a selected item from the tree view UI.
        """
        self.sock.send("Graphique printimg {}".format(
            item_dic["text"]).encode())
        size_of_file = self.sock.recv(BUFFER_SIZE).decode('utf-8')
        print(size_of_file)

        img = self.sock.recv(int(size_of_file))
        taille = sys.getsizeof(img)
        print("Taille : {}".format(taille))
        imageDict = pickle.loads(img)
        print(imageDict)
        # if size_of_file == "Directory":
        #    self.populate_tree_view()
        # else:
        print("test")
        # content = self.sock.recv(int(size_of_file)).decode('utf-8')
        print("fin content")
        # print(content)
        return imageDict['imageFile']

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


# main_app = tk.Tk()
# main_app.title("Login Dossier Medical")
# app = LoginApp(master=main_app)
# app.mainloop()
root_app = tk.Tk()
root_app.title = "Dossier médical"
nb = ttk.Notebook(root_app)
page1 = LoginApp(nb)
nb.add(page1, text="Login")
nb.pack(expand=1, fill="both")
root_app.mainloop()
