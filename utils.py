import os
import sys
import csv
import platform
import tarfile
import xml.etree.ElementTree as ET
import datetime
import subprocess
import shutil
import tarfile
import json
import time
import re
import logging

#from meaning.meaning import Meaning

class Utils:
    @staticmethod
    def get_base_path_folder():
        return os.path.dirname(__file__)

    @staticmethod
    def get_platform():
        version = platform.system().lower()
        if version.startswith('java'):
            import java.lang
            version = java.lang.System.getProperty("os.name").lower()
        
        return version

    @staticmethod
    def get_all_packages():
        return Utils.read_json((os.path.join(Utils.get_base_path_folder(), "modules", "packages.json")))

    @staticmethod
    def find_package(app):
        return Utils.get_all_packages().get(app)

    @staticmethod
    def find_app_name(package):
        for app, pack in Utils.get_all_packages().items():
            if package == pack:
                return app
        
        return None

    @staticmethod
    def generate_tar_gz_file(folder_path, generated_file_path):
        arcname = os.path.basename(generated_file_path).replace('.tar.gz', '')
        with tarfile.open(generated_file_path, mode='w:gz') as archive:
            archive.add(folder_path, recursive=True, arcname = arcname)
    
    @staticmethod
    def list_files(folder_name, filter_type = None):
        files_list = []
        if not folder_name or not os.path.exists(folder_name):
            return files_list

        for root, _, files in os.walk(os.path.join(Utils.get_base_path_folder(), folder_name)):
            for file in files:
                if filter_type:
                    extension = os.path.splitext(file)[1].strip().lower()
                    if not extension in filter_type:
                        if extension != "": #ignore files with extension
                            continue

                        if not ".db" in filter_type: #we are only checking header for sqlite for now
                            continue
                        
                        #verify sqlite files with extension
                        if not Utils.verify_header_signature(os.path.join(root, file), header_type = b"SQLite", offset = 0):
                            continue

                files_list.append(os.path.join(root, file))
        
        return files_list
    
    @staticmethod
    def get_current_time():
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def get_current_millis():
        return int(round(time.time() * 1000))
    
    #not necessary, remove in future?
    '''
    @staticmethod
    def export_columns_from_database(folder_path):
        meaning = Meaning()
        path = os.path.join(folder_path, 'DumpColumns.csv')
        print("[Utils] Dumping Columns to CSV. Base path {}".format(path))
        with open(path, 'w', newline='') as csvfile:
            fieldnames = ['database', 'table', 'column', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        
            for db in Utils.list_files(folder_path, filter_type = [".db"]):
                database_name = db.split("/")[-1]
                for table, columns in DatabaseParser.dump_columns(database = db).items():
                    meanings = meaning.get_meaning(database_name, table)
                    item = {}
                    item["database"] = db.replace(folder_path, '') #remove basepath
                    item["table"] = table
                    
                    for column in columns:
                        item["column"] = column
                        if meanings:
                            item["description"] = meanings.get(column)

                        writer.writerow(item)
    '''

    @staticmethod
    def safe_members(members): #used to clean : in folders
        for finfo in members:
            if re.sub('[<>:|?*"]', "", finfo.name) == str(finfo.name):
                yield finfo

    @staticmethod
    def extract_tar(file, path):
        tar = tarfile.open(file)
        tar.extractall(path, members = Utils.safe_members(tar))
        tar.close()

    @staticmethod
    def verify_header_signature(file, header_type, offset, stream = None):
        header = b""
        if stream:
            header = stream.read(32)
        else:
            with open(file, "rb") as f:
                header = f.read(32)

        query = header.find(header_type) #query includes position of header

        return True if query == offset else False

    @staticmethod
    def xml_attribute_finder(xml_path, attrib_values = None):
        listing = {}
        if not os.path.exists(xml_path):
            return None
            
        root = ET.parse(xml_path).getroot()
        for child in root:
            if not attrib_values or child.attrib.get("name") in attrib_values: #all values or specific value
                if child.attrib.get("value"):
                    value= child.attrib.get("value")
                else:
                    value = child.text

                try:
                    listing[child.attrib.get("name")] = str(value)
                except: #jython2 fix
                    listing[child.attrib.get("name")] = str(value.encode('utf-8','ignore'))

        return listing

    @staticmethod
    def check_and_generate_folder(path):
        if not os.path.exists(path):
            return os.makedirs(path)

        return True

    @staticmethod
    def replace_slash_platform(path):
        if Utils.get_platform().startswith("windows"):
            return path.replace('/', '\\')
        
        return path.replace('\\', '/')

    @staticmethod
    def get_adb_location():
        if Utils.get_platform().startswith("windows"):
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "windows", "adb.exe")
        elif Utils.get_platform().startswith("darwin"):
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "mac", "adb")
        else:
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "linux", "adb")
    
    @staticmethod
    def get_undark_location():
        if Utils.get_platform().startswith( "windows"):
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "windows", "undark.exe")
        elif Utils.get_platform().startswith("darwin"):
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "mac", "undark")
        else:
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "linux", "undark")

    @staticmethod
    def get_base64_location():
        if Utils.get_platform().startswith("windows"):
            return os.path.join(Utils.get_base_path_folder(), "dependencies", "windows", "base64.exe")
        else:
            return "base64"

    @staticmethod
    def run_undark(db):
        undark = Utils.get_undark_location()
        output = subprocess.Popen([undark,'-i', db, '--freespace'], shell=False, stdout=subprocess.PIPE).stdout.read()
        return output

    @staticmethod
    def remove_folder(folder):
        shutil.rmtree(folder)

    @staticmethod
    def read_json(path):
        f = open(path, "r")
        contents = json.loads(f.read())
        f.close()
        return contents

    @staticmethod
    def save_report(report_name, contents):
        f = open(report_name, "w")
        f.write(json.dumps(contents, indent=2))
        f.close()
    
    @staticmethod
    def log(log):
        
        # logging.info(log)
        logging.warning(log)
        logging.critical(log)
        logging.debug(log)
