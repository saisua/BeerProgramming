import Client , front
from wx import App
from multiprocessing import Process
import logging
import multiprocessing_logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
from re import finditer, sub
import time

def main():
    multiprocessing_logging.install_mp_handler()
    logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.DEBUG)
    from sys import argv
    Beer_programming(**arg_parse(argv)).play(False)

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

        self.last_state = ';;'

        if(not ip is None): self.connect(ip,port)
        else: self.connect("127.0.0.1", port)

    def play(self, gui:bool=True) -> None:
        logging.debug(f"BeerProgramming.play(self, {gui})")
        name = False
        while(not name):
            name = input("In-game alias: ")
            name = name if input("Confirm?[Y/n] ").lower() in ["y","ye","yes","s","si"] else False
        self.name = name
        
        self.client.send_to_server(f"--add_player;{name}")
        logging.debug("Sent alias to server")
        self.client.send_to_server("--play;;")
        logging.debug("Sent play petition to server")
    
        #self.start_compiler()
    
        if(gui): 
            play_pro = Process(target=self._play_process)
            play_pro.start()
            self.gui()
            play_pro.join()
        else: self._play_process()
            
    def _play_process(self) -> None:
        new_order = self.last_state
        while(new_order):
            order,new_order = new_order,''
            for meta in finditer(";;|<-|::|/+>",order):
                if(meta.group(0) == "<-" or meta.group(0) == "::"):
                    new_order += input("> ")
                    if(new_order[0] =="#"): new_order = eval(new_order)

                    self.client.send_to_server(new_order)
                else: #if(meta.group(0) == ";;"):
                    decoded_data = self.listen()

                    new_order += decoded_data

                    logging.debug(f"Decoded_data: {decoded_data}")

                    decoded_data = sub("<-|->|::|[</+]|[/+>]",'',decoded_data)

                    self.parse_data(decoded_data)
                    break
            else: 
                self.last_state = meta.group(0)
                logging.debug(f"Last state set to {self.last_state}")

    def connect(self, ip:str, port:int=12412) -> None:
        logging.debug(f"BeerProgramming.connect(self, {ip}, {port})")
        self.listener = self.client.connect(ip,port)

    def listen(self, listener:"generator"=None)-> str:
        #logging.debug(f"BeerProgramming.listen(self, {listener})")
        if(listener is None):
            if(self.listener is None): return
            listener = self.listener

        return(next(listener))
        
    def gui(self):
        logging.debug("BeerProgramming.gui(self)")
        app = App()
        
        frame = front.Frame(name="Beer Programming")
        panel = frame.new_panel(bgcolor=(50,50,50))
        
        player_panel =  panel.new_panel("(%0.49,%1)")
        chat_panel = panel.new_panel("(%0.49,%1)","(%0.51,0)")
        
        self.text_list = {self.name:panel.add_text((0,0),"(%1,%0.2)", self.name)}
        
        app.MainLoop()
        
    def start_compiler(self) -> None:
        firefox_capabilities = DesiredCapabilities.FIREFOX
        firefox_capabilities['marionette'] = True

        options = webdriver.firefox.options.Options()
        
        profile = webdriver.FirefoxProfile()
        
        logging.info("Configuration complete. Trying to run the drivers. This could take some time...")
        self.driver = webdriver.Firefox(executable_path=(
                __file__).replace("play.py", "geckodriver"),
                options=options, firefox_profile=profile) #firefox_binary=binary,
        logging.info("Drivers ran succesfully!")
        
        self.driver.get("https://www.onlinegdb.com/online_java_compiler")
        self.tab = self.driver.current_window_handle
        
        self.driver.find_element_by_xpath("//*[@class='glyphicon glyphicon-menu-left']").click()


    def parse_data(self, data:str):
        #print(f"parse_data {data}")
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
        

    # Game related functions

    def compile(self) -> int:
        self.driver.switch_to.window(self.tab)
        
        self.driver.find_element_by_xpath("//*[@class='glyphicon glyphicon-play']").click()
        
        time.sleep(3)
        
        self.driver.switch_to.window(self.tab)
        
        try:
            self.client.send_to_server(f"--drink;{len(self.driver.find_elements_by_xpath('''//*[@class='error_line']'''))}")
        except:
            self.client.send_to_server(f'--drink;0')

    def drink(self, drinks:str='0'):
        logging.info(f"Recieved order to drink {drinks} times")
        self.driver.execute_script(f"alert('Drink {drinks} times');", [])        
        
    def add_player(self, player:"str(addr, name)"):
        addr, name = eval(player)
        logging.info(f"Added new player {name} ({addr})")
        self.players[addr] = name

    def add_chat(self, text:str):
        self.chat.append(eval(text))

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
