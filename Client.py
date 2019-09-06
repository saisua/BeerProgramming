import socket
import logging
import sys
import time

def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    cl = Client()
    cl.connect(sys.argv[1], 12418)

class Client():
    def __init__(self):
        logging.debug(f"Client.__init__(self)")
        logging.info("Created new client")

    def connect(self, ip:str, port:int=12412, password:str=None):
        logging.debug(f"Client.connect(self, {ip}, {port}, {password})")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.connect((ip, port))
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
                    except: logging.warning(f"Recieved non-int port ({port}) from server")
        
        time.sleep(0.5)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.connect((ip, port))
            timeout = 0
            logging.info(f"Connected to personal port in {ip}:{port}")
            while(True):
                server.send(bytes(input("> "), "utf-8"))

                data = server.recv(1024)

                print(data.decode("utf-8"))

                if(data is None):
                    timeout += 1
                    if(timeout > 9): break
                else:
                    timeout = 0

if __name__ == "__main__":
    main()
