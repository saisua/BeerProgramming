import Server
import logging
import multiprocessing_logging
from multiprocessing import Process, Manager

import time

def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    from sys import argv
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
    def __init__(self, ip:str=None, port:int=12412, player_num:int=1):
        self.serv = Server.Server(ip, int(port), order_dict=
                                {"--add_player":self.add_player,
                                "--send_players":self.send_players,
                                "--chat":self.add_chat,"--send_chat":self.send_chat,
                                "--play":self.play})
        
        self.players = Manager().dict()
        
        self.chat = Manager().list()
        self.serv.listen_connections(int(player_num))
        
    def play(self, addr:tuple):
        order = -1
        while(order != 'exit'):
            try:
                order = input("> ")
                self.serv.sendto(order,addr)
            except: pass
            print(order)
        
    def add_player(self, addr:tuple, name:str):
        self.players[addr] = name

    def send_players(self, addr:tuple):
        self.serv.sendto(self.players, addr)
        
    def add_chat(self, addr:tuple, text:str):
        self.chat.append([addr, text])
        
    def send_chat(self, addr:tuple, last:int=0):
        if(last >= len(self.chat) or last < 0): return
        for mssg in self.chat[last:-1]:
            self.serv.sendto(f"{mssg};;",addr)
        self.serv.sendto(self.chat[-1],addr)
        
        
if __name__ == "__main__":
    main()
