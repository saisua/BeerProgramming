import Server
import logging
import multiprocessing_logging
from multiprocessing import Process, Manager

def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    from sys import argv
    argv += ('-i','192.168.0.154','-pl','1')
    Beer_programming(**arg_parse(argv)).play()

def arg_parse(args:list, arg_dict:dict=
        {"--ip":"ip","--port":"port",
         "-i":"ip","-p":"port",
         "-pl":"player_num",
         "--players":"player_num"}) -> dict:
    final = {}
    before = False
    for arg in args[1:]:
        if(before):
            logging.debug(f"Found arg ({before}) : {arg}")
            final[before] = arg
            before = False
            continue
        value = arg_dict.get(arg, None)
        if(not value is None):
            before = value
    return final
    
class Beer_programming():
    def __init__(self, ip:str=None, port:int=12412, player_num:int=2):
        self.serv = Server.Server(ip, int(port), order_dict=
                                {"--add_player":self.add_player,
                                "--send_players":self.send_players})
        
        self.players = Manager().dict()
        
        self.serv.listen_connections(int(player_num))
        
        print("Good process")
        print(self.players)
        import time
        
        while(True):
            time.sleep(5)
            print(self.players)
        
    def play(self): pass
        
    def add_player(self, port:int, name:str):
        self.players[port] = name

    def send_players(self, port:int):
        self.serv._p_obj_from_port[port].sendall(str(self.players))
        
if __name__ == "__main__":
    main()