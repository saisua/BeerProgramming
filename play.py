import Client #, front
#from wx import App
from multiprocessing import Process
import logging
import multiprocessing_logging

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
        
        self.orders = {""}

        if(not ip is None): self.connect(ip,port)

    def play(self, gui:bool=True):
        logging.debug(f"BeerProgramming.play(self, {gui})")
        name = False
        while(not name):
            name = input("In-game alias: ")
            name = name if input("Confirm?[Y/n] ").lower() in ["y","ye","yes","s","si"] else False
        self.name = name
        
        self.client.send_to_server(f"--add_player;{name}")
        logging.debug("Sent alias to server")
    
        if(gui): 
            play_pro = Process(target=self._play_process)
            play_pro.start()
            self.gui()
            play_pro.join()
        else: self._play_process()
            
    def _play_process(self):
        order = -1
        while(order != 'end'):
            order = input("> ")
            self.client.send_to_server(order)
            while(";;" in order):
                order = order.replace(";;",';')
                try:
                    order = self.listen()
                
                except: pass
                
                print(order)

    def connect(self, ip:str, port:int=12412):
        logging.debug(f"BeerProgramming.connect(self, {ip}, {port})")
        self.listener = self.client.connect(ip,port)

    def listen(self, listener:"generator"=None):
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
        
if __name__ == "__main__":
    main()
