import importlib
import os
import win32gui
import ctypes
import time
import dearpygui.dearpygui as dpg
import ctypes
from ctypes import c_int
import oxyapi
from fonts.IconsFontAwesome6 import IconsFontAwesome6 as icons
from utils import logsearch, checker_lib, node_manager
import webbrowser

dwm = ctypes.windll.dwmapi

width = 900
height = 600
    
title_bar_drag = False
def exit():
    dpg.destroy_context()
    
dpg.create_context()

p1 = [0,0]
p2 = [10,0]
p3 = [10,10]
p4 = [0,10]
p5 = [0,0]

class MARGINS(ctypes.Structure):
  _fields_ = [("cxLeftWidth", c_int),
              ("cxRightWidth", c_int),
              ("cyTopHeight", c_int),
              ("cyBottomHeight", c_int)
             ]


viewport = dpg.create_viewport(title="Oxygen Checker",width=width,height=height,decorated=False,resizable=False,clear_color=[0.0,0.0,0.0,0.0])

print("Loading api and plugins...")
_t = time.time()
oxyapi.__oxy__()

class AccountNode(oxyapi.OxyNode):
    def __init__(self):
        super().__init__()
        self.name = "Account"
        self.description = "Base node"
        self.attrs = [
            oxyapi.OxyNodeAttr("Account", dpg.mvNode_Attr_Output),
            oxyapi.OxyNodeAttr("Is valid", dpg.mvNode_Attr_Output),
            oxyapi.OxyNodeAttr("Is invalid", dpg.mvNode_Attr_Output),
        ]

    @staticmethod
    def call() -> tuple:
        return (oxyapi._check_acc, oxyapi._check_acc_isValid, not oxyapi._check_acc_isValid)

oxyapi.oxy_register_node(AccountNode(), "Account")

for file in os.listdir("./plugins"):
    if not ".py" in file: continue
    # print("Loading", file)
    try:
        oxyapi.__oxy_import__(f"plugins/{file}")
    except Exception as ex:
        print(f"Failed to import plugins/{file} | {ex}")

print(f"Finished at {round(time.time()-_t, 4)} seconds!")

oxyapi.__oxy_before_load__()
dpg.setup_dearpygui()
    
with dpg.font_registry():
    default_font = dpg.add_font("fonts/main.ttf", 20)
    small_font = dpg.add_font("fonts/main.ttf", 15)
    big_font = dpg.add_font("fonts/main.ttf", 40)
    icon_font = dpg.add_font("fonts/icons.ttf", 20)

    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=default_font)
    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=small_font)
    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic, parent=big_font)

    dpg.add_font_range(icons.ICON_MIN, icons.ICON_MAX, parent=icon_font)

    oxyapi.default_font = default_font
    oxyapi.big_font = big_font
    oxyapi.small_font = small_font


with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 7, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 10)

    # with dpg.theme_component(dpg.mvInputInt):
    #     dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (140, 255, 23), category=dpg.mvThemeCat_Core)
    #     dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

current_tab = 1

def update_global():
    # current_time = f"tab 1 {time.time()}"
    # dpg.set_value("time_text", current_time)
    # print(oxyapi._node_manager.connections)
    ...

def cange_tab(tab_number):
    global current_tab
    current_tab = tab_number
    dpg.configure_item(f"tab_{current_tab}", show=True)
    for i in range(1, 4):
        if i != current_tab:
            dpg.configure_item(f"tab_{i}", show=False)

def node_link_handler(sender, app_data):
    out_attr, in_attr = app_data
    out_node_id = dpg.get_item_parent(out_attr)
    in_node_id = dpg.get_item_parent(in_attr)

    # Search for the node instance in EDITOR_NODES
    out_node = next((n for n in oxyapi.editor_nodes if out_node_id in n.node_ids), None)
    in_node = next((n for n in oxyapi.editor_nodes if in_node_id in n.node_ids), None)

    if not out_node or not in_node:
        print("Error: Failed to find linked nodes!")
        return

    link_id = dpg.add_node_link(out_attr, in_attr, parent=sender)
    conn = node_manager.Connection(link_id, in_attr, out_attr, in_node, out_node)
    oxyapi._node_manager.add_connection(conn)

def node_unlink_handler(sender, app_data):
    print("UNLINK:", app_data)
    dpg.delete_item(app_data)
    oxyapi._node_manager.delete_connection(app_data)

def add_node(sender, data, user_data):
    new_node = user_data.__class__()
    new_node.node_add("nodeeditor")
    oxyapi.editor_nodes.append(new_node) 

checking = False

