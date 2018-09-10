import fcntl
# import logging
import os
import platform
import socket
import struct

import myMaster
import myAgent
import myCommon


def main():
    config = myCommon.MyConfig()

    ip_master = get_interface_ip(config.get_master_nic())
    ip_agent = get_interface_ip(config.get_agent_nic())
    print(myCommon.get_frame() + 'My IP({0}) : {1}'.format(config.get_master_nic(), ip_master))
    if ip_master == config.get_master_ip():
        print(myCommon.get_frame() + 'This is master.')
        myMaster.master()
    elif ip_agent == config.get_agent_ip():
        print(myCommon.get_frame() + 'This is agent.')
        myAgent.agent(config)


def get_interface_ip(device_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', bytes(device_name[:15], 'utf-8')))[20:24])


def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if os.name != 'nt':
        interfaces = [
            'eth0',
            'enp0s31f6',
        ]
        for eth in interfaces:
            try:
                ip = eth + ' : ' + get_interface_ip(eth)
                break
            except IOError:
                pass
    return ip


if __name__ == '__main__':
    try:
        f = open('config.ini', 'r')
        f.close()
    except:
        print('Failed to read \'config.ini\'.')
        exit(-1)

    if platform.system() != 'Linux':
        print(myCommon.get_frame() + 'OS is NOT Linux.')
        exit(-1)

    if os.geteuid() != 0:
        print(
            myCommon.get_frame() + 'You are NOT administrator. account=[ \'{0}({1})\' ].'.format(os.environ.get('USER'),
                                                                                                 os.geteuid()))
        exit(-1)

    main()
