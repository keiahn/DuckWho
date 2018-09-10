import datetime
import json
import logging
import os
import requests
import signal
import threading
import time

import myCommon


def master():
    logger = myCommon.MyLogger('main', 'myHA.log')
    logger.log(logging.INFO, 'Start')
    checker = MyChecker()
    checker.start()

    signal.signal(signal.SIGTERM, checker.set_end)

    while True:
        s = input()
        if s == 'exit':
            checker.is_end = True
            break

    checker.join()

    logger.log(logging.INFO, 'End')


class MySQLState:
       master = False
       agent = False


class MyChecker(threading.Thread):
    logger = myCommon.MyLogger('master', 'myHA.log')
    is_end = False
    my_config = myCommon.MyConfig()

    old_state = MySQLState()
    new_state = MySQLState()

    def __init__(self):
        print(myCommon.get_frame() + self.my_config.get_master_nic())
        print(myCommon.get_frame() + self.my_config.get_process_name())
        threading.Thread.__init__(self)

    def run(self):
        self.check_first()

        while self.is_end is False:
            time_start = datetime.datetime.now()

            if self.is_running(self.my_config.get_process_name()) is True:
                self.new_state.master = True
            else:
                self.new_state.master = False

            try:
                r = requests.get('http://{}:{}/?command=check'.format(self.my_config.get_agent_ip(),
                                                                      self.my_config.get_agent_port()))
                result = json.loads(r.text)
                if result['state'] == 'ok':
                    self.new_state.agent = True
                else:
                    self.new_state.agent = False
            except Exception as e:
                print(myCommon.get_frame() + e)

            if self.new_state.master is True:
                str_m = 'Master\'s \'{}\' is good.'.format(self.my_config.get_process_name())
            else:
                str_m = 'Master\'s \'{}\' is NOT good.'.format(self.my_config.get_process_name())

            if self.new_state.agent is True:
                str_a = 'Agent\'s \'{}\' is good.'.format(self.my_config.get_process_name())
            else:
                str_a = 'Agent\'s \'{}\' is NOT good.'.format(self.my_config.get_process_name())

            if self.new_state.master != self.old_state.master or self.new_state.agent != self.old_state.agent:
                if self.new_state.master is True and self.new_state.agent is True:
                    myCommon.vip_add(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
                    requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                        self.my_config.get_agent_port()))
                elif self.new_state.master is True and self.new_state.agent is False:
                    myCommon.vip_add(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
                    requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                        self.my_config.get_agent_port()))
                elif self.new_state.master is False and self.new_state.agent is True:
                    myCommon.vip_del(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
                    requests.get('http://{}:{}/?command=vip_add'.format(self.my_config.get_agent_ip(),
                                                                        self.my_config.get_agent_port()))
                else:
                    myCommon.vip_del(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
                    requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                        self.my_config.get_agent_port()))
            self.old_state.master = self.new_state.master
            self.old_state.agent = self.new_state.agent

            self.logger.log(logging.INFO, str_m + ' ' + str_a)

            time_end = datetime.datetime.now()
            time.sleep(1.0 - (time_end - time_start).total_seconds())

    def is_running(self, process_name):
        process_id_list = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in process_id_list:
            try:
                open_file = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read().decode('utf-8')
                if open_file.find(process_name) != -1:
                    return True
            except IOError:
                print(IOError.errno)
                self.logger.log(logging.ERROR, IOError.errno)
                return False
        return False

    def set_end(self):
        self.is_end = True

    def check_first(self):
        # Master의 MySQL 확인 ###########################################################################################
        if self.is_running(self.my_config.get_process_name()) is True:
            self.old_state.master_mysqld = True
        else:
            self.old_state.master_mysqld = False
        ################################################################################################################

        # Master의 Virtual IP 확인 ######################################################################################
        # command_line = 'ip address show dev {0} | grep {1} | wc -l'.format(self.my_config.get_agent_nic(),
        #                                                                    self.my_config.get_virtual_ip())
        # command_result = int(os.popen(command_line).read())
        # if command_result == 1:
        #     master_vip = True
        # else:
        #     master_vip = False;
        ################################################################################################################

        # Agent의 MySQL 확인 ############################################################################################
        r = requests.get('http://{}:{}/?command=check'.format(self.my_config.get_agent_ip(),
                                                              self.my_config.get_agent_port()))
        result = json.loads(r.text)
        if result['state'] == 'ok':
            self.old_state.agent = True
        else:
            self.old_state.agent = False
        ################################################################################################################

        # Agent의 Virtual IP 확인 #######################################################################################
        # r = requests.get('http://{}:{}/?command=do_you_have_vip'.format(self.my_config.get_agent_ip(),
        #                                                                 self.my_config.get_agent_port()))
        # result = json.loads(r.text)
        # if result['do_you_have_vip'] == 'yes':
        #     agent_vip = True
        # else:
        #     agent_vip = False
        ################################################################################################################

        if self.old_state.master is True and self.old_state.agent is True:
            myCommon.vip_add(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
            requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                self.my_config.get_agent_port()))
        elif self.old_state.master is True and self.old_state.agent is False:
            myCommon.vip_add(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
            requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                self.my_config.get_agent_port()))
        elif self.old_state.master is False and self.old_state.agent is True:
            myCommon.vip_del(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
            requests.get('http://{}:{}/?command=vip_add'.format(self.my_config.get_agent_ip(),
                                                                self.my_config.get_agent_port()))
        else:
            myCommon.vip_del(self.my_config.get_master_nic(), self.my_config.get_virtual_ip())
            requests.get('http://{}:{}/?command=vip_del'.format(self.my_config.get_agent_ip(),
                                                                self.my_config.get_agent_port()))
