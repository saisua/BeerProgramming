# Imports
import logging, wx
from re import split as multisplit
from cv2 import imread

# Main function for testing
def __main():
    # level = logging. + [CRITICAL, ERROR, WARNING, INFO, DEBUGGING]
    logging.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logging.DEBUG)

    return

    app = wx.App()
    frame = Frame(name="Un xicotet test", size=(1000,700))
    #panel = frame.new_panel(bgcolor=(50,50,50))
    winsize = frame._size
    
    #panel = frame.new_panel((winsize[0],40),bgcolor=(255,0,0))
    #panel.add_text("Un petit test", (0,0), (300,100),font=wx.Font(37,wx.ROMAN,wx.NORMAL,wx.NORMAL))
    #panel = frame.new_panel((300,400),(0,41),(170,170,170),(0,600))
    #panel.add_checkbox("Did i say it was a test?", (10, 50), (200,180), on_click=lambda ev: print(ev))
    #but = panel.add_button("Try it out", (20, 250),(160,50), on_click=lambda ev: print(ev))
    #but.Bind(wx.EVT_ENTER_WINDOW, (lambda ev: ev.GetEventObject().SetLabelText("Tested :P")))
    #but.Bind(wx.EVT_LEAVE_WINDOW, (lambda ev: ev.GetEventObject().SetLabelText("Try it out")))
    

    panel = frame.new_panel("(_size[0],@350)", "(0,@41)")
    panel.add_textbox(f"(@{panel.Size.x/2},0)", f"(@{panel.Size.x/2},@{panel.Size.y})", "Editable test", on_event=lambda e: print(f"User pressed enter. | {e.String} \n               END  |"))

    panel.add_image("Special.PNG",(0,0),f"(@{panel.Size.x/2},@{panel.Size.y})")

    panel = frame.new_panel("(_size[0]-@320,20+@20)", "(@300,@391)")
    panel.add_textbox((0,0), f"(@{panel.Size.x},{panel.Size.y/2}+@{panel.Size.y/2})", "Editable password", hidden = True, on_event=lambda e: print(f"User password | {e.String}"))


    app.MainLoop()

# Not typing hints 'cause is just a test funct




"""
    The class Frame creates a new empty window. To add widgets such as
    buttons you have to first run Frame.new_panel and use the object
    it returns to draw those widgets. The first panel may not follow size arg
    but you can stack panels on top of each other.
"""
class Frame(wx.Frame):
    def __init__(self, parent:wx.Frame=None, name:str="New frame", size:tuple=None, resizable:bool=True):
        logging.info("New Frame(wx.Frame) created.")
        logging.debug(f"Frame.__init__(self, {parent}, {name}, {size})")

        self._parent = parent
        if(not parent is None): self.__parent_size = parent._size

        # Check size format
        if(size is None or (type(size) != tuple and type(size) != list) or len(size) != 2):
            logging.warning("Looks like size was either not set or in a wrong format\n"
                        f"      size={size}")

            size = wx.DisplaySize()

        self.__class__.__base__.__init__(self, parent, -1, name, (0,0), size)

        if(not resizable):
            pass
        else: self.Bind(wx.EVT_SIZE, lambda _: self.__resize__())


        self.windows = []
        self.panels = []

        self.Show(True)

    # Creates a new unique window, child of parent. It returns a Frame
    # object becaue all windows are Frames
    def new_window(self,size:tuple=None, resizable:bool=True, parent:object=None) -> 'Frame':
        logging.debug(f"Frame.new_window(self, {size}, {parent})")

        if(parent is None): parent = self
        if(size is None): size = self._size

        self.windows.append(Frame(parent, size=size, resizable=resizable))
        self.windows[-1].Show()
        return self.windows[-1]

    # new_panel creates a canvas inside the Frame. It returns a Panel object
    # which has functions to create and draw widgets
    def new_panel(self, size:tuple=None, location:tuple=(0,0),
                        bgcolor:tuple=(90,90,90), scrollbarsxy_size:tuple=False, scrollbarsxy_extend:tuple=0,
                        style:"style1 | style2"=wx.BORDER_THEME, resizable:bool=True,
                        name:str='', allow_files_drop:bool=False, parent:object=None) -> 'Panel':
        logging.debug(f"Frame.new_panel(self, {size}, {location}, {bgcolor}, {scrollbarsxy_size},"
                                f" {scrollbarsxy_extend}, {style}, {resizable}, {name}, {allow_files_drop},"
                                f" {parent})")

        if(parent is None): parent = self
        if(size is None): size = self._size

        self.panels.append(Panel(parent, size, location, bgcolor, scrollbarsxy_size, scrollbarsxy_extend,
                                        style, resizable, name, allow_files_drop)) 
        return self.panels[-1]

    
    @property
    def _size(self) -> tuple:
        return (self.Size.x, self.Size.y)

    # Function to resize all marked as resizable
    def __resize__(self) -> None:
        for panel in self.panels:
            panel.__resize__()