def start_check():
    global checking

    print("Checking",oxyapi.selected_project)
    # return

    dpg.configure_item("start_check_btn", label="Checking...")

    if checking == True:
        print("Already checking...")
        return
    
    checking = True
    if oxyapi.logs_folder == "":
        print("Select logs folder")
        return
    print("Starting check...")

    logs_checked = 0
    errors = 0
    for log in oxyapi.loaded_cookies:
        for project in oxyapi.selected_project:
            checker = checker_lib.FastChecker(f"Projects/{project}",max_workers=30)

            ch_res = checker.check_single(log)
            if ch_res.status == 'error':
                errors += 1
                continue
            if ch_res.status == 'invalid':
                # print(proj, "Invalid!", ch_res)
                oxyapi.event_handler.call_event("invalid_account", ch_res.account)
                continue
            oxyapi.oxy_append_line_to_results(f"{project} | VALID: "+ " ".join([f"{key}: {val} | " for key, val in ch_res.account.fields.items()]) +"\n")
            oxyapi.event_handler.call_event("valid_account", ch_res.account)
        logs_checked+=1
        # print(f"{logs_checked}/{len(oxyapi.loaded_cookies)}")
        dpg.configure_item("start_check_btn", label=f"{logs_checked}/{len(oxyapi.loaded_cookies)}")

    dpg.configure_item("start_check_btn", label=f"Start")
    checking = False
    

def select_logs_folder():
    def fs_cb(_, path: dict):
        directory = path.get("file_path_name")
        print("Selected", directory)
        oxyapi.oxy_append_line_to_results("Loading cookies...\n")
        plog = logsearch.parse_logs(directory)
        
        oxyapi.oxy_append_line_to_results(plog[0])
        oxyapi.loaded_cookies = plog[1]
        oxyapi.logs_folder = directory
    print("Selecting logs folder...")
    with dpg.file_dialog(label="Select path with cookies", callback=fs_cb, modal=True, directory_selector=True, user_data=True):
        pass
    # oxyapi.logs_folder = "123"

def on_proj_checkbox(sender, data, name):
    if data: oxyapi.selected_project.append(name)
    if not data: oxyapi.selected_project.remove(name)

def get_all_projects():
    res = []
    for file in os.listdir("Projects"):
        if file.endswith(".json"): res.append(file)
    return res

