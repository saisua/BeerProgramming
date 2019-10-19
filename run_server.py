import Server #, front
import logging
#from wx import App
from multiprocessing import Process, Manager
from re import finditer, sub

import time, datetime

# This function gets executed when you run
# python run_server.py and its use is to deploy
# the main server used in Beer_Programming
def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    from sys import argv
    Beer_programming(gui=False,**arg_parse(argv)).play()

# arg_parse does take a list of arguments and returns
# one dict with the parameters and values (str) determined
# by the keys and values of arg_dict
# if one key is found, the following argument is
# chosen as a value
def arg_parse(args:list, arg_dict:dict=
        {"--ip":"ip","--port":"port",   
         "-i":"ip","-p":"port",
         "-pl":"player_num",
         "--players":"player_num",
         "-t":"compile_time",
         "--time":"compile_time",
         "-dpe":"drinks_per_error",
         "--drinks_per_error":"drinks_per_error"}) -> dict:
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
    
"""
    The class Beer_programming is the main class used to
    play the game. It will create the server to which the
    clients will connect to. Between its features, it will
    mostly stay still until it is time for the users to
    compile, and then it will send them the order to do so,
    until someone finishes.
"""
class Beer_programming():
    def __init__(self, ip:str=None, port:int=12412, player_num:int=1, 
                        compile_time:int=240, gui:bool=True,
                        drinks_per_error:"(float,function)"=(1,round)):
        self.serv = Server.Server(ip, int(port), order_dict=
                                {"--add_player":self.add_player,
                                "--send_players":self.send_players,
                                "--chat":self.add_chat,"--send_chat":self.send_chat,
                                "--play":self.play,
                                "--drink":self.drink})
        
        self.players = Manager().dict()
        self.players_drinks = Manager().dict()
        self.players_last_drink = Manager().dict()
        
        self.compile_time = float(compile_time)
        self.compile_at = Manager().list()

        if(type(drinks_per_error) is str): drinks_per_error = eval(drinks_per_error)
        if(not hasattr(drinks_per_error, '__iter__')):
            drinks_per_error = (float(drinks_per_error), round)

        self.drinks_per_error = drinks_per_error

        self.end = Manager().list([False])

        self.conn_step = [";;"]
        self.conn_symbols = {"Serv_to_Client":";;", "Client_to_Serv":"::",
                                "Serv_listen":"->", "Serv_send":"<_",
                                "Client_listen":"<-", "Client_send":"<_",
                                "Urgency":"!!", "Evaluate":"#"}

        self.chat = Manager().list()

        if(gui): self.gui()

        self.serv.listen_connections(int(player_num))
        
    # __play has debugging purposes, and it allows the
    # user to send the server direct orders
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

    # play is the main function that shold be run to
    # ensure the game is automatic and no problems arise.
    # It will first ask the users to open an instance of
    # the compiler
    def play(self, addr:tuple):
        logging.debug(f"play({addr})")

        self.serv.sendto("--_start!!<-", addr)

        self.listen(addr)

        while(not self.end[0]):
            if(self.conn_step[0] == ";;" or self.conn_step[0] == "<_"): self.conn_step.pop(0)
            self.sleep(compile_after=True, addr=addr)

    # symbol_parse is used by the user and the client
    # to tell (into a queue) what the Server should do
    # next (listen/send something)
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

    # listen does wait for the client in addr to send data
    # which then is parsed and executed if it matches any
    # order_dict key
    def listen(self, addr:tuple, max_timeout:float=None):
        if(addr is None): return
        
        timeout = 0

        if(max_timeout is None):
            max_timeout = datetime.datetime.now() + datetime.timedelta(days=30)
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

    #
    # Game related functions
    #

    # add_player adds to self.players the alias given
    # by the player with the key being the sender's address
    # if the player did not exist, it gets assigned
    # to 0 the record of drinks haven
    def add_player(self, addr:tuple, name:str):
        self.players[addr] = name
        if(self.players_drinks.get(addr, None) is None):
            self.players_drinks[addr] = 0
            self.players_last_drink[addr] = False

    # send_players is a mean for the clients to keep
    # the record of players updated. It will send to
    # the client the order to add/overwrite the name
    # of all players asked. Making use of python's dict
    # being ordered structures, it is possible to ask only
    # all players that came after number {last}, to reduce
    # the amount of data to send in cases where there's
    # a lot of players
    def send_players(self, addr:tuple, last:int=0):
        players = list(self.players.items())
        if(last >= len(players) or last < 0): return
        for player in players[last:-1]:
            self.serv.sendto(f"--add_player;{player}{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}", addr)
        self.serv.sendto(f"--add_player;{players[-1]}", addr)
        
    # add_chat will add an entry into the self.chat list
    # with a tuple containing the address of the sender
    # and the message he/she sent
    def add_chat(self, addr:tuple, text:str):
        self.chat.append((addr, text))
        
    # send_chat will send the client in addr all chat entries
    # from {last}
    def send_chat(self, addr:tuple, last:int=0):
        if(last >= len(self.chat) or last < 0): return
        for mssg in self.chat[last:-1]:
            self.serv.sendto(f"--add_chat;{mssg}{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}",addr)
        self.serv.sendto(f"--add_chat;{self.chat[-1]}",addr)
        
    # drink is a function executed by the client to add as a
    # record how many drink has an user had.
    # It also does send back the client to tell the user
    # what to drink
    def drink(self, addr:tuple, drinks:int=1):
        drinks = self.drinks_per_error[1](drinks*
                 self.drinks_per_error[0])

        print(f"Player {addr} drinks {drinks}")

        self.players_drinks[addr] += int(drinks)
        self.players_last_drink[addr] = int(drinks)

        self.serv.sendto(f"--drink;{drinks}",addr)

    # sleep (kind of) overloads the time.sleep in order to
    # make the process sleep but until the time defined by
    # the server (stored in self.compile_at[0]) and to
    # tell the client to compile if {compile_after}
    def sleep(self, sleep_time:float=None, compile_after:bool=False, addr:tuple=None):
        if(sleep_time is None): 
            if(not len(self.compile_at)):
                self.compile_at.append(datetime.datetime.now() + datetime.timedelta(seconds=self.compile_time)) 
            elif(self.compile_at[0] < datetime.datetime.now()):
                self.compile_at[0] = datetime.datetime.now() + datetime.timedelta(seconds=self.compile_time)
            
            sleep_time = (self.compile_at[0] - datetime.datetime.now()).seconds

        logging.info(f"Sleeping for {sleep_time} seconds.")

        time.sleep(sleep_time)
        if(compile_after):
            self.serv.sendto(f"--compile{self.conn_symbols['Client_listen']}{self.conn_symbols['Client_listen']}", addr)
            self.listen(addr, max_timeout=5)

    # gui is used for displaying the connected users if
    # the server device has a display attached to it
    def gui(self):
        logging.debug("BeerProgramming.gui(self)")
        """
        app = App()
        
        frame = front.Frame(name="Beer Programming")
        panel = frame.new_panel(bgcolor=(50,50,50))
        
        player_panel =  panel.new_panel("(%0.49,%1)")
        chat_panel = panel.new_panel("(%0.49,%1)","(%0.51,0)")
        
        self.text_list = {self.name:panel.add_text((0,0),"(%1,%0.2)", self.name)}
        
        app.MainLoop()
        """

if __name__ == "__main__":
    main()
