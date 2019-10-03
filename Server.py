from multiprocessing import Process, Manager
import socket, logging

def main():
    pass
    
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

    def listen_connections(self, connections:int=1, ip:str=None, port:int=None):
        logging.debug(f"Server.listen_connections(self, {connections}, {ip}, {port})")
        
        if(ip is None): ip = self.ip
        if(port is None): port = self.port
        else: self.port = int(port)
            
        process = [] #miau
        if(self.threaded[0]):
            for _ in range(connections):
                process.append(Process(target=self.new_connection, args=(ip, port)))
                
                print("stop")

                process[-1].start()
                
            for conn in process: conn.join()
        else: self.new_connection(ip, port)
    
    
    def new_connection(self, ip:str=None, port:int=None):
        logging.debug(f"Server.new_connection(self, {ip}, {port})")
        if(self.max_connections + 1 and len(self._clients_p_obj) >= self.max_connections): return
    
        if(ip is None): ip = self.ip
        if(port is None): port = self.port

        self._connection.listen()
            
        listener, addr = self._connection.accept()
        
        logging.info(f"Connected new user: {addr}")
        
        self._client_from_addr[addr] = listener
        self.open[addr] = True

        if(self.threaded[1]):
            self._process_from_addr[addr] = Process(target=self.listen, args=(addr))#, daemon=True)
            self._process_from_addr[addr].start()
        else: self.listen(addr)
    
    def sendto(self, message:str, addr:tuple):
        self._client_from_addr[addr].sendto(bytes(str(message), "utf-8"), addr)
    
    def listen(self, addr):
        logging.debug("Client_p_obj.listen(self)")
        if(not self.open[addr]): return

        listener = self._client_from_addr[addr]
        
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
                    
                        
    def parse_data(self, data:str, addr:str):
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