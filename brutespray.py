#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from argparse import RawTextHelpFormatter
import sys, time, os
import subprocess
import xml.dom.minidom
import re
import argparse
import argcomplete
import itertools
import conversions
from multiprocessing import Process

services = {}

class colors:
    white = "\033[1;37m"
    normal = "\033[0;00m"
    red = "\033[1;31m"
    blue = "\033[1;34m"
    green = "\033[1;32m"
    lightblue = "\033[0;34m"

banner = colors.red + r"""
                              #@                           @/              
                           @@@                               @@@           
                        %@@@                                   @@@.        
                      @@@@@                                     @@@@%      
                     @@@@@                                       @@@@@     
                    @@@@@@@                  @                  @@@@@@@    
                    @(@@@@@@@%            @@@@@@@            &@@@@@@@@@    
                    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    
                     @@*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ @@     
                       @@@( @@@@@#@@@@@@@@@*@@@,@@@@@@@@@@@@@@@  @@@       
                           @@@@@@ .@@@/@@@@@@@@@@@@@/@@@@ @@@@@@           
                                  @@@   @@@@@@@@@@@   @@@                  
                                 @@@@*  ,@@@@@@@@@(  ,@@@@                 
                                 @@@@@@@@@@@@@@@@@@@@@@@@@                 
                                  @@@.@@@@@@@@@@@@@@@ @@@                  
                                    @@@@@@ @@@@@ @@@@@@                    
                                       @@@@@@@@@@@@@                       
                                       @@   @@@   @@                       
                                       @@ @@@@@@@ @@                       
                                         @@% @  @@                 

"""+'\n' \
+ r"""
        ██████╗ ██████╗ ██╗   ██╗████████╗███████╗███████╗██████╗ ██████╗  █████╗ ██╗   ██╗
        ██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
        ██████╔╝██████╔╝██║   ██║   ██║   █████╗  ███████╗██████╔╝██████╔╝███████║ ╚████╔╝ 
        ██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  ╚════██║██╔═══╝ ██╔══██╗██╔══██║  ╚██╔╝  
        ██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗███████║██║     ██║  ██║██║  ██║   ██║   
        ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
                                                                                   
"""+'\n' \
+ '\n brutespray.py v1.4' \
+ '\n Created by: Shane Young/@x90skysn3k && Jacob Robles/@shellfail' \
+ '\n Inspired by: Leon Johnson/@sho-luv' + colors.normal + '\n'
#ascii art by: Cara Pearson

def make_dic_gnmap():
    global services
    port = None
    with open(args.file, 'r') as nmap_file:
        for line in nmap_file:
            supported = ['ssh','ftp','postgresql','telnet',
                        'mysql','ms-sql-s','shell','vnc',
                        'imap','imaps','nntp','pcanywheredata',
                        'pop3','pop3s','exec','login','microsoft-ds',
                        'smtp', 'smtps','submission','svn','iss-realsecure']
            for name in supported:
                matches = re.compile(r'([0-9][0-9]*)/open/[a-z][a-z]*//' + name)
                try:
                    port =  matches.findall(line)[0]
                except:
                    continue
    
                ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', line)
                tmp_ports = matches.findall(line)
                for tmp_port in tmp_ports:
                    try:
                        name = conversions.nmap_to_medusa[name]
                    except KeyError:
                        pass

                    if name in services:
                        if tmp_port in services[name]:
                            services[name][tmp_port] += ip
                        else:
                            services[name][tmp_port] = ip
                    else:
                        services[name] = {tmp_port:ip}


