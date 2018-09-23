#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   tcprelay.py - TCP connection relay for usbmuxd
#
# Copyright (C) 2009    Hector Martin "marcan" <hector@marcansoft.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# Modified by RDC 23 September 2018
# Removed command line arguments and main function
# also removed prints
# Added Threaded Object and method to create threads


import usbmux
import SocketServer
import select
import sys
import threading

class SocketRelay(object):
    def __init__(self, a, b, maxbuf=65535):
        self.a = a
        self.b = b
        self.atob = ""
        self.btoa = ""
        self.maxbuf = maxbuf
    def handle(self):
        while True:
            rlist = []
            wlist = []
            xlist = [self.a, self.b]
            if self.atob:
                wlist.append(self.b)
            if self.btoa:
                wlist.append(self.a)
            if len(self.atob) < self.maxbuf:
                rlist.append(self.a)
            if len(self.btoa) < self.maxbuf:
                rlist.append(self.b)
            rlo, wlo, xlo = select.select(rlist, wlist, xlist)
            if xlo:
                return
            if self.a in wlo:
                n = self.a.send(self.btoa)
                self.btoa = self.btoa[n:]
            if self.b in wlo:
                n = self.b.send(self.atob)
                self.atob = self.atob[n:]
            if self.a in rlo:
                s = self.a.recv(self.maxbuf - len(self.atob))
                if not s:
                    return
                self.atob += s
            if self.b in rlo:
                s = self.b.recv(self.maxbuf - len(self.btoa))
                if not s:
                    return
                self.btoa += s

class TCPRelay(SocketServer.BaseRequestHandler):
    def handle(self):
        #print "Incoming connection to %d"%self.server.server_address[1]
        mux = usbmux.USBMux(None)
        #print "Waiting for devices..."
        if not mux.devices:
            mux.process(1.0)
        if not mux.devices:
            #print "No device found"
            self.request.close()
            return
        dev = mux.devices[0]
        #print "Connecting to device %s"%str(dev)
        dsock = mux.connect(dev, self.server.rport)
        lsock = self.request
        #print "Connection established, relaying data"
        try:
            fwd = SocketRelay(dsock, lsock, self.server.bufsize * 1024)
            fwd.handle()
        finally:
            dsock.close()
            lsock.close()
        #print "Connection closed"

class TCPServer(SocketServer.TCPServer):
    allow_reuse_address = True

class ServerSession(threading.Thread):
    """ Represents 1 port forwarding thread server """

    _alive = False
    _server = None

    def __init__(self, server):
        super(ServerSession, self).__init__()
        self._server = server
        self._alive = True

    def run(self):
        while self._alive:
            self._server.handle_request()

    def stop(self):
        self._alive = False
        self._Thread__stop()

def create_server(host="localhost", remote_port=22, local_port=2222):
    """
    Creates and returns a TCP Server thread

    :param str host: the host to open the port forwarding from
    :param int remote_port: the remote ort to be forward to locally
    :param int local_port: the local port to open to forward to
    :return ServerSession: the thread with the forwarding server
    """

    server = TCPServer((host, int(local_port)), TCPRelay)
    server.rport = int(remote_port)
    server.bufsize = 128

    thread = ServerSession(server)
    thread.start()
    return thread
