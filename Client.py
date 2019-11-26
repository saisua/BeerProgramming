import socket
import logging
import time

# This function gets executed when you run
# python Client.py and its use is to test the code
# so it will usually be empty
def main():
    return
    import sys
    #multiprocessing_logging.install_mp_handler()
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    cl = Client()
    cl.connect(sys.argv[1], 12412)

"""
    The Client class is the main socket client class.
    It is programmed to connect to an instance of
    Server.Server. It mostly listens and sends data
    from and to the server
"""
class Client():
    def __init__(self):
        logging.debug(f"Client.__init__(self)")
        logging.info("Created new client")
        self.listener = None
        self.server = None

    # connect will connect to the server in ip:port .
    # if given a password, the client will try to send it to
    # the server (not working)
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

    # listen takes one connected instance of socket.socket
    # and returns one generator. Each time that the
    # generator executes its .next() , tbe function will
    # be resumed, and it will return any data collected
    # from the server
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

    # send_to_server turns {data} into utf-8 formatted
    # bytes and sends them to the server
    def send_to_server(self, data:str):
        if(not self.server is None):
            self.server.sendall(bytes(data, "utf-8"))


if __name__ == "__main__":
    main()

