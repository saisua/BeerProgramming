import Client , front
from wx import App
from multiprocessing import Process
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoAlertPresentException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
from re import finditer, sub
import time

# This function gets executed when you run
# python play.py and it serves as a way to run
# the Beer_programming client and parse the user's
# arguments
def main():
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    from sys import argv
    Beer_programming(**arg_parse(argv)).play(False)

# arg_parse does take a list of arguments and returns
# one dict with the parameters and values (str) determined
# by the keys and values of arg_dict
# if one key is found, the following argument is
# chosen as a value
def arg_parse(args:list, arg_dict:dict=
        {"--ip":"ip","--port":"port",
         "-i":"ip","-p":"port"}) -> dict:
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
    play the game. It will create a Client, who will then
    connect to the server, which will rule the game.
    Between its features there is the possibility to
    run and compile the chosen online compiler, and to
    chat (unused)
"""
class Beer_programming():
    def __init__(self, ip:str=None, port:int=12412):
        logging.debug(f"BeerProgramming.__init__(self,{ip},{port})")
        self.client = Client.Client()
        self.listener = None
        
        self.order_dict = {"--compile":self.compile,
                            "--drink":self.drink,
                            "--add_player":self.add_player,
                            "--add_chat":self.add_chat,

                            "--_print":self.__print_gui,
                            "--_start":self.start_compiler}

        self.players = {}
        self.chat = []
        self.drinks = 0

        self.conn_step = [";;"]
        self.conn_symbols = {"Serv_to_Client":";;", "Client_to_Serv":"::",
                                "Serv_listen":"->", "Serv_send":"<_",
                                "Client_listen":"<-", "Client_send":"<_",
                                "Urgency":"!!", "Evaluate":"#"}

        if(not ip is None): self.connect(ip,port)
        else: self.connect("127.0.0.1", port)

    # The play function should be the first function to be
    # executed when the server starts to listen to the socket.
    # When executed, play will send the server the order to
    # add itself as a named user, will ask the server
    # what are the names of the other players and then it
    # will give the server the control.
    # play can open a gui(unused) and will then run
    # _play_process
    def play(self, gui:bool=True) -> None:
        logging.debug(f"BeerProgramming.play(self, {gui})")
        name = False
        while(not name):
            name = input("In-game alias: ")
            name = name if input("Confirm?[Y/n] ").lower() in ["y","ye","yes","s","si"] else False
        self.name = name
        
        self.client.send_to_server(f"--add_player;{name}{self.conn_symbols['Client_to_Serv']}")
        logging.debug("Sent alias to server")
        self.client.send_to_server(f"--play{self.conn_symbols['Serv_to_Client']}")
        logging.debug("Sent play petition to server")
    
        #self.start_compiler()
    
        if(gui): 
            play_pro = Process(target=self._play_process)
            play_pro.start()
            self.gui()
            play_pro.join()
        else: self._play_process()
            
    # _play_process is the main function to interactuate
    # with the server. Based on the actual state of the
    # Beer_programming.conn_steps queue it will either
    # listen or ask what to send to the server.
    # It's the server's job to determine if it should or
    # shoul not need the user's input
    def _play_process(self) -> None:
        while(len(self.conn_step)):
            
            step = self.conn_step[0]
            self.conn_step.pop(0)

            if(step == self.conn_symbols["Client_to_Serv"] or step == self.conn_symbols["Client_send"]):
                decoded_data = input("> ")
                if(step == self.conn_symbols["Evaluate"]): decoded_data = eval(decoded_data)

                self.symbol_parse(decoded_data)
                
                self.client.send_to_server(decoded_data)
            elif(step == self.conn_symbols["Serv_to_Client"] or step == self.conn_symbols["Client_listen"]):
                decoded_data = self.listen()

                logging.info(f"Recived data '{decoded_data}' from server")
        
                self.symbol_parse(decoded_data)

                decoded_data = sub(f'|'.join(self.conn_symbols.values()),'',decoded_data)

                self.data_parse(decoded_data)
                    
            logging.debug(f"Conn_steps: {self.conn_step}")

    # connect (kind of) overrides Client.connect. Even if
    # unnecessary, I think this function makes the code
    # cleaner
    def connect(self, ip:str, port:int=12412) -> None:
        logging.debug(f"BeerProgramming.connect(self, {ip}, {port})")
        self.listener = self.client.connect(ip,port)

    # listen does make use of the Client's generator to
    # listen to the server and return a string
    def listen(self, listener:"generator"=None) -> str:
        #logging.debug(f"BeerProgramming.listen(self, {listener})")
        if(listener is None):
            if(self.listener is None): return
            listener = self.listener

        return(next(listener))
        
    # (unused) gui does open a gui for the user to see
    # all clients connected and chat with them
    def gui(self) -> None:
        logging.debug("BeerProgramming.gui(self)")
        app = App()
        
        frame = front.Frame(name="Beer Programming")
        panel = frame.new_panel(bgcolor=(50,50,50))
        
        player_panel =  panel.new_panel("(%0.49,%1)")
        chat_panel = panel.new_panel("(%0.49,%1)","(%0.51,0)")
        
        self.text_list = {self.name:panel.add_text((0,0),"(%1,%0.2)", self.name)}
        
        app.MainLoop()
        
    # start_compiler does start a new selenium instance (gecko)
    # controlled by the game to make sure nobody can cheat
    # with (at least) one saved file
    def start_compiler(self) -> None:
        logging.info("Configuration complete. Trying to run the drivers. This could take some time...")
        self.driver = webdriver.Firefox(executable_path=(
                __file__).replace("play.py", "geckodriver"))
                #options=options, firefox_profile=profile,# capabilities=firefox_capabilities, 
                #firefox_binary=FirefoxBinary((__file__).replace("play.py", "geckodriver")))
        logging.info("Drivers ran succesfully!")
        
        self.driver.get("https://www.onlinegdb.com/online_java_compiler")
        self.tab = self.driver.current_window_handle
        
        self.driver.find_element_by_xpath("//*[@class='glyphicon glyphicon-menu-left']").click()

        self.client.send_to_server("Done")

    # data_parse takes any message sent by the server
    # and it executes the function assigned as key
    # in the self.order_dict dictionary
    def data_parse(self, data:str) -> None:
        #print(f"data_parse {data}")
        order = None
        args = ()
        for arg in data.split(';'):
            new_ord = self.order_dict.get(arg.strip(), None)
            print(f"arg:{arg}, new_ord:{new_ord}")
            if(not new_ord is None):
                if(not order is None): 
                    print(f"{order}{args}")
                    try:
                        order(*args)
                    except Exception as err: print(f"ERROR: {err}")
                    
                order = new_ord
                args = ()
                
            elif(arg.strip() != ''): args+=(arg.strip(),)
            
        if(not order is None): 
            print(f"{order}{args}.")
            try:
                order(*args)
            except Exception as err:
                print(order)
                print(args)
                raise err
                print(f"ERROR: {err}.")

    # symbol_parse is used by the user and the server
    # to tell (into a queue) what the Client should do
    # next (listen/send something)
    def symbol_parse(self, command:str):
        urgent = False
        num = 0 
        for symbol in finditer('|'.join(self.conn_symbols.values()), command):
            if(symbol.group(0) == self.conn_symbols["Urgency"]):
                urgent = True
            else:
                if(urgent):
                    self.conn_step.insert(0, symbol.group(0))
                    urgent = False
                    num += 1
                else:
                    self.conn_step.append(symbol.group(0))
        
    #
    # Game related functions
    #

    # compile will make use of the selenium instance to
    # try to compile the code. Any error in the code will
    # be sent to the server, who will answer how
    # many times will have the user to drink
    def compile(self) -> int:
        self.driver.switch_to.window(self.tab)

        try: self.driver.switch_to.alert.dismiss()
        except NoAlertPresentException: pass

        while(True):
            try: 
                self.driver.switch_to.window(self.tab)

                self.driver.find_element_by_xpath("//*[@class='glyphicon glyphicon-play']").click()
                
                break
            except: pass

        time.sleep(3)
        
        self.driver.switch_to.window(self.tab)
        
        try:
            self.client.send_to_server(f"--drink;{len(self.driver.find_elements_by_xpath('''//*[@class='error_line']'''))}"
                                        f"{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}")
        except:
            self.client.send_to_server(f"--drink;0{self.conn_symbols['Urgency']}{self.conn_symbols['Client_listen']}")

        self.driver.switch_to.window(self.tab)

        try: self.driver.find_elements_by_xpath('''//*[@class='glyphicon glyphicon-stop']''').click()
        except: pass

    # drink will be executed by the server when the code is
    # compiled. It will then tell the user how many times
    # it should drink
    def drink(self, drinks:str='0'):
        logging.info(f"Recieved order to drink {drinks} times")
        self.driver.execute_script(f"alert('Drink {drinks} times');", [])        
        
    # add_player will record a new player, when given by the
    # server. It is meant to have the utility of listing
    # all users avaliable to chat with
    def add_player(self, player:"str(addr, name)"):
        addr, name = eval(player)
        logging.info(f"Added new player {name} ({addr})")
        self.players[addr] = name

    # add_chat adds a new message to the chat list
    def add_chat(self, text:str):
        self.chat.append(eval(text))

    # __print_gui is a debugging function that prints all
    # server-recieved variables
    def __print_gui(self):
        print()
        print(f"Chat: {self.chat}")
        print()
        print(f"Players: {self.players}")
        print()
        print(f"Drinks:{self.drinks}")
        print()
        
if __name__ == "__main__":
    main()