"""
    The Panel object is the canvas of a Frame object and should
    have a wx.Frame object as a parent. The functions here are
    written to create locally (in self Panel) widgets.
"""
class Panel(wx.ScrolledWindow):
    def __init__(self, parent:wx.Frame, size:tuple, location:tuple=(0,0), bgcolor:tuple=(90,90,90),
                        scrollbarsxy_size:tuple=False, scrollbarsxy_extend:tuple=0,
                        style:"style1 | style2"=wx.BORDER_THEME,
                        resizable:tuple=True, name:str='', allow_files_drop:bool=False):
        logging.info("New Panel(wx.ScrolledWindow) created.")
        logging.debug(f"Panel.__init__(self, {parent}, {size}, {location}, {bgcolor}, {scrollbarsxy_size}, "
                        f"{scrollbarsxy_extend}, {style}, {resizable}, {name}, {allow_files_drop}")

        self._parent = parent
        self.name = name

        logging.debug(f"loc: {location} -> {self.check_format(location,False)} -> {self.check_format(location)}")
        logging.debug(f"siz: {size} -> {self.check_format(size,False)} -> {self.check_format(size)}")

        self.__class__.__base__.__init__(self, parent, -1, self.check_format(location), self.check_format(size), style)
        self.SetBackgroundColour(bgcolor)
        if(scrollbarsxy_size): 
            self.SetScrollbars(1,1,*scrollbarsxy_size)

            self.extend_scrollbar = scrollbarsxy_extend

            self.Bind(wx.EVT_SCROLL_BOTTOM, self.__extend_scrollbar__)
        
        self.resizable = resizable
        if(resizable):
            self.resize = self.check_format(size, False)
            self.relocate = self.check_format(location, False)

        self.Bind(wx.EVT_SCROLL, lambda _: self.Refresh())
        self.DragAcceptFiles(allow_files_drop)

        self.buttons = []
        self.text = []
        self.checkbox = []
        self.bitmaps = []
        self.textbox = []

        self.widgets_list = [self.buttons, self.text, self.checkbox,
                            self.bitmaps, self.textbox]

        self.panels = []

        # SetBackgroundColor won't work if this is not called
        self.Refresh()

    # new_panel creates a canvas inside the Panel parent.
    def new_panel(self, size:tuple=None, location:tuple=(0,0),
                        bgcolor:tuple=(90,90,90), scrollbarsxy_size:tuple=False, scrollbarsxy_extend:tuple=0, 
                        style:"style1 | style2"=wx.BORDER_THEME, resizable:bool=True,
                        name:str='', allow_files_drop:bool=False, parent:object=None) -> 'Panel':
        logging.debug(f"Parent.new_panel(self, {size}, {location}, {bgcolor}, {scrollbarsxy_size}, "
                                f"{scrollbarsxy_extend}, {style}, {resizable}, {name}, {allow_files_drop}, "
                                f"{parent}")

        if(parent is None): parent = self
        if(size is None): size = self._size

        #Do not chech_format since it is done in __init__
        self.panels.append(Panel(parent, size, location, bgcolor, scrollbarsxy_size, scrollbarsxy_extend, 
                                        style, resizable, name, allow_files_drop)) 
        return self.panels[-1]

    # Adds a button in the panel
    def add_button(self, label:str, location:tuple, size:tuple, on_click:"function", 
                            style:"style1 | style2"=0, parent:wx.Window=None) -> wx.Button:
        logging.debug(f"Panel.add_button(self, {label}, {location}, {size}"
                            f", {on_click}, {style}, {parent})")

        if(parent is None): parent = self

        self.buttons.append([wx.Button(parent, label=label, pos=self.check_format(location),
                                        size=self.check_format(size), style=style), 
                                        self.check_format(size,False), self.check_format(location,False)])

        self._parent.Bind(wx.EVT_BUTTON, on_click, self.buttons[-1][0])

        return self.buttons[-1][0]

    # Adds a text box in the panel
    def add_text(self, location:tuple, size:tuple, text:str, color:tuple=(0,0,0), 
                        bgcolor:tuple=None, font:wx.Font=None, 
                        style:"style1 | style2"=0, parent:wx.Window=None) -> wx.StaticText:
        logging.debug(f"Panel.add_text(self, {text}, {location}, {size},"
                                f"{color}, {bgcolor}, {font}, {style}, {parent})")

        if(parent is None): parent = self
        
        self.text.append([wx.StaticText(parent, -1, text, self.check_format(location),
                                        self.check_format(size), style), 
                                        self.check_format(size,False), self.check_format(location,False)])

        self.text[-1][0].SetForegroundColour(color) 
        if(not bgcolor is None): self.text[-1][0].SetBackgroundColour(bgcolor)
        if(not font is None): self.text[-1][0].SetFont(font) 

        return self.text[-1][0]

    # Add a writable text box
    def add_textbox(self, location:tuple, size:tuple, text:str='', 
                                style:"style1 | style2"=0, on_event:"function"=None, 
                                multiline:bool=True, hidden:bool=False, writable:bool=True,
                                event:"wx.EVT_TEXT"=wx.EVT_TEXT_ENTER,
                                parent:wx.Window=None) -> wx.TextCtrl:
        logging.debug(f"Panel.add_textbox(self, {location}, {size}, {text}, {style},"
                                f"{multiline}, {hidden}, {writable}, {event}, {parent})")

        if(parent is None): parent = self
        
        # Looks like you can't have a multiline password
        # (at least i can't nor care) maybe i'll retry it later
        if(hidden): 
            style = style | wx.TE_PASSWORD
        elif(multiline): style = style | wx.TE_MULTILINE
        elif(not writable): style = style | wx.TE_READONLY

        self.textbox.append([wx.TextCtrl(parent, -1, text, self.check_format(location), 
                                        self.check_format(size), style), 
                                        self.check_format(size,False), self.check_format(location,False)])

        if(not on_event is None):
            if(hidden and event == wx.EVT_TEXT_ENTER): event = wx.EVT_TEXT
            self.textbox[-1][0].Bind(event, on_event)

        return self.textbox[-1][0]

    # Adds a checkbox in the panel
    def add_checkbox(self, text:str, location:tuple, size:tuple, on_click:'function'=None,
                        style:'style1 | style2'=0, validator:wx.Validator=wx.Validator,
                        parent:wx.Window=None) -> wx.CheckBox:
        logging.debug(f"Panel.add_checkbox(self, {text}, {location}, {size},"
                                f"{on_click}, {style}, {validator}, {parent})")

        if(parent is None): parent = self
        
        self.checkbox.append([wx.CheckBox(parent, -1, text, self.check_format(location), 
                                            self.check_format(size), style), 
                                        self.check_format(size,False), self.check_format(location,False)])

        if(not on_click is None): self.checkbox[-1][0].Bind(wx.EVT_CHECKBOX, on_click)

        return self.checkbox[-1][0]

    # Adds an image as a StaticBitmap in the frame
    def add_image(self, location:tuple, size:tuple, image_path:"str(path)"="None.jpg",
                            style:"style1 | style2"=wx.Center, allow_files_drop:bool=False,
                            multiimage:bool=True, parent:wx.Window=None, menu:bool=True,
                            bitmap_images:list=[]) -> wx.StaticBitmap:
        logging.debug(f"Panel.add_image(self, {image_path}, {location}, {size}, {style}, {parent})")

        if(parent is None): parent = self
        if(menu): size = f"{str(size[:-1])}-@30)"

        self.bitmaps.append([Image_container(self, location, size, style, image_path, menu, bitmap_images), 
                                self.check_format(size,False), self.check_format(location,False)])

        if(allow_files_drop): self.Bind(wx.EVT_DROP_FILES, self.bitmaps[-1][0].image_drop_event)

        return self.bitmaps[-1][0]

    # Runs instances times function(**args). This function is designed to create
    # rows or columns
    def create_multiple(self, instances:int, function:'function', args:dict={}) -> list:
        logging.debug(f"Panel.create_multiple(self, {instances}, {function}, {args})")

        returned = []

        for num in range(instances):
            checked_args = {}
            for arg,value in args.items(): 
                if(type(value) == str):
                    checked_args[arg] = value.replace("num", str(num))
                    continue
                checked_args[arg] = value
                    
            returned.append(function(**checked_args))

        return returned


    def check_format(self, variable, do_eval:bool=True):
        if(type(variable) == str): 
            _size = self._parent._size
            if(variable.find('@') + 1 or variable.find('%') + 1): variable = self.__resize_formatting__(variable)
            if(do_eval): return eval(variable)
        return variable

    # This will format any n (2 pref) dimensional tuple and calculate any number starting with
    # @ so that it will be able to resize based on parent's size
    # Example [size=(700,1000)] (@300, @500 + 10) -> (0.42857*size[0], 0.5*size[1] + 10) [(300/700*size[0], 500/1000*size[1] + 10)] 
    def __resize_formatting__(self, formula:"str(tuple)", characters:list=['+','-','*','/','(',')']) -> "str(tuple)":
        logging.debug(f"Panel.__resize_formatting(self, {formula}, {characters})")

        start = formula.find("(")
        # end should be -= 1 but it's a wasted operation
        end = len(formula)-formula[::-1].find(")")
        
        before = formula[:start]
        after = formula[end:]
        formula = formula[start:end]

        del start, end
        
        final = ()
        # Just in case not to mess up the eval
        size = self._parent._size

        for dim_num, dimension in enumerate(formula.replace(' ','')[1:][:-1].split(',')):
            dimension_formatted = ""

            # Maybe this was better but didn't work. I think my understanding of re was insufficient
            # Idk, this is O(6*n) algorithm and the one below is only m, but usually m won't be bigger than 50
            # Also the second one has way more assignments '-.-
            #splitables = [not_empty for found in findall(characters, dimension) for not_empty in found if not_empty] + ['']

            # Just get all +, -, *, /, ( and ) in order
            splitables = []
            splitable = ""
            for num, char in enumerate(dimension):
                if(not char in characters):
                    if(splitable): 
                        # Check if there's any symbol before any number
                        if(num == len(splitable)):
                            dimension_formatted += splitable
                            splitable = ''
                            continue

                        splitables.append(splitable)
                        splitable = ''

                    continue

                splitable += char

            if(splitable): splitables.append(splitable)
            else: splitables.append('')

            del splitable

            num = 0
            for splitted in multisplit("\\"+"|\\".join(characters)+"+", dimension):
                logging.debug(f"dim: {dim_num} || splitted: {splitted}")
                if(not splitted): continue
                if(splitted[0] == '@'): splitted = f"{splitted[1:]}/{size[dim_num]}*_size[{dim_num}]"
                elif(splitted[0] == '%'): splitted = splitted[1:]+f"*_size[{dim_num}]"
                dimension_formatted += splitted + splitables[num]
                num += 1

            final = final + (dimension_formatted,)

        return before + str(final).replace('\'','') + after

    def __resize__(self):
        logging.debug("Panel.__resize__(self)")
        if(not self.resizable): return
        
        self.SetPosition(self.check_format(self.relocate))
        self.SetSize(self.check_format(self.resize))

        for panel in self.panels:
            panel.__resize__()

        # This can be done since list are immutable
        for widgets in self.widgets_list:
            for widget in widgets:
                widget[0].SetSize(self.check_format(widget[1]))
                widget[0].SetPosition(self.check_format(widget[2]))

        self.Refresh()

    def __extend_scrollbar__(self, event):
        logging.debug(f"Panel.__extend_scrollbar__(self, {event})")
        new_size = check_format(self.extend_scrollbar)

        if(type(new_size) == int): new_size = (new_size, new_size)

        event.GetParent().GetScroll(event.GetOrientation()).Range = (event.GetParent().GetScroll(event.GetOrientation()).Range +
                                                                    new_size[event.GetOrientation()])
    
    @property
    def delete(self, step:int=-1) -> None:
        logging.debug(f"Panel.delete(self)")
        logging.info("Removed one panel")
            
        if(step == 1 or step < 0):
            self._parent.panels.remove(self)
        if(step == 2 or step < 0):
            self.Destroy()

    @property
    def _size(self) -> tuple:
        return (self.Size.x, self.Size.y)


