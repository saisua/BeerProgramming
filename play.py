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

def main():
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

        self.conn_step = [";;"]
        self.conn_symbols = {"Serv_to_Client":";;", "Client_to_Serv":"::",
                                "Serv_listen":"->", "Serv_send":"<_",
                                "Client_listen":"<-", "Client_send":"<_",
                                "Urgency":"!!", "Evaluate":"#"}

        if(not ip is None): self.connect(ip,port)
        else: self.connect("127.0.0.1", port)

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

    def data_parse(self, data:str):
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
        

    # Game related functions

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
