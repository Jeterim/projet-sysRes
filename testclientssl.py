#!/usr/bin/python3.5

import ssl
import socket
import os

TCP_IP = '127.0.0.1'
TCP_PORT = 6264
BUFFER_SIZE=1024
data=''

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = False								# a revoir si il faut checker
context.load_verify_locations("/etc/ssl/certs/cert.pem")
print("context ok")

conn = context.wrap_socket(socket.socket(socket.AF_INET,socket.SOCK_STREAM),server_hostname="toto")
print("wrap ok")
conn.connect((TCP_IP,TCP_PORT))
print("connect ok")

cert = conn.getpeercert()
print("cert ok")

conn.send(b'barfoo')

while not data:
	data = conn.recv(BUFFER_SIZE)

print(data)

conn.close()