"""Oxygen Checker built-in plugin | Open lolz threads on first program run"""
import oxyapi
import webbrowser
import dearpygui.dearpygui as dpg
import os

__oxy_name__ = "Firstrun Example"
__description__ = "Test plugin"
__author__ = "ночь"
__version__ = "v.1"
__api__ = 0 # major api version

@oxyapi.event_handler.on_event
def before_load():
    if os.path.exists(".frun"): return
    with open(".frun", "w") as f:
        f.write("1")
    webbrowser.open_new_tab("https://lolz.live/threads/7766339/")
    webbrowser.open_new_tab("https://lolz.live/threads/7809122/")

# def setup_ui():
#     dpg.add_button(label="Test")

if __name__ == "__main__":
    raise ModuleNotFoundError()