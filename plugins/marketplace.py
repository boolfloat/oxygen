"""Oxygen Checker built-in plugin | Marketplace!"""
import webbrowser
import requests
import oxyapi
import dearpygui.dearpygui as dpg
import configparser
import json
import os

__oxy_name__ = "Marketplace"
__description__ = "Get projects and plugins for Oxygen!"
__author__ = "ночь"
__version__ = "beta"
__api__ = 0 # major api version


# def view_plugins():
    

# def view_projects():
#     ...

def dl_plugin(s, d, user_data):
    r = requests.get(f"http://oxy.strnq.xyz/market/get_plugins/{user_data}")

    with open(f"plugins/{user_data}.py", "w") as f:
        f.write(r.text)

def setup_ui():
    dpg.add_button(label="View plugins")
    with dpg.popup(dpg.last_item(), dpg.mvMouseButton_Left, True):
        r = requests.get("http://oxy.strnq.xyz/market/get_plugins")
        resp = r.json()

        api_ver = resp["oxy"]
        if api_ver != __api__: print("WARNING: Bad api version")

        plugins = resp["plugins"]

        for plugin in plugins:
            with dpg.group(horizontal=True):
                with dpg.group(horizontal=False):
                    with dpg.group(horizontal=True):
                        h = dpg.add_text(f"{plugin['name']}", color=(-255,0,0,255))
                        with dpg.tooltip(h):
                            dpg.add_text(plugin["description"])
                    m = dpg.add_text(f"by {plugin['author']}")
                    dpg.bind_item_font(m, oxyapi.small_font)
                    dpg.bind_item_font(h, oxyapi.big_font)
                with dpg.group(horizontal=False, width=100):
                    dpg.add_button(label="Download", user_data=plugin["id"], callback=dl_plugin)
                    dpg.add_button(label="Open link", callback=lambda: webbrowser.open_new_tab(f"http://oxy.strnq.xyz/market/get_plugins/{plugin['id']}"))

    dpg.add_button(label="View projects")
    with dpg.popup(dpg.last_item(), dpg.mvMouseButton_Left, True):
        dpg.add_text("TODO")
    dpg.add_button(label="Upload project/plugin", callback=lambda: webbrowser.open_new_tab("https://lolz.live/threads/8236948/"))
    

if __name__ == "__main__":
    raise ModuleNotFoundError()