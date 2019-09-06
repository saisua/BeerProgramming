from multiprocessing import Process
import socket
import logging
import sys

def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    serv = Server("192.168.0.154", 12418)#sys.argv[1])
    serv.listen_connections(3)
    i = True
    while(i):
        i = input("> ")
        try:
            exec(i)
        except Exception as ex: logging.warning(ex)
    serv.close

class Server():
    def __init__(self, ip:str=None, port:int=12412, password:str=None, max_connections:int=-1):
        logging.debug(f"Server.__init__(self, {ip}, {port}, {password}, {max_connections})")
        self._clients_process = []
        self._clients_p_obj = []

        if(ip is None): 
            ip = socket.getfqdn()
            logging.warning(f"Ip set automatically to {ip}")
        self.ip = ip
        self.port = port

        self.password = password
        self.max_connections = max_connections

        self.router_connection = socket.socket(socket.AF_INET, 
                            socket.SOCK_STREAM)
        self.router_connection.bind((ip, port))
        self.port += 1
        logging.info("Created new server")

    def listen_connections(self, connections:int=1, ip:str=None, port:int=None):
        logging.debug(f"Server.listen_connections(self, {connections}, {ip}, {port})")
        if(ip is None): ip = self.ip
        if(port is None): port = self.port
        else: self.port = port

        new_conn = []
        
        for conn_num in range(connections):
            # if fails, move to __init__
            self.router_connection.listen(1)
            listener, addr = self.router_connection.accept()
            with listener:
                logging.debug(f"Connected new user {addr} to router")
                listener.sendall(bytes(str(self.port), "utf-8"))
                new_conn.append(Process(target=self.new_connection, args=(ip, self.port)))
                new_conn[-1].start()
            self.port += 1

        for conn in new_conn:
            conn.join(60)

    def new_connection(self, ip:str=None, port:int=None):
        logging.debug(f"Server.new_connection(self, {ip}, {port})")
        if(self.max_connections + 1 and len(self._clients_p_obj) >= self.max_connections): return

        if(ip is None): ip = self.ip
        if(port is None): port = self.port
        
        connection = socket.socket(socket.AF_INET, 
                            socket.SOCK_STREAM)
        connection.bind((ip, port))
        
        self._clients_p_obj.append(Client_p_obj(
                self, connection, None,
                port
                ))

        self._clients_p_obj[-1].listen()

        self._clients_process.append(
                Process(target=self._clients_p_obj[-1].listen)
                )
        self._clients_p_obj[-1]._process = self._clients_process[-1]
        self._clients_process[-1].start()
        self._clients_process[-1].join()

    def close_connection(self, p_obj:"Client_p_obj"):
        logging.debug(f"Server.close_connection(self, {p_obj})")
        process = p_obj._process
        connection = p_obj._connection

        self._clients_p_obj.remove(p_obj)

        connection.shutdown(socket.SHUT_RDWR)
        connection.close()
        process.terminate()

        self._clients_process.remove(process)

    @property
    def close(self):
        logging.debug("Server.close(self)")
        for p_obj in self._clients_p_obj: self.close_connection(p_obj)
        self.router_connection.shutdown(socket.SHUT_RDWR)
        self.router_connection.close()

class Client_p_obj():
    def __init__(self, server:"Server", connection:socket.socket,
                process:Process, port:int=None):
        logging.debug(f"Client_p_obj.__init__(self, {server}, {connection}, {process}, {port})")
        self.open = True
        self.accepted = False
        self._server = server
        self._connection = connection
        self._process = process
        self._port = port

    def listen(self):
        logging.debug("Client_p_obj.listen(self)")
        self._connection.listen()
        listener, addr = self._connection.accept()
        with listener:
            logging.info(f"Connected new user: {addr} ({self._port})")
            timeout = 0
            if(not self._server.password is None):
                wrong_att = 0
                while(not self.accepted):
                    password = listener.recv(1024)
                    decoded_password = password.decode("utf-8")
                    if(password is None):
                        timeout += 1
                        if(timeout > 9): 
                            self.close()
                            return
                    elif(decoded_password != ''):
                        timeout = 0
                        if(decoded_password == self._server.password):
                            self.accepted = True
                            del wrong_att
                            del password
                            del decoded_password
                        else:
                            wrong_att += 1
                            if(wrong_att > 3):
                                del wrong_att
                                self.close()
                                return

            while(self.open):
                data = listener.recv(1024)
                decoded_data = data.decode("utf-8")
                print(decoded_data)

                if(data is None):
                    timeout += 1
                    logging.debug(f"Timeout in port {self._port} increased to {timeout}")
                    if(timeout > 9): 
                        logging.warning(f"Port {self._port} has disconnected")
                        self.close()
                elif(decoded_data != ''):
                    timeout = 0
                    logging.info(f"Recived data '{decoded_data}' from port {self._port}")
                    listener.sendall(data)

    @property
    def close(self):
        logging.debug("Client_p_obj.close(self)")
        self.open = False
        self._server.close_connection(self)

if __name__ == "__main__":
    main()