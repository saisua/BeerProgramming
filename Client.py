import socket
import logging
import time

def main():
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

    def connect(self, ip:str, port:int=12412, password:str=None):
        logging.debug(f"Client.connect(self, {ip}, {port}, {password})")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            while(True):
                try:
                    server.connect((ip, int(port)))
                    break
                except ConnectionRefusedError: pass
            port = False
            timeout = 0
            while(not port):
                data = server.recv(1024)
                decoded_data = data.decode("utf-8")
                if(data is None):
                    timeout += 1
                    logging.debug(f"Main server timeout increased to {timeout}")
                    if(timeout > 9): 
                        logging.error("Main server has timed out")
                        return
                elif(decoded_data != ''):
                    timeout = 0
                    logging.info(f"Recieved personal port ({decoded_data})")
                    try:
                        port = int(decoded_data)
                        logging.debug("The port is valid!")
                    except: logging.warning(f"Recieved non-int port ({port}) from server")

        time.sleep(0.5)

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

        while(True):
            data = server.recv(1024)
            decoded_data = data.decode("utf-8")

            if(data is None):
                timeout += 1
                if(timeout > 9): break
            elif(decoded_data == ''):
                timeout = 0
                yield decoded_data

    def send_to_server(self, data:str):
        if(not self.server is None):
            self.server.sendall(bytes(data, "utf-8"))


if __name__ == "__main__":
    main()

