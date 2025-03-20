"""Project Creator plugin for Oxygen Checker"""
import dearpygui.dearpygui as dpg
import json
import http.cookiejar
import requests
import os
from urllib.parse import urlparse
import configparser
import oxyapi

__oxy_name__ = "Project Creator"
__description__ = "Cookie project creator with parser functionality"
__author__ = "белочка"
__version__ = "v.1"
__api__ = 0

class CookieProjectCreator:
    def __init__(self):
        self.parser_values = []  # Список для хранения активных значений
        self.next_value_id = 2  # Start with 2 since status is 1
        self.deleted_value_ids = set()  # Track deleted value IDs
        self.cookies = None
        self.name_value_entries = {}
        self.headers_widgets = {}
        self.setup_main_window()
        self.setup_headers_section()
        self.setup_name_value_entries()

    def setup_main_window(self):
        with dpg.window(label="Project Creator", 
                    autosize=True, 
                    tag="ProjectCreator", 
                    show=False,
                    modal=True,  # Добавляем это
                    no_close=False,  # И это
                    pos=[50, 50]):  # И позицию
            # Top controls
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load Cookies", callback=self.load_cookies_dialog)
                dpg.add_input_text(label="Domain", tag="domain", width=200)
                dpg.add_button(label="Load Project", callback=self.load_project_dialog)
            
            dpg.add_text("Ready", tag="status")
            
            # Request settings
            with dpg.group(horizontal=True):
                dpg.add_combo(["GET", "POST"], default_value="GET", tag="method", width=100)
                dpg.add_input_text(label="URL", tag="url", width=400)

            # Body editor
            dpg.add_text("POST Body (name=value per line):")
            dpg.add_input_text(tag="body", multiline=True, height=60, width=600)

            # Headers section
            with dpg.collapsing_header(label="Request Headers", tag="headers_section"):
                pass

            # Parser settings
            with dpg.collapsing_header(label="Parser Settings", tag="parser_settings"):
                dpg.add_checkbox(label="Use Parser", tag="use_parser")
                with dpg.group(tag="parser_values_group"):
                    # Status validation
                    dpg.add_button(label="Add Value", callback=self.add_parser_value)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(label="Value_1", default_value="status", readonly=True, width=100)
                        dpg.add_input_text(label="Valid String", tag="valid_string", width=200, 
                                         hint="If this string is found in response, cookies are valid")
                    
                    # Add value button

            # Raw Response display
            dpg.add_text("Raw Response:")
            dpg.add_input_text(tag="response", multiline=True, height=200, width=600)

            # Parsed Response display
            dpg.add_text("Parsed Response:")
            dpg.add_input_text(tag="parsed_response", multiline=True, height=100, width=600)

            # Response validate
            # dpg.add_input_text(label="Response Validate", tag="response_validate", width=300)

            # Parser URL
            # with dpg.group(parent="parser_settings"):
            #     dpg.add_input_text(label="Parser URL", tag="pars_url", width=300)

            # Status bar
            # dpg.add_text(tag="status", default_value="Ready")

            # Bottom controls
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="Project Name", tag="project_name", width=200)
                dpg.add_button(label="Save Project", callback=self.save_project_dialog)
                dpg.add_button(label="Send Request", callback=self.send_request)

    def add_parser_value(self):
        # Находим наименьший доступный ID
        new_id = 2  # Начинаем с 2, так как 1 зарезервирован для status
        existing_ids = {parser_value.id for parser_value in self.parser_values}
        
        while new_id in existing_ids or new_id in self.deleted_value_ids:
            new_id += 1
        
        # Проверяем существование и удаляем старый тег если он есть
        tag = f"parser_value_{new_id}"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
                
        self.parser_values.append(ParserValue("parser_values_group", new_id))
        if new_id >= self.next_value_id:
            self.next_value_id = new_id + 1

    def setup_headers_section(self):
        headers_list = [
            ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", True),
            ("Accept", "*/*", True),
            ("Content-Type", "application/x-www-form-urlencoded", True),
            ("Referer", "", False),
            ("X-Requested-With", "XMLHttpRequest", False)
        ]
        
        with dpg.group(parent="headers_section"):
            for header, default, enabled in headers_list:
                with dpg.group(horizontal=True):
                    cb = dpg.add_checkbox(default_value=enabled, tag=f"header_cb_{header}")
                    inp = dpg.add_input_text(label=header, default_value=default, width=300)
                    self.headers_widgets[header] = {"cb": cb, "input": inp}

    def setup_name_value_entries(self):
        with dpg.group(parent="headers_section"):
            for i in range(1, 6):
                with dpg.group(horizontal=True):
                    cb = dpg.add_checkbox(tag=f"nv_cb_{i}")
                    dpg.add_text(f"NAME{i}=VALUE{i}")
                    inp = dpg.add_input_text(tag=f"nv_input_{i}", width=200)
                    self.name_value_entries[i] = {"cb": cb, "input": inp}

    def load_cookies_dialog(self):
        def callback(sender, app_data):
            try:
                self.cookies = http.cookiejar.MozillaCookieJar(app_data['file_path_name'])
                self.cookies.load()
                dpg.set_value("status", f"Loaded cookies: {os.path.basename(app_data['file_path_name'])}")
            except Exception as e:
                dpg.set_value("status", f"Cookie error: {str(e)}")
                print(f"Cookie error: {str(e)}")  # Add debug print

        with dpg.file_dialog(
            label="Select Cookies File",
            callback=callback,
            modal=True,
            directory_selector=False
        ):
            dpg.add_file_extension(".txt", color=(0, 255, 0, 255))

    def load_project_dialog(self):
        def callback(sender, app_data):
            try:
                with open(app_data['file_path_name'], 'r') as f:
                    if app_data['file_path_name'].endswith('.proj'):
                        config = configparser.ConfigParser()
                        config.read_string(f.read())
                        project_data = self.convert_proj_to_json(config)
                    else:
                        project_data = json.load(f)
                
                self.load_project_data(project_data)
                dpg.set_value("status", f"Project loaded: {os.path.basename(app_data['file_path_name'])}")
            except Exception as e:
                dpg.set_value("status", f"Load error: {str(e)}")

        with dpg.file_dialog(
            label="Select Project File",
            callback=callback,
            modal=True,
            directory_selector=False
        ):
            dpg.add_file_extension(".json", color=(0, 255, 0, 255))
            dpg.add_file_extension(".proj", color=(255, 0, 0, 255))

    def save_project_dialog(self):
        def callback(sender, app_data):
            try:
                project_data = self.prepare_project_data()
                with open(app_data['file_path_name'], 'w') as f:
                    json.dump(project_data, f, indent=4)
                dpg.set_value("status", f"Project saved: {os.path.basename(app_data['file_path_name'])}")
            except Exception as e:
                dpg.set_value("status", f"Save error: {str(e)}")

        with dpg.file_dialog(
            label="Save Project As",
            callback=callback,
            modal=True,
            directory_selector=False,
            default_filename=f"{dpg.get_value('project_name')}"
        ):
            dpg.add_file_extension(".json", color=(0, 255, 0, 255))

    def prepare_project_data(self):
        # Collect headers
        headers = {}
        for header, widgets in self.headers_widgets.items():
            headers[header] = {
                "enabled": dpg.get_value(widgets["cb"]),
                "value": dpg.get_value(widgets["input"])
            }
        
        # Collect parser values, excluding deleted ones
        parser_values = {}
        parser_values["value_1"] = {
            "name": "status",
            "valid_string": dpg.get_value("valid_string"),
            "method": "GET"
        }
        
        for i in range(2, self.next_value_id):
            if i not in self.deleted_value_ids and dpg.does_item_exist(f"value_name_{i}"):
                parser_values[f"value_{i}"] = {
                    "name": dpg.get_value(f"value_name_{i}"),
                    "url": dpg.get_value(f"value_url_{i}"),
                    "after": dpg.get_value(f"value_after_{i}"),
                    "before": dpg.get_value(f"value_before_{i}"),
                    "method": dpg.get_value(f"value_method_{i}") if dpg.does_item_exist(f"value_method_{i}") else "GET"
                }

        return {
            "projectSettings": {
                "projectName": dpg.get_value("project_name")
            },
            "requestSettings": {
                "domain": dpg.get_value("domain"),
                "method": dpg.get_value("method"),
                "url": dpg.get_value("url"),
                "body": dpg.get_value("body"),
                "headers": headers
            },
            "parserSettings": {
                "useParser": dpg.get_value("use_parser"),
                "values": parser_values
            }
        }

    def load_project_data(self, data):
        # Основные настройки
        dpg.set_value("project_name", data["projectSettings"].get("projectName", ""))
        dpg.set_value("domain", data["requestSettings"].get("domain", ""))
        dpg.set_value("method", data["requestSettings"].get("method", "GET"))
        dpg.set_value("url", data["requestSettings"].get("url", ""))
        dpg.set_value("body", data["requestSettings"].get("body", ""))
        
        # Заголовки
        headers_data = data["requestSettings"].get("headers", {})
        for header in self.headers_widgets:
            if header in headers_data:
                widget = self.headers_widgets[header]
                dpg.set_value(widget["cb"], headers_data[header].get("enabled", False))
                dpg.set_value(widget["input"], headers_data[header].get("value", ""))
        
        # Парсер
        parser_data = data.get("parserSettings", {})
        dpg.set_value("use_parser", parser_data.get("useParser", False))
        
        # Загрузка значений парсера
        values_data = parser_data.get("values", {})
        for key in values_data:
            value_id = int(key.split("_")[1])
            value_data = values_data[key]
            
            if value_id == 1:  # Status validation
                dpg.set_value("valid_string", value_data.get("valid_string", ""))
            else:
                # Добавляем новое значение
                self.add_parser_value()
                current_id = self.next_value_id - 1
                dpg.set_value(f"value_name_{current_id}", value_data.get("name", ""))
                dpg.set_value(f"value_url_{current_id}", value_data.get("url", ""))
                dpg.set_value(f"value_after_{current_id}", value_data.get("after", ""))
                dpg.set_value(f"value_before_{current_id}", value_data.get("before", ""))
                dpg.set_value(f"value_method_{current_id}", value_data.get("method", "GET"))

    def load_cookies(self):
        try:
            # Здесь должна быть реализация выбора файла через oxyapi
            self.cookies = http.cookiejar.MozillaCookieJar()
            dpg.set_value("status", "Cookies loaded successfully")
        except Exception as e:
            dpg.set_value("status", f"Error: {str(e)}")

    def load_project(self):
        try:
            # Заглушка для реализации загрузки проекта
            with open("example.json", "r") as f:
                project_data = json.load(f)
            
            dpg.set_value("project_name", project_data.get("project_name", ""))
            dpg.set_value("domain", project_data.get("domain", ""))
            dpg.set_value("method", project_data.get("method", "GET"))
            dpg.set_value("url", project_data.get("url", ""))
            dpg.set_value("body", project_data.get("body", ""))
            
            dpg.set_value("status", "Project loaded successfully")
        except Exception as e:
            dpg.set_value("status", f"Load error: {str(e)}")

    def create_project(self):
        project_data = {
            "project_name": dpg.get_value("project_name"),
            "domain": dpg.get_value("domain"),
            "method": dpg.get_value("method"),
            "url": dpg.get_value("url"),
            "body": dpg.get_value("body"),
        }
        
        try:
            with open(f"{project_data['project_name']}.json", "w") as f:
                json.dump(project_data, f, indent=4)
            dpg.set_value("status", "Project saved successfully")
        except Exception as e:
            dpg.set_value("status", f"Save error: {str(e)}")

    def send_request(self):
        if not self.cookies:
            dpg.set_value("status", "Load cookies first!")
            return

        try:
            session = requests.Session()
            session.cookies = self.cookies
            
            # Collect enabled headers
            headers = {}
            for header, widgets in self.headers_widgets.items():
                if dpg.get_value(widgets["cb"]):  # Only include enabled headers
                    headers[header] = dpg.get_value(widgets["input"])
            
            response = session.request(
                method=dpg.get_value("method"),
                url=dpg.get_value("url"),
                headers=headers,
                data=dpg.get_value("body")
            )
            
            # Show raw response
            dpg.set_value("response", response.text)
            
            # Handle parsing if enabled
            if dpg.get_value("use_parser"):
                parsed_results = {"status": "invalid"}  # Default status
                
                # Check status validation
                valid_string = dpg.get_value("valid_string")
                if valid_string and valid_string in response.text:
                    parsed_results["status"] = "valid"
                
                # Parse other values
                for parser_value in self.parser_values:
                    value_id = parser_value.id
                    if dpg.does_item_exist(f"value_name_{value_id}"):
                        name = dpg.get_value(f"value_name_{value_id}")
                        after = dpg.get_value(f"value_after_{value_id}")
                        before = dpg.get_value(f"value_before_{value_id}")
                        
                        # Extract value using after/before markers
                        if after and before:
                            start = response.text.find(after) + len(after)
                            end = response.text.find(before, start)
                            if start != -1 and end != -1:
                                parsed_results[f"value_{value_id}"] = response.text[start:end].strip()
                
                # Display parsed results as formatted JSON
                dpg.set_value("parsed_response", json.dumps(parsed_results, indent=2))
            
            dpg.set_value("status", "Request successful")
        except Exception as e:
            dpg.set_value("status", f"Request failed: {str(e)}")

    def parse_response(self, text):
        after = dpg.get_value("pars_after")
        before = dpg.get_value("pars_before")
        start = text.find(after) + len(after) if after else 0
        end = text.find(before, start) if before else len(text)
        return text[start:end] if start != -1 and end != -1 else None

