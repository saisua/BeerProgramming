import socket
import logging
import time
try:
    import Server
except ImportError: pass

def main():
    return
    import sys
    #multiprocessing_logging.install_mp_handler()
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    cl = Client()
    cl.connect(sys.argv[1], 12412)

class Client():
    def __init__(self):
        logging.debug(f"Client.__init__(self)")
        logging.info("Created new client")
        self.listener = None
        self.server = None

        try:
            Server.Process(target=lambda x: x, args=(1))
            self.__can_be_server = True 
        except Exception:
            self.__can_be_server = False

    def connect(self, ip:str, port:int=12412, password:str=None):
        logging.debug(f"Client.connect(self, {ip}, {port}, {password})")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while(True):
            try:
                server.connect((ip, int(port)))
                break
            except ConnectionRefusedError: pass

        self.server = server
        logging.info(f"Connected to personal port in {ip}:{port}")

        self.listener = self.listen(server)

        return self.listener

    def listen(self, server:socket.socket) -> "generator":
        timeout = 0
        
        #server.settimeout(10)

        while(True):
            data = server.recv(1024)
            decoded_data = data.decode("utf-8")

            if(data is None):
                timeout += 1
                if(timeout > 9): break
            elif(decoded_data != ''):
                timeout = 0
                del data
                yield decoded_data

    def send_to_server(self, data:str):
        if(not self.server is None):
            self.server.sendall(bytes(data, "utf-8"))


if __name__ == "__main__":
    main()

