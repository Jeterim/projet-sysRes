#!/usr/bin/python3.5

import socket
import os
import ssl

TCP_IP = '127.0.0.1'
TCP_PORT = 6264
BUFFER_SIZE = 1024
data=[]

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((TCP_IP,TCP_PORT))
s.listen(1)
print("listening")

newsocket, addr = s.accept()
print("accept ok")
connstream = context.wrap_socket(newsocket, server_side=True)
print('Connection adress :',addr)

while not data:
    data = connstream.recv(BUFFER_SIZE)
    print("Waiting for datas")

print(data)

connstream.send(b'foobar')

connstream.shutdown(socket.SHUT_RDWR)
connstream.close()