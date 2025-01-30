"""Oxygen Checker built-in plugin | BLTools Converter"""
import oxyapi
import dearpygui.dearpygui as dpg
import configparser
import json
import os

__oxy_name__ = "BLTools Converter"
__description__ = "Convert BLTools .proj files to JSON format"
__author__ = "белочка"
__version__ = "beta"
__api__ = 0 # major api version

def remove_bom(content):
    return content.replace('\ufeff', '')

def proj_to_json(proj_content):
    config = configparser.ConfigParser()
    cleaned_content = remove_bom(proj_content)
    config.read_string(cleaned_content)
    
    # Create parser values structure
    parser_values = {
        "value_1": {
            "name": "status",
            "valid_string": config["Request Settings"]["ResponseValide"],
            "method": "GET"
        }
    }
    
    # If parser is enabled, add value_2 for the main parsing
    if config["Parser Settings"]["UseParser"] == "True":
        parser_values["value_2"] = {
            "name": "plan",  # Default name, can be customized
            "url": config["Parser Settings"]["ParsURL"] or config["Request Settings"]["URL"],
            "after": config["Parser Settings"]["ParsAfter"],
            "before": config["Parser Settings"]["ParsBefore"],
            "method": "GET"
        }
    
    json_data = {
        "projectSettings": {
            "projectName": config["Project Settings"]["ProjectName"]
        },
        "requestSettings": {
            "domain": config["Request Settings"]["Domain"],
            "method": config["Request Settings"]["Method"],
            "url": config["Request Settings"]["URL"],
            "body": config["Request Settings"]["Body"],
            "headers": {
                "User-Agent": {
                    "enabled": config["Request Settings"]["UserAgent"].split("\t")[0] == "True",
                    "value": config["Request Settings"]["UserAgent"].split("\t")[1] if "\t" in config["Request Settings"]["UserAgent"] else ""
                },
                "Accept": {
                    "enabled": config["Request Settings"]["Accept"].split("\t")[0] == "True",
                    "value": "*/*"
                },
                "Content-Type": {
                    "enabled": config["Request Settings"]["ContentType"].split("\t")[0] == "True",
                    "value": "application/x-www-form-urlencoded"
                },
                "Referer": {
                    "enabled": config["Request Settings"]["Referer"].split("\t")[0] == "True",
                    "value": ""
                },
                "X-Requested-With": {
                    "enabled": config["Request Settings"]["X-Requested-With"].split("\t")[0] == "True",
                    "value": "XMLHttpRequest"
                }
            }
        },
        "parserSettings": {
            "useParser": True,
            "values": parser_values
        }
    }
    
    return json_data

def convert_proj_file(filename):
    try:
        with open(filename, "rb") as f:
            content = f.read().decode('utf-8-sig')
        json_config = proj_to_json(content)
        
        json_filename = filename.replace('.proj', '.json')
        with open(json_filename, "w", encoding='utf-8') as f:
            json.dump(json_config, f, indent=4)
        
        return True, f"Successfully converted {filename} to {json_filename}"
    except Exception as e:
        return False, f"Error converting {filename}: {str(e)}"

def fs_cb(_, path: dict, bulk: bool):
    if bulk:
        directory = path.get("file_path_name")
        successes = 0
        failures = 0
        
        for filename in os.listdir(directory):
            if filename.endswith('.proj'):
                full_path = os.path.join(directory, filename)
                success, message = convert_proj_file(full_path)
                if success:
                    successes += 1
                else:
                    failures += 1
                print(message)
        
        print(f"Conversion complete. Successes: {successes}, Failures: {failures}")
    else:
        filepath = path.get("file_path_name")
        if filepath.endswith('.proj'):
            success, message = convert_proj_file(filepath)
            print(message)
        else:
            print("Selected file is not a .proj file")

def on_one_conv():
    with dpg.file_dialog(label="Select .proj file", callback=fs_cb, modal=True, directory_selector=False, user_data=False):
        dpg.add_file_extension(".proj", color=(0, 255, 0, 255), custom_text="[BLTools Project]")

def on_bulk_conv():
    with dpg.file_dialog(label="Select path with projects", callback=fs_cb, modal=True, directory_selector=True, user_data=True):
        pass

def setup_ui():
    dpg.add_text("Converter may disbehave!", color=(255,255,0,255))
    dpg.add_button(label="Convert one", callback=on_one_conv)
    dpg.add_button(label="Bulk convert", callback=on_bulk_conv)

if __name__ == "__main__":
    raise ModuleNotFoundError()