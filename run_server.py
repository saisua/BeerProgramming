import Server
import logging
from multiprocessing import Process, Manager
from re import finditer, sub

import time, datetime

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
                        compile_time:int=240, 
                        drinks_per_error:"(float,function)"=(1,lambda x: x)):
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
        self.compile_at = None
        self.drinks_per_error = drinks_per_error

        self.end = Manager().list([False])

        self.conn_step = [";;"]
        self.conn_symbols = {"Serv_to_Client":";;", "Client_to_Serv":"::",
                                "Serv_listen":"->", "Serv_send":"<_",
                                "Client_listen":"<-", "Client_send":"<_",
                                "Urgency":"!!", "Evaluate":"#"}

        self.chat = Manager().list()
        self.serv.listen_connections(int(player_num))
        
    def __play(self, addr:tuple):
        logging.debug(f"__play({addr})")

        while(len(self.conn_step)):

            step = self.conn_step[0]
            self.conn_step.pop(0)

            if(step == self.conn_symbols["Serv_to_Client"] or step == self.conn_symbols["Serv_send"]):
                decoded_data = input("> ")
                if(step == self.conn_symbols["Evaluate"]): decoded_data = eval(decoded_data)

                self.symbol_parse(decoded_data)
                
                self.serv.sendto(decoded_data,addr)
                
            elif(step == self.conn_symbols["Client_to_Serv"] or step == self.conn_symbols["Serv_listen"]):
                self.listen(addr)
            logging.debug(f"Conn_steps: {self.conn_step}")

    def play(self, addr:tuple):
        logging.debug(f"play({addr})")

        self.serv.sendto("--_start!!<-")

        while(not self.end[0]):
            if(self.conn_step[0] == ";;" or self.conn_step[0] == "<_"): self.conn_step.pop(0)
            self.sleep(compile_after=True)

    def symbol_parse(self, command:str):
        urgent = False
        num = 0
        for symbol in finditer('|'.join(self.conn_symbols.values()), command):
            if(symbol.group(0) == self.conn_symbols["Urgency"]):
                urgent = True
            else:
                if(urgent):
                    self.conn_step.insert(num, symbol.group(0))
                    urgent = False
                    num += 1
                else:
                    self.conn_step.append(symbol.group(0))
        
    def listen(self, addr:tuple, max_timeout:float=None):
        if(addr is None): return
        
        timeout = 0

        if(max_timeout is None):
            max_timeout = datetime.datetime.now() + datetime.timedelta(days=99999999)
        else:
            max_timeout = datetime.datetime.now() + datetime.timedelta(seconds=int(max_timeout), 
                            milliseconds=int(max_timeout*1000%1000))

        while(datetime.datetime.now() < max_timeout):
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
        
                self.symbol_parse(decoded_data)

                decoded_data = sub('|'.join(self.conn_symbols.values()),'',decoded_data)

                self.serv.parse_data(decoded_data, addr)
                break
        

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
            self.serv.sendto(f"--add_player;{player}{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}", addr)
        self.serv.sendto(f"--add_player;{players[-1]}", addr)
        
    def add_chat(self, addr:tuple, text:str):
        self.chat.append([addr, text])
        
    def send_chat(self, addr:tuple, last:int=0):
        if(last >= len(self.chat) or last < 0): return
        for mssg in self.chat[last:-1]:
            self.serv.sendto(f"--add_chat;{mssg}{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}",addr)
        self.serv.sendto(f"--add_chat;{self.chat[-1]}",addr)
        
    def drink(self, addr:tuple, drinks:int=1):
        print(f"Player {addr} drinks {drinks}")
        self.players_drinks[addr] += int(drinks)
        self.players_last_drink[addr] = int(drinks)

        #Later it can be modified by a lambda
        self.serv.sendto(f"--drink;{drinks}",addr)

    def sleep(self, sleep_time:float=None, compile_after:bool=False, **kwargs):
        if(sleep_time is None): 
            if(self.compile_at is None):
                self.compile_at = datetime.datetime.now() + datetime.timedelta(seconds=self.compile_time)
            
            sleep_time = self.compile_at - datetime.datetime.now()

        time.sleep(sleep_time)
        if(compile_after):
            self.listen(kwargs.get("addr",None), max_timeout=5)
            self.serv.sendall(f"--compile{self.conn_symbols['Urgency']}{self.conn_symbols['Server_listen']}")


if __name__ == "__main__":
    main()