class ParserValue:
    def __init__(self, parent, id):
        self.id = id
        # Проверяем существование группы перед созданием
        tag = f"parser_value_{id}"
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
            
        with dpg.group(parent=parent, horizontal=True, tag=tag):
            dpg.add_input_text(label=f"Value_{id}", tag=f"value_name_{id}", width=100)
            dpg.add_input_text(label="URL", tag=f"value_url_{id}", width=200)
            dpg.add_input_text(label="After", tag=f"value_after_{id}", width=150)
            dpg.add_input_text(label="Before", tag=f"value_before_{id}", width=150)
            dpg.add_button(label="×", callback=self.delete, tag=f"delete_{id}")

    def delete(self):
        if dpg.does_item_exist(f"parser_value_{self.id}"):
            dpg.delete_item(f"parser_value_{self.id}")
        # Добавляем ID в список удаленных
        for window in dpg.get_windows():
            if dpg.get_item_label(window) == "Project Creator":
                for child in dpg.get_item_children(window, slot=1):
                    if isinstance(dpg.get_item_user_data(child), CookieProjectCreator):
                        creator = dpg.get_item_user_data(child)
                        creator.deleted_value_ids.add(self.id)
                        # Также удаляем из списка активных значений
                        if self in creator.parser_values:
                            creator.parser_values.remove(self)
                        break

def setup_ui():
    def pidoras():
        oxyapi.in_modal = True
        dpg.configure_item("ProjectCreator", show=True)
    dpg.add_button(label="Open Creator", callback=pidoras)
    creator = CookieProjectCreator()

if __name__ == "__main__":
    raise RuntimeError("This is a plugin and should not be run directly")