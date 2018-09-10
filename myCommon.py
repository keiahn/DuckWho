import configparser
import inspect
import logging
import os


def get_frame():
    caller_frame_record = inspect.stack()[1]

    frame = caller_frame_record[0]
    info = inspect.getframeinfo(frame)

    value = '[{0}:{1} - {2}] - '.format(info.filename, info.lineno, info.function)
    return value


def vip_add(device_name, ip):
    command_line = 'ip address show dev {0} | grep {1} | wc -l'.format(device_name, ip)
    command_result = int(os.popen(command_line).read())
    if command_result == 0:
        command_line = 'ip address add dev {0} {1}/32'.format(device_name, ip)
        os.popen(command_line)


def vip_del(device_name, ip):
    command_line = 'ip address show dev {0} | grep {1} | wc -l'.format(device_name, ip)
    command_result = int(os.popen(command_line).read())
    if command_result == 1:
        command_line = 'ip address delete dev {0} {1}/32'.format(device_name, ip)
        os.popen(command_line)


class MyConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

    def get_log_name(self):
        return self.config['common']['log_name']

    def get_process_name(self):
        return self.config['common']['process_name']

    def get_virtual_ip(self):
        return self.config['virtual']['ip']

    def get_master_ip(self):
        return self.config['master']['ip']

    def get_master_nic(self):
        return self.config['master']['nic']

    def get_agent_ip(self):
        return self.config['agent']['ip']

    def get_agent_port(self):
        return int(self.config['agent']['port'])

    def get_agent_nic(self):
        return self.config['agent']['nic']


class MyLogger:
    def __init__(self, logger_name, file_name):
        self.logger = logging.getLogger(logger_name)
        # formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] - %(message)s')

        file_handler = logging.FileHandler(file_name)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)

    def log(self, level, msg):
        if level == logging.DEBUG:
            self.logger.debug(msg)
        elif level == logging.INFO:
            self.logger.info(msg)
        elif level == logging.WARNING:
            self.logger.warn(msg)
        elif level == logging.ERROR:
            self.logger.error(msg)
        elif level == logging.FATAL:
            self.logger.fatal(msg)
        else:
            print(get_frame() + 'level=\'%s\' msg=\'%s\'' % (level, msg))
