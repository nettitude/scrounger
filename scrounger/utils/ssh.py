"""
SSH and SFTP wrapper wround paramiko framework.
"""

import paramiko as _paramiko

class SSHClient(object):
    """
        SSH Client wrapper using paramik framework.
    """

    _session = _ip = _port = _username = _password = _timout = None

    def __init__(self, ip, port, username, password, timeout=30):
        """
        Creates an SSH Client object.

        :param str ip: the ip of the remote host
        :param int port: the port running ssh on the remote host
        :param strusername: the username to be used for login
        :param str password: the password to be used for login
        """
        self._ip = ip
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout

    def connect(self):
        """ Connected to the report server. """
        self._session = _paramiko.SSHClient()
        self._session.load_system_host_keys()
        self._session.set_missing_host_key_policy(
            _paramiko.AutoAddPolicy()) # auto adds remote host to known_hosts
        self._session.connect(self._ip, port=self._port,
            username=self._username, password=self._password)

    def disconnect(self):
        """ Disconnects from the remote server. """
        self._session.close()
        self._session = None

    def execute(self, command):
        """
        Executes a given command on the remote server.

        :param str command: the command to be executed on the remote server
        :return: returns stdout and stderr or None
        """
        if self._session:
            stdin, stdout, stderr = self._session.exec_command(command,
                timeout=self._timeout)
            return stdout.read(), stderr.read()
        return None, None

    def get_file(self, remote_file_path, local_file_path):
        """
        Retrieves a file from the remove server.

        :param str remote_file_path: the path on the remote server of the files
        to be coppied
        :param str local_file_path: the path on the local host where to copy the
        file
        :return: returns nothing
        """
        if self._session:
            sftp = self._session.open_sftp()
            sftp.get(remote_file_path, local_file_path)
            sftp.close()

    def put_file(self, local_file_path, remote_file_path):
        """
        Copies a file to the remote server.

        :param str local_file_path: the local file path fo the file to be
        coppied to the remote server
        :param str remote_file_path: the file path where the file is going to be
        coppied to
        :return: returns nothing
        """
        if self._session:
            sftp = self._session.open_sftp()
            sftp.put(local_file_path, remote_file_path)
            sftp.close()

    def connected(self):
        """
        Checks if the host is connected to the local server

        :return: returns True if there is a connection or False if not
        """
        return self._session != None

