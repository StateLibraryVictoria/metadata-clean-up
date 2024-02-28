import logging

def debug_log_config(name):
    logging.basicConfig(filename="".join(('log_',name,'.log')), encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')