"""
    A special class in order to make ALL StaticBitmap containers look better
    that's the reason it is in front.py
"""
class Image_container(wx.StaticBitmap):
    def __init__(self, parent:Panel, location:tuple, size:tuple, style:'style1 | style2',
                        image_path:str="None.jpg", menu:bool=True, bitmap_images:list=[]):
        
        self._parent = parent
        self.bitmap_images = bitmap_images

        self.__class__.__base__.__init__(self, parent, -1, self.image_from_path(image_path, parent), 
                                self._parent.check_format(location), self._parent.check_format(size), style)

        if(image_path != "None.jpg"): 
            self.bitmap_images.append(image_path)

        self.image_num = 0

        if(menu): 
            self.menu = parent._parent.new_panel(f"{str(size)[:str(size).find(',')]}, @30)", 
                                        f"{str(location)[:str(size).find(',')]}{str(size)[str(size).find(',')+1:]}", 
                                        (255,255,255))
                                    
            # in case of adding anything i have to change the way of accessing it in self.set_image
            self.menu_sub = [
                    self.menu.add_button('<', (0,0), "(self.Size.y, self.Size.y)", lambda _: self.set_image(self.image_num-1)),
                    self.menu.add_textbox("(self.Size.x/2-self.Size.y,0)", "(self.Size.y*2,self.Size.y)",
                                            f"{self.image_num}/{len(self.bitmap_images)}", multiline=False,
                                            on_event=lambda event: self.set_image(event.String), event=wx.EVT_TEXT),
                    self.menu.add_button('>', "(self.Size.x-self.Size.y,0)", "(self.Size.y, self.Size.y)", 
                                                lambda _: self.set_image(self.image_num+1))
                ]

        else: 
            self.menu = None
            self.menu_sub = None

        self.menu.Refresh()

        self.set_image(len(self.bitmap_images))

    # Saves all images droped on event
    def image_drop_event(self, event:wx.EVT_DROP_FILES, filetypes:list=["jpg","jpeg","png"]):
        logging.debug(f"Image_container.image_drop_event(self, {event}, {filetypes})")
        logging.info(f"The user has dropped {event.GetNumberOfFiles()} file"
                        f"{'s' if event.GetNumberOfFiles() != 1 else ''}")
        for image in event.GetFiles():
            if(image[len(image)-image[::-1].find("."):].lower() in filetypes):
                self.bitmap_images.append(self.image_from_path(image, self._parent))

        if(len(self.bitmap_images)):
            self.set_image(len(self.bitmap_images))

            self.CenterOnParent()

            self.Refresh()

    # Returns a bitmap from a image_path
    @staticmethod
    def image_from_path(image_path:str, panel:wx.Window, keep_ratio:bool=True, scale_to:"fit/fill"='fit') -> wx.Bitmap:
        logging.debug(f"Image_container.image_from_path({image_path}, {panel}, {scale_to})")

        if(keep_ratio or scale_to == "fit"):
            img_size = imread(image_path).shape[:2][::-1]

            logging.debug(f"Non-formatted image has size {img_size}")

            if(scale_to == "fill"): 
                if(img_size[0] < img_size[1]):
                    img_size = (panel.Size.x, img_size[1]*panel.Size.x/img_size[0])
                elif(img_size[0] > img_size[1]):
                    img_size = (img_size[0]*panel.Size.y/img_size[1], panel.Size.y)
                else: img_size = (min(panel._size),)*2
            else: # Done so that i don't have to raise ValueError of scale_to
                if(img_size[0] < img_size[1]):
                    img_size = (img_size[0]*panel.Size.y/img_size[1], panel.Size.y)
                elif(img_size[0] > img_size[1]):
                    img_size = (panel.Size.x, img_size[1]*panel.Size.x/img_size[0])
                else: img_size = (min(panel._size),)*2

        else:
            img_size = panel.Size
        
        logging.debug(f"Formatted image has size {img_size}")

        return wx.Image(image_path, wx.BITMAP_TYPE_ANY).Scale(img_size[0], img_size[1],
                                        wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()

    def set_image(self, image_num:int):
        logging.debug(f"Image_container.set_image(self, {image_num})")
        
        if(str(image_num).find('/')+1): image_num = image_num[:image_num.find('/')]

        try:
            if(int(image_num) < 1 or int(image_num) > len(self.bitmap_images) or int(image_num) == self.image_num): return
        except: return

        self.image_num = int(image_num)

        # This will trigger itself
        if(not self.menu is None): self.menu_sub[1].SetValue(f"{image_num}/{len(self.bitmap_images)}")

        self.SetBitmap(self.bitmap_images[self.image_num-1])
        self.CenterOnParent()

        self.Refresh()


    def SetSize(self, size:tuple) -> None:
        logging.debug(f"Image_container.SetSize(self, {size})")
        self.__class__.__base__.SetSize(self, size)
        self.CenterOnParent()
    
    def SetPosition(self, location:tuple) -> None:
        logging.debug(f"Image_container.SetPosition(self, {location})")
        self.__class__.__base__.SetPosition(self, location)
        # self.CenterOnParent here looks unnecessary

# Testing
if __name__ == "__main__":
    __main()