def chunks(lst: list[str], n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def on_compile_nodes():
    print(oxyapi._node_manager.compile())

with dpg.window(label="Frameless Window",width=width,height=height,no_collapse=True,no_move=True,no_resize=True,on_close=exit, no_title_bar=True) as win:
    # dpg.add_text("Smaller text")
    with dpg.group(horizontal=True):
        with dpg.group(horizontal=False, width=200):
            logo = dpg.add_text("Oxygen")
            oxyapi.__oxy_ui_init__()
            dpg.bind_item_font(logo, big_font)
            dpg.add_button(label="Checker", height=50, callback=lambda: cange_tab(1))
            dpg.add_button(label="Node editor", height=50, callback=lambda: cange_tab(2))
            dpg.add_button(label="Settings", height=50, callback=lambda: cange_tab(3))
            
        with dpg.group(horizontal=False):
            with dpg.group(tag="tab_1", show=current_tab==1):
                with dpg.group():
                    with dpg.group(horizontal=True, width=159, height=40):
                        dpg.add_button(label="Select path", callback=select_logs_folder)
                        dpg.add_button(label="Start", callback=start_check, tag="start_check_btn")
                        dpg.add_button(label="Results", callback=lambda: os.startfile("Results"))
                        dpg.add_button(label="Proxy")
                        with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, modal=True):
                            dpg.add_text("In next version :3")
                    # dpg.add_spacer(height=height-310)
                with dpg.group():
                    for proj_chunk in chunks(get_all_projects(), 4):
                        with dpg.group(horizontal=True):
                            for proj in proj_chunk:
                                dpg.add_checkbox(label=proj.rstrip(".json"), user_data=proj, callback=on_proj_checkbox)
                with dpg.group(pos=[width-670, height-220]):
                    dpg.add_input_text(default_value="Loaded Oxygen Checker\n",multiline=True, readonly=True, width=width-240, height=200, tag="check_result")
            with dpg.group(tag="tab_2", show=current_tab==2):
                with dpg.group(horizontal=True):
                    add_node_button = dpg.add_button(label="Add node")
                    dpg.add_button(label="Convert nodes to plugin", callback=on_compile_nodes)
                    dpg.add_input_text(label="Service name", width=160)
                with dpg.popup(add_node_button, modal=True, mousebutton=dpg.mvMouseButton_Left, tag="add_node_modal", no_move=True, min_size=[width-300, height-200]):
                    dpg.add_text("Select node")
                    for category, nodes in oxyapi.node_storage.items():
                        with dpg.tree_node(label=category):
                            for node in nodes:
                                dpg.add_button(label=node.name, callback=add_node, user_data=node)
                with dpg.node_editor(tag="nodeeditor",callback=node_link_handler, 
                             delink_callback=node_unlink_handler, minimap=True, minimap_location=dpg.mvNodeMiniMap_Location_BottomRight) as ne:
                    # with dpg.node(label="Account", pos=[10, 10]) as main_node:
                    #     with dpg.popup(main_node):
                    #         dpg.add_text("Add node")
                    #     with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                    #         dpg.add_text("On Valid")

                    #     with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                    #         dpg.add_text("On Invalid")
                    oxyapi.node_storage["Account"][0].node_add(ne)

            with dpg.group(tag="tab_3", show=current_tab==3):
                dpg.add_text("Creators: белочка & ночь")
                dpg.add_text(f"Loaded {len(oxyapi.plugin_storage)} plugins")
                dpg.add_button(label="Plugin list", height=30)
                with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, modal=True, tag="plugin_modal", no_move=True, min_size=[width-300, height-300]):
                    for plugin in oxyapi.plugin_storage:
                        with dpg.group(horizontal=True):
                            if plugin.icon:
                                dpg.add_image(plugin.id+"_ico", width=72, height=72)
                            with dpg.group(horizontal=False):
                                with dpg.group(horizontal=True):
                                    h = dpg.add_text(f"{plugin.name}", color=(-255,0,0,255) if not plugin.warn else (255,255,0,255))
                                    if plugin.tooltip != None:
                                        with dpg.tooltip(h):
                                            dpg.add_text(plugin.tooltip)
                                m = dpg.add_text(f"{plugin.version} by {plugin.author}")
                                dpg.bind_item_font(m, small_font)
                                dpg.bind_item_font(h, big_font)
                            with dpg.group(horizontal=False, width=100):
                                dpg.add_button(label="Open", callback= lambda: os.startfile(os.path.abspath(".")+"\\"+'/'.join(plugin.path.split("/")[:-1])))
                                dpg.add_button(label="Browse", enabled=False)
                        dpg.add_separator()
                    dpg.add_text(f"Plugin API: {oxyapi.__version_major__}.{oxyapi.__version_minor__} | Load problems: {oxyapi._plugin_init_problems}")
                    dpg.add_button(label="Documentation", callback=lambda: webbrowser.open_new_tab("http://oxy.strnq.xyz/"))
                for plugin in oxyapi.plugin_storage:
                    if plugin.setup_ui == None: continue
                    dpg.add_separator(label=plugin.name)
                    try:
                        plugin.setup_ui()
                    except Exception as ex:
                        import traceback
                        dpg.add_text(f"Failed to setup ui! {ex}", color=(255,0,0,255))
                        traceback.print_exception(ex)
    


dpg.bind_theme(global_theme)

_hold_fix = False

def cal_dow(sender,data):
    global title_bar_drag, _hold_fix
    if dpg.is_mouse_button_down(0):
        x = data[0]
        y = data[1]
        if _hold_fix:
            title_bar_drag = True
        else:
            title_bar_drag = False
            _hold_fix = False
    
def cal(sender,data):
    global title_bar_drag
    if title_bar_drag:
        pos = dpg.get_viewport_pos()
        x = data[1]
        y = data[2]
        final_x = pos[0]+x
        final_y = pos[1]+y
        dpg.configure_viewport(viewport,x_pos=final_x,y_pos=final_y)

def drag_fix():
    global _hold_fix
    # _hold_fix = True
    data = dpg.get_mouse_pos()
    x = data[0]
    y = data[1]

    if y <= 20:
        # print()
        _hold_fix = True
    else:
        _hold_fix = False
    
with dpg.handler_registry():
    dpg.add_mouse_drag_handler(0,callback=cal)
    dpg.add_mouse_move_handler(callback=cal_dow)
    dpg.add_mouse_click_handler(0, callback=drag_fix)
    
dpg.bind_font(default_font)
# dpg.bind_font(icon_font)
# dpg.add_font_range(icon_font, 0xf000, 0xf2ff)

dpg.show_viewport()

# dpg.configure_viewport(viewport, alpha_value=0)
hwnd = win32gui.FindWindow(None, "Oxygen Checker")
margins = MARGINS(-1, -1,-1, -1)
dwm.DwmExtendFrameIntoClientArea(hwnd, margins)
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()  
    update_global()