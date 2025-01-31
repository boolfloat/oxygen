"""Oxygen Checker built-in plugin | Basic nodes and etc. You can use this plugin as example for your plugins :3"""
import typing
import oxyapi
import dearpygui.dearpygui as dpg
import configparser
import json
import os, sys
from utils import logsearch

__oxy_name__ = "Core"
__description__ = "Core plugin. Please don't edit this file manually"
__author__ = "ночь"
__api__ = 0 # major api version
__version__ = f"v.{__api__}"

if __name__ == "__main__":
    raise ModuleNotFoundError()


def ex_handler(_type, value, tb):
    import traceback
    tbtext = ''.join(traceback.format_exception(_type, value, tb))

    print(tbtext)
    if _type == KeyboardInterrupt: return

    print("Crashing! Exc", _type, value, tb)
    with open(".core-crashlog", "w") as cl:
        cl.write(tbtext)

# sys.excepthook = ex_handler

class PrintNode(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Print"
        self.description = "Print input to console"
        self.attrs = [
            oxyapi.OxyNodeAttr("Input")
        ]

    def call(input: typing.Any):
        print(input)

class AppendToFile(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Append to file"
        self.description = "Append to results.txt"
        self.attrs = [
            oxyapi.OxyNodeAttr("Account")
        ]
    
    def node_add(self, parent):
        print(f"Adding {self.name} to node editor")
        with dpg.node(label=self.name, pos=[300, 10], parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(self.description)
                dpg.add_input_text(label="File name", width=140)

            for attr in self.attrs:
                with dpg.node_attribute(attribute_type=attr.type):
                    dpg.add_text(attr.name)
    
    @staticmethod
    def call(input: oxyapi.AccountResult):
        print(input)

class GetField(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Get field"
        self.description = "Get field in account result"
        self.attrs = [
            oxyapi.OxyNodeAttr("Account"),
            oxyapi.OxyNodeAttr("Value", dpg.mvNode_Attr_Output)
        ]
    
    def node_add(self, parent):
        print(f"Adding {self.name} to node editor")
        with dpg.node(label=self.name, pos=[300, 10], parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(self.description)
                dpg.add_input_text(label="Field name", width=140)

            for attr in self.attrs:
                with dpg.node_attribute(attribute_type=attr.type):
                    dpg.add_text(attr.name)
    
    @staticmethod
    def call(input: oxyapi.AccountResult):
        print(input)

class Number(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Number"
        self.description = "Just return number"
        self.attrs = [
            oxyapi.OxyNodeAttr("Value", dpg.mvNode_Attr_Output)
        ]

    def node_add(self, parent):
        print(f"Adding {self.name} to node editor")
        with dpg.node(label=self.name, pos=[300, 10], parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(self.description)
                dpg.add_input_int(label="Number", width=140)

            for attr in self.attrs:
                with dpg.node_attribute(attribute_type=attr.type):
                    dpg.add_text(attr.name)
    
    @staticmethod
    def call(input: None):
        print(input)

class String(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "String"
        self.description = "Just return string"
        self.attrs = [
            oxyapi.OxyNodeAttr("Value", dpg.mvNode_Attr_Output)
        ]

    def node_add(self, parent):
        print(f"Adding {self.name} to node editor")
        with dpg.node(label=self.name, pos=[300, 10], parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(self.description)
                dpg.add_input_text(label="String", width=140)

            for attr in self.attrs:
                with dpg.node_attribute(attribute_type=attr.type):
                    dpg.add_text(attr.name)
    
    @staticmethod
    def call(input: None):
        print(input)

class TrueFilter(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "True Filter"
        self.description = ""#"Return input if value is True"
        self.attrs = [
            oxyapi.OxyNodeAttr("Input", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Value", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Return", dpg.mvNode_Attr_Output)
        ]
    
    @staticmethod
    def call(input: None):
        print(input)

class LargerSmaller(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Larger/Smaller"
        self.description = "V1>V2?"
        self.attrs = [
            oxyapi.OxyNodeAttr("V1", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("V2", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Larger", dpg.mvNode_Attr_Output),
            oxyapi.OxyNodeAttr("Smaller", dpg.mvNode_Attr_Output)
        ]
    
    @staticmethod
    def call(input: None):
        print(input)

class GETRequest(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "GET Request"
        self.description = "Do GET"
        self.attrs = [
            oxyapi.OxyNodeAttr("When", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("URL", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Response", dpg.mvNode_Attr_Output),
        ]
    
    @staticmethod
    def call(input: None):
        print(input)

class POSTRequest(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "POST Request"
        self.description = "Do POST"
        self.attrs = [
            oxyapi.OxyNodeAttr("When", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("URL", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Body", dpg.mvNode_Attr_Input),
            oxyapi.OxyNodeAttr("Response", dpg.mvNode_Attr_Output),
        ]
    
    @staticmethod
    def call(when: typing.Any):
        # print(input)
        ...

@oxyapi.event_handler.on_event
def ui_init():
    if os.path.exists(".core-crashlog"):
        with dpg.popup(dpg.last_item(), modal=True, tag="core_modal_crash", no_move=True):
            noch_text = dpg.add_text("It looks like your program crashed!")
            dpg.bind_item_font(noch_text, oxyapi.big_font)
            with open(".core-crashlog") as f:
                dpg.add_input_text(label="Traceback", multiline=True, default_value=f.read(), readonly=True) 
        
        dpg.configure_item("core_modal_crash", show=True)
    
    if oxyapi.__version_major__ != __api__:
        with dpg.popup(dpg.last_item(), modal=True, tag="core_modal_badapi", no_move=True):
            noch_text = dpg.add_text("Something strange happened!")
            dpg.bind_item_font(noch_text, oxyapi.big_font)
            dpg.add_text("It looks like this Core module version designed for other Oxygen Checker API version! :P")
            dpg.add_text(f"Oxy API: {oxyapi.__version_major__} | Core API: {__api__}", color=(255,0,0,255))
        
        dpg.configure_item("core_modal_badapi", show=True)

@oxyapi.event_handler.on_event
def valid_account(account: oxyapi.AccountResult):
    fh_str = ""
    for field, val in account.fields.items():
        fh_str += f"[{field} {val}]"

    filename = f"Results/{fh_str} Spotify {str(id(account.cookies))}.txt"
    if os.path.exists(filename):
        print("[CORE] Dublicate result...")
        return
    with open(filename, "a+", encoding="utf-8") as f:
        f.write("""# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This file was generated by Oxygen Checker (Core)
""")
        for cookie in account.cookies:
            if account.domain in cookie.url:
                f.write(cookie.netscape()+"\n")

@oxyapi.event_handler.on_event
def before_load():
    """This event triggered before ui load, so there we can create our nodes"""
    oxyapi.oxy_register_node(GetField(), "Account")
    oxyapi.oxy_register_node(Number(), "Constants")
    oxyapi.oxy_register_node(String(), "Constants")
    oxyapi.oxy_register_node(LargerSmaller(), "Logical")
    oxyapi.oxy_register_node(TrueFilter(), "Filters")
    oxyapi.oxy_register_node(AppendToFile(), "File operations")
    oxyapi.oxy_register_node(GETRequest(), "Network")
    oxyapi.oxy_register_node(POSTRequest(), "Network")
    oxyapi.oxy_register_node(PrintNode(), "Misc")

def on_telemetry():
    # dpg.push_container_stack("123")
    raise NotImplementedError()

def setup_ui():
    dpg.add_checkbox(label="Telemetry", callback=on_telemetry)
    dpg.add_button(label="Show full credits")
    with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, modal=True, tag="core_modal", no_move=True):
        noch_text = dpg.add_text("ночь")
        dpg.bind_item_font(noch_text, oxyapi.big_font)
        dpg.add_text("Plugin system", bullet=True)
        dpg.add_text("Node system", bullet=True)
        dpg.add_text("UI", bullet=True)
        dpg.add_text("Base checker", bullet=True)
        dpg.add_text("Other...", bullet=True)
        belochka_text = dpg.add_text("белочка")
        dpg.bind_item_font(belochka_text, oxyapi.big_font)
        dpg.add_text("Project editor", bullet=True)
        dpg.add_text("Logo", bullet=True)
        dpg.add_text("Built-in plugins", bullet=True)
        dpg.add_text("Base checker", bullet=True)
        dpg.add_text("Other...", bullet=True)
        dpg.add_separator()
        dpg.add_text("Made with love for lolz contest <3")

