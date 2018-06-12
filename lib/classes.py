#!/usr/bin/env python3

import socket
import struct
import sys
import time
from http.server import BaseHTTPRequestHandler
from email.utils import formatdate

# Set up some nice colors
class bcolors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    ORANGE = '\033[93m'
    ENDC = '\033[0m'
okBox = bcolors.BLUE + '[*] ' + bcolors.ENDC
noteBox = bcolors.GREEN + '[+] ' + bcolors.ENDC
warnBox = bcolors.ORANGE + '[!] ' + bcolors.ENDC

class SSDPListener:
    def __init__(self, localIp, localPort, serverName):
        self.sock = None
        self.knownHosts = []
        self.localIp = localIp
        self.localPort = localPort
        self.serverName = serverName
    def run(self):
        ssdpPort = 1900			# This is defined by the SSDP spec, do not change
        mcastGroup='239.255.255.250'	# This is defined by the SSDP spec, do not change
        serverAddress = ('', ssdpPort)
        knownHosts = []
        
        # Create the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Bind to the server address
        self.sock.bind(serverAddress)
        
        # Tell the operating system to add the socket to
        # the multicast group on for the interface on the specific IP.
        group = socket.inet_aton(mcastGroup)
        mreq = struct.pack('4s4s', group, socket.inet_aton(self.localIp))
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            mreq)
        
        # Receive/respond loop
        while True:
            data, address = self.sock.recvfrom(1024)
            self.process_data(data,address)

    def process_data(self, data, address):
        (remoteIp,remotePort) = address
        if 'M-SEARCH' in str(data):
            if address[0] not in self.knownHosts:
                print(noteBox + "Received an M-SEARCH query from new host {} on port {}".format(remoteIp, remotePort))
                print("    " + okBox + "Subsequent requests from this host will be processed but not printed here.")
                self.knownHosts.append(address[0])
            self.send_location(address)

    def send_location(self, address):
        URL = 'http://{}:{}/ssdp/device-desc.xml'.format(self.localIp, self.localPort)
        lastSeen = str(time.time())
        dateFormat = formatdate(timeval=None, localtime=False, usegmt=True)
        reply = 'HTTP/1.1 200 OK\n'
        reply += 'DATE: ' + dateFormat + '\n'
        reply += 'EXT: \n'
        reply += 'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\n'
        reply += 'LOCATION: ' + URL + '\n'
        reply += 'SERVER: ' + self.serverName + '\n'
        reply += 'ST: upnp:rootdevice\n'
        reply += 'USN: uuid:e427ce1a-3e80-43d0-ad6f-89ec42e46363::upnp:rootdevice\n'
        reply += 'BOOTID.UPNP.ORG: 0\n'
        reply += 'CACHE-CONTROL: max-age=1800\n'
        reply += 'last-seen: ' + lastSeen + '\n'
        reply = bytes(reply, 'utf-8')
        self.sock.sendto(reply, address)

class DeviceDescriptor(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/test':
            print("Got it!")

        self.send_response(200)