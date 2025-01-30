import importlib
import os
import typing
from utils import eventit, logsearch
import dearpygui.dearpygui as dpg

__version_major__ = 0
__version_minor__ = 1

init = False
event_handler = eventit.EventIt()

class AccountResult:
    def __init__(self, cookies: list[logsearch.Cookie], fields: dict, domain: str):
        self.cookies = cookies
        self.fields = fields
        self.domain = domain

class OxyNodeAttr:
    def __init__(self, name, type=dpg.mvNode_Attr_Input):
        self.name = name
        self.type = type

class OxyNode:
    """Base class for nodes"""
    def __init__(self):
        self.name = "BaseNode"
        self.description = "Description"
        self.attrs = [
            OxyNodeAttr("Input 1"),
            OxyNodeAttr("Input 2"),
            OxyNodeAttr("Output 1", dpg.mvNode_Attr_Output),
            OxyNodeAttr("Output 2", dpg.mvNode_Attr_Output),
        ]

    def node_add(self, parent):
        print(f"Adding {self.name} to node editor")
        with dpg.node(label=self.name, pos=[300, 10], parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                # dpg.add_input_text(label="Variable", width=140)
                dpg.add_text(self.description)

            for attr in self.attrs:
                with dpg.node_attribute(attribute_type=attr.type):
                    dpg.add_text(attr.name)

    @staticmethod
    def call(*args):
        raise NotImplementedError

class OxyPlugin:
    def __init__(self, path, id, name, desc, author, version, api_version, warn=False):
        self.path = path
        self.id = id
        self.name = name
        self.desc = desc
        self.author = author
        self.version = version
        self.api_version = api_version

        self.warn = warn

        self.tooltip = None
        
        self.setup_ui: typing.Callable[[], None] = None

        self.icon = False

plugin_storage: list[OxyPlugin] = []
node_storage: typing.Dict[str, list[OxyNode]] = {}

_plugin_init_problems = 0
_before_load_reached = False

logs_folder = ""
loaded_cookies: list[list[logsearch.Cookie]] = []
selected_project: list[str] = []

texture_registry = None

default_font = None
small_font = None
big_font = None

def __oxy_import__(path: str):
    global _plugin_init_problems
    if _before_load_reached:
        print(f"WARN: Trying to load {path} after before_load event. This is not recomended and may lead to errors")
        _plugin_init_problems += 1
    m = importlib.import_module(path.rstrip('.py').replace("/", "."))
    plugin = OxyPlugin(path, path.rstrip('.py').split("/")[-1], m.__oxy_name__, m.__description__, m.__author__, m.__version__, m.__api__, _before_load_reached)
    plugin.tooltip = plugin.desc
    if plugin.api_version != __version_major__:
        print(f"WARN: Importing incompatible plugin {plugin.name} (Plugin api: {plugin.api_version} | Current api: {__version_major__}.{__version_minor__})! It can misbehave or not work at all")
        _plugin_init_problems += 1
        plugin.warn = True
        plugin.tooltip = f"Incompatible api version (Plugin api: {plugin.api_version} | Current api: {__version_major__}.{__version_minor__})!"

    has_ui_setup = hasattr(plugin, "setup_ui")
    if has_ui_setup:
        plugin.setup_ui = m.setup_ui
    print(f"Loaded plugin: {plugin.name} {m.__version__} by {plugin.author}")
    plugin_storage.append(plugin)

def __oxy_ui_init__():
    """NOT FOR PLUGIN USE"""
    event_handler.call_event("ui_init")

def __oxy_before_load__():
    """NOT FOR PLUGIN USE"""
    global _before_load_reached
    _before_load_reached = True
    with texture_registry:
        for plugin in plugin_storage:
            if os.path.exists(plugin.path.rstrip(".py")+".png"):
                print("Adding plugin icon:",plugin.path.rstrip(".py")+".png", "Tag:", plugin.id+"_ico")
                width, height, channels, data = dpg.load_image(plugin.path.rstrip(".py")+".png")
                dpg.add_static_texture(width=width, height=height, default_value=data, tag=plugin.id+"_ico")
                plugin.icon = True
    event_handler.call_event("before_load")

def oxy_append_line_to_results(line: str):
    dpg.configure_item("check_result", default_value=dpg.get_value("check_result")+line)

def oxy_register_node(node: OxyNode, category: str):
    if node_storage.get(category) == None: node_storage[category] = []
    node_storage.get(category).append(node)
    print(f"Registered node {node.name} ({category})")

def __oxy__():
    """NOT FOR PLUGIN USE"""
    global init, texture_registry
    if init: return
    texture_registry = dpg.texture_registry()
    event_handler.register_event("before_load")
    event_handler.register_event("ui_init")
    event_handler.register_event("valid_account")
    event_handler.register_event("invalid_account")
    event_handler.register_event("exit")
    init = True