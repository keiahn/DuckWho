import os
import json
import time
import urllib

from http.server import BaseHTTPRequestHandler, HTTPServer

import myCommon


def agent(my_config):
    server_class = HTTPServer
    httpd = server_class((my_config.get_agent_ip(), my_config.get_agent_port()), MyAgent)

    print(myCommon.get_frame() + time.asctime(),
          'HTTPd starts - %s:%s' % (my_config.get_agent_ip(), my_config.get_agent_port()))
    try:
        httpd.serve_forever()
    except:
        pass
    httpd.server_close()

    print(myCommon.get_frame() + time.asctime(),
          'HTTPd stops - %s:%s' % (my_config.get_agent_ip(), my_config.get_agent_port()))


class MyAgent(BaseHTTPRequestHandler):
    my_config = myCommon.MyConfig()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self.respond()

    def handle_http(self, path):
        path1 = urllib.parse.urlparse(path)
        path2 = urllib.parse.parse_qs(path1.query)
        json_data = {}
        status_code = 200
        if path2.get('command') == ['do_you_have_vip']:
            command_line = 'ip address show dev {0} | grep {1} | wc -l'.format(self.my_config.get_agent_nic(),
                                                                               self.my_config.get_virtual_ip())
            command_result = int(os.popen(command_line).read())
            if command_result == 1:
                json_data = {'do_you_have_vip': 'yes'}
            else:
                json_data = {'do_you_have_vip': 'no'}
        elif path2.get('command') == ['check']:
            if self.is_running() is True:
                json_data = {'mode': 'agent', 'state': 'ok'}
            else:
                json_data = {'mode': 'agent', 'state': 'not'}
        elif path2.get('command') == ['vip_add']:
            myCommon.vip_add(self.my_config.get_agent_nic(), self.my_config.get_virtual_ip())
        elif path2.get('command') == ['vip_del']:
            myCommon.vip_del(self.my_config.get_agent_nic(), self.my_config.get_virtual_ip())
        else:
            print(myCommon.get_frame() + 'Unknown : {}'.format(path2))
            status_code = 500

        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        json_string = json.dumps(json_data)
        content = '{}'.format(json_string)

        return bytes(content, 'UTF-8')

    def respond(self):
        response = self.handle_http(self.path)
        self.wfile.write(response)

    def is_running(self):
        process_id_list = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        for pid in process_id_list:
            try:
                open_file = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read().decode('utf-8')
                if open_file.find(self.my_config.get_process_name()) != -1:
                    return True
            except IOError:
                # print(myCommon.get_frame() + IOError.errno)
                return False
        return False
