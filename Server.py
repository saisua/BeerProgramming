from multiprocessing import Process, Manager
import socket, logging
import typing

# This function gets executed when you run
# python Server.py and its use is to test the code
# so it will usually be empty
def main():
    logging.error("Run run_server instead")

    
"""
    The Server class is the main builder for the Sockets
    over TCP. It will by default allow an unlimited number
    of clients, but it will accept only 1.
    When told so, it can accept multiple clients at once.
    When one client gets connected, the Server assigns
    one process to that client, and that process divides
    into two, one that operates from the point of view of the
    server, and a second one, as a daemon, who listens and
    runs the functions given in order_dict
"""
class Server():
    def __init__(self, ip:str=None, port:int=12412, password:str=None, max_connections:int=-1,
                        order_dict:dict={}):
        self.threaded = [False, False]
        
        logging.debug(f"Server.__init__(self, {ip}, {port}, {password}, {max_connections})")
        #self._clients_process = []
        #self._clients_p_obj = []
        self.__manager = Manager()
        self._client_from_addr = self.__manager.dict()
        self._process_from_addr = {}
        self.open = self.__manager.dict()
        
        self.order_dict = order_dict

        if(ip is None): 
            ip = socket.gethostbyname_ex(socket.gethostname())[-1]
            if(type(ip) is list or type(ip) is tuple): ip = ip[-1]
            logging.warning(f"Ip set automatically to {ip}")

            ip = "127.0.0.1"
            logging.warning(f"Ip set automatically to {ip}")

        self.ip = ip
        self.port = int(port)

        self.password = password
        self.max_connections = int(max_connections) if max_connections >= -1 else -1

        self._connection = socket.socket(socket.AF_INET, 
                            socket.SOCK_STREAM)
        self._connection.bind((ip, port))
        logging.info("Created new server")

    # listen_connections sets up {connections} connections,
    # that when connected by a client, will assign one new
    # thread to that client
    def listen_connections(self, connections:int=1, ip:str=None, port:int=None) -> None:
        logging.debug(f"Server.listen_connections(self, {connections}, {ip}, {port})")
        
        if(ip is None): ip = self.ip
        if(port is None): port = self.port
        else: self.port = int(port)
            
        if(self.threaded[0]):
            process = [] #miau
            for _ in range(connections):
                process.append(Process(target=self.new_connection, args=(ip, port)))
                
                print("stop")

                process[-1].start()
                
            for conn in process: conn.join()
        else: self.new_connection(ip, port)
    
    # new_connection is run by a client-assigned thread,
    # and it does wait for the client to send an order
    # that when parsed, will coincide with one of tge keys
    # of ord_dict, and so its value will be executed
    def new_connection(self, ip:str=None, port:int=None) -> None:
        logging.debug(f"Server.new_connection(self, {ip}, {port})")
        if(self.max_connections + 1 and len(self._client_from_addr) >= self.max_connections): return
    
        if(ip is None): ip = self.ip
        if(port is None): port = self.port

        self._connection.listen()
            
        listener, addr = self._connection.accept()
        
        logging.info(f"Connected new user: {addr}")
        
        self._client_from_addr[addr] = listener
        self.open[addr] = True

        if(self.threaded[1]):
            self._process_from_addr[addr] = Process(target=self.listen, args=(addr, listener))#, daemon=True)
            self._process_from_addr[addr].start()
        else: self.listen(addr,listener)
    
    # sendto (kind of) overloads socket.socket.sendto .
    # Given a message and an address, the server will
    # turn message into utf-8 formatted bytes, and it
    # will send it (if possible) to the client with the
    # given address
    def sendto(self, message:str, addr:tuple) -> "iterable":
        self._client_from_addr[addr].sendto(bytes(str(message), "utf-8"), addr)

    # sendall (kind of) overloads socket.socket.sendall .
    # Even if it is not tested, it theorically turns message
    # into utf-8 formatted bytes and sends it to all clients
    # in the socket server.
    def sendall(self, message:str):
        self._connection.sendall(bytes(str(message), "utf-8"))
    
    # listen will make use of listener to (if given one)
    # ask for a password, and then it will return a generator
    def listen(self, addr:tuple, listener:"socket.socket") -> "generator[str]":
        logging.debug("Client.listen(self)")
        if(not self.open[addr]): return
        
        with listener:
            timeout = 0
            if(not self.password is None):
                wrong_att = 0
                accepted = False
                while(not accepted):
                    password = listener.recv(1024)
                    decoded_password = password.decode("utf-8")
                    if(password is None):
                        timeout += 1
                        if(timeout > 9): 
                            self.open[addr] = False
                            break
                    elif(decoded_password != ''):
                        timeout = 0
                        if(decoded_password == self.password):
                            accepted = True
                            del wrong_att
                            del password
                            del decoded_password
                        else:
                            wrong_att += 1
                            if(wrong_att > 3):
                                del wrong_att
                                self.open[addr] = False
                                break

            while(self.open[addr]):
                data = listener.recv(1024)
                decoded_data = data.decode("utf-8")

                if(data is None):
                    timeout += 1
                    logging.debug(f"Timeout of user {addr} increased to {timeout}")
                    if(timeout > 9): 
                        logging.warning(f"User {addr} has disconnected")
                        break
                elif(decoded_data != ''):
                    timeout = 0
                    logging.info(f"Recived data '{decoded_data}' from address {addr}")
                    
                    self.parse_data(decoded_data, addr)

        del self._process_from_addr[addr]
        del self._client_from_addr[addr]
        del self.open[addr]
                    
                        
    # parse_data takes one string recieved from one client
    # and its address and executes (if found) any matches
    # separated by ';' in the string as keys in ord_dict
    # the functions in the values of the dict must take 
    # addr as the first parameter even if unnecessary
    def parse_data(self, data:str, addr:str) -> None:
        #print(f"parse_data {data}")
        order = None
        args = (addr,)
        for arg in data.split(';'):
            new_ord = self.order_dict.get(arg.strip(), None)
            print(f"arg:{arg}, new_ord:{new_ord}")
            if(not new_ord is None):
                if(not order is None): 
                    print(f"{order}{args}")
                    try:
                        order(*args)
                    except Exception as err: print("ERROR: {err}")
                    
                order = new_ord
                args = (addr,)
                
            elif(arg.strip() != ''): args+=(arg.strip(),)
            
        if(not order is None): 
            print(f"{order}{args}.")
            try:
                order(*args)
            except Exception as err: print(f"ERROR: {err}")
