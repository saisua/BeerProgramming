import Server
import logging
import multiprocessing_logging
from multiprocessing import Process, Manager
from re import finditer, sub

from time import sleep

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
    def __init__(self, ip:str=None, port:int=12412, player_num:int=1, 
                        compile_time:int=240):
        self.serv = Server.Server(ip, int(port), order_dict=
                                {"--add_player":self.add_player,
                                "--send_players":self.send_players,
                                "--chat":self.add_chat,"--send_chat":self.send_chat,
                                "--play":self.play,
                                "--drink":self.drink})
        
        self.players = Manager().dict()
        self.players_drinks = Manager().dict()
        self.players_last_drink = Manager().dict()

        self.compile_time = compile_time

        self.last_state = ';;'

        self.chat = Manager().list()
        self.serv.listen_connections(int(player_num))
        
    def play(self, addr:tuple):
        logging.debug(f"play({addr})")
        new_order = self.last_state
        while(new_order):
            order,new_order = new_order,''
            for meta in finditer(";;|->|::|</+",order):
                if(meta.group(0) == ";;" or meta.group(0) == "<+"):
                    new_order = input("> ")
                    if(new_order[0] =="#"): new_order = eval(new_order)
                    
                    self.serv.sendto(new_order,addr)
                else: #if(meta.group(0) == "->"):
                    timeout = 0
                    while(True):
                        data = self.serv._client_from_addr[addr].recv(1024)
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
                    
                            new_order += decoded_data

                            logging.debug(f"Decoded data: {decoded_data}")

                            decoded_data = sub("<-|->|::|[</+]|[/+>]",'',decoded_data)

                            self.serv.parse_data(decoded_data, addr)
                            break
            else: 
                self.last_state = meta.group(0)
                logging.debug(f"Last state set to {self.last_state}")
    
    def set_state(self, state:str):
        self.last_state = state.replace(' ','')
        
    # Ausiàs cabro pegali a ton pare

    # Game related functions

    def add_player(self, addr:tuple, name:str):
        self.players[addr] = name
        exists = self.players_drinks.get(addr, None)
        if(exists is None):
            self.players_drinks[addr] = 0
            self.players_last_drink[addr] = False

    def send_players(self, addr:tuple, last:int=0):
        players = list(self.players.items())
        if(last >= len(players) or last < 0): return
        for player in players[last:-1]:
            self.serv.sendto(f"--add_player;{player};;", addr)
        self.serv.sendto(f"--add_player;{players[-1]}", addr)
        
    def add_chat(self, addr:tuple, text:str):
        self.chat.append([addr, text])
        
    def send_chat(self, addr:tuple, last:int=0):
        if(last >= len(self.chat) or last < 0): return
        for mssg in self.chat[last:-1]:
            self.serv.sendto(f"--add_chat;{mssg};;",addr)
        self.serv.sendto(f"--add_chat;{self.chat[-1]}",addr)
        
    def drink(self, addr:tuple, drinks:int=1):
        print(f"Player {addr} drinks {drinks}")
        self.players_drinks[addr] += int(drinks)
        self.players_last_drink[addr] = int(drinks)

        #Later it can be modified by a lambda
        self.serv.sendto(f"--drink;{drinks}",addr)

    def sleep(self):
        pass #self.

if __name__ == "__main__":
    main()