def make_dic_xml():
    global services
    supported = ['ssh','ftp','postgresql','telnet',
                'mysql','ms-sql-s','shell','vnc',
                'imap','imaps','nntp','pcanywheredata',
                'pop3','pop3s','exec','login','microsoft-ds',
                'smtp','smtps','submission','svn','iss-realsecure']
    doc = xml.dom.minidom.parse(args.file)

    for host in doc.getElementsByTagName("host"):
        try:
            address = host.getElementsByTagName("address")[0]
            ip = address.getAttribute("addr")
            eip = ip.encode("utf8")
            iplist = eip.split(',')
        except:
            # move to the next host
            continue
        try:
            status = host.getElementsByTagName("status")[0]
            state = status.getAttribute("state")
        except:
            state = ""
        try:
            ports = host.getElementsByTagName("ports")[0]
            ports = ports.getElementsByTagName("port")
        except:
            continue

        for port in ports:
            pn = port.getAttribute("portid")
            state_el = port.getElementsByTagName("state")[0]
            state = state_el.getAttribute("state")
            if state == "open":
                try:
                    service = port.getElementsByTagName("service")[0]
                    port_name = service.getAttribute("name")
                except:
                    service = ""
                    port_name = ""
                    product_descr = ""
                    product_ver = ""
                    product_extra = ""
                name = port_name.encode("utf-8")
                tmp_port = pn.encode("utf-8")
                if name in supported:
                    try:
                        name = conversions.nmap_to_medusa[name]
                    except KeyError:
                        pass

                    if name in services:
                        if tmp_port in services[name]:
                            services[name][tmp_port] += iplist
                        else:   
                         services[name][tmp_port] = iplist
                    else:
                        services[name] = {tmp_port:iplist}


def brute(service,port,fname):  

    if args.userlist is None and args.username is None:
        userlist = 'wordlist/'+service+'/user'
        uarg = '-U'
    elif args.userlist:
        userlist = args.userlist
        uarg = '-U'
    elif args.username:
        userlist = args.username
        uarg = '-u'

    if args.passlist is None and args.password is None:
        passlist = 'wordlist/'+service+'/password'
        parg = '-P'
    elif args.passlist:
        passlist = args.passlist
        parg = '-P'
    elif args.password:
        passlist = args.password
        parg = '-p'
    
    if args.continuous:
        cont = ''
    else:
        cont = '-F'
    
    p = subprocess.Popen(['medusa', '-H', fname, uarg, userlist, parg, passlist, '-M', service, '-t', args.threads, '-n', port, '-T', args.hosts, cont],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, bufsize=-1)

    out = "[" + colors.green + "+" + colors.normal + "] "
    output = 'output/' + service + '-success.txt'
    
 
    for line in iter(p.stdout.readline, b''):
        print line,
        sys.stdout.flush()
        time.sleep(0.0001)
        if 'SUCCESS' in line:
            f = open(output, 'a')
            f.write(out + line)
            f.close()    
   
def animate():
        t_end = time.time() + 2
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if not time.time() < t_end:
                break
            sys.stdout.write('\rStarting to brute, please make sure to use the right amount of threads(-t) and parallel hosts(-T)...  ' + c)
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\n\nBrute-Forcing...     \n') 
        time.sleep(1)

def parse_args():
    
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description=\
 
    "Usage: python brutemap.py <OPTIONS> \n")

    menu_group = parser.add_argument_group(colors.lightblue + 'Menu Options' + colors.normal)
    menu_group.add_argument('-f', '--file', help="GNMAP or XML file to parse", required=True)
    menu_group.add_argument('-s', '--service', help="specify service to attack", default="all")
    menu_group.add_argument('-t', '--threads', help="number of medusa threads", default="2")
    menu_group.add_argument('-T', '--hosts', help="number of hosts to test concurrently", default="1")
    menu_group.add_argument('-U', '--userlist', help="reference a custom username file", default=None)
    menu_group.add_argument('-P', '--passlist', help="reference a custom password file", default=None)
    menu_group.add_argument('-u', '--username', help="specify a single username", default=None)
    menu_group.add_argument('-p', '--password', help="specify a single password", default=None)
    menu_group.add_argument('-c', '--continuous', help="keep brute-forcing after success", default=False, action='store_true')
    
    argcomplete.autocomplete(parser)    
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    print(banner)
    args = parse_args()
    if not os.path.exists("tmp/"):
        os.mkdir("tmp/")
    tmppath = "tmp/"
    filelist = os.listdir(tmppath)
    for filename in filelist:
        os.remove(tmppath+filename)
    if not os.path.exists("output/"):
        os.mkdir("output/")

    try:
        doc = xml.dom.minidom.parse(args.file)
        make_dic_xml()
    except:
        make_dic_gnmap()
    animate()
    
    to_scan = args.service.split(',')
    for service in services:
        if service in to_scan or to_scan == ['all']:
            for port in services[service]:
                fname = 'tmp/'+service + '-' + port
                iplist = services[service][port]
                f = open(fname, 'w+')
                for ip in iplist:
                    f.write(ip + '\n')
                f.close()
                brute_process = Process(target = brute, args=(service,port,fname))
                brute_process.start()
