import logging
from os import path

def debug_log_config(name):
    path_name = path.join("logs", "".join(('log_',name,'.log')))
    logging.basicConfig(filename=path_name, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')