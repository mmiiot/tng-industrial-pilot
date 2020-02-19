import socket # finding ip address used for websocket, get_ip_address
import netifaces as iface # finding ip address used for iface see get_ip_iface

def get_ip_address(test_url):
    # In: target IP , Out: IP of the interface that is used to reach it
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((test_url, 80))
        ip = s.getsockname()[0]
        #print("Test url: " + test_url + " IP: " + ip)
    except:
        ip = -1
    return ip

def get_ip_iface(test_iface):
    # In: interface name , Out: IP of the interface
    try:
        iface.ifaddresses(test_iface)
        ip = 0
    except:
        ip = -1
    if (ip==0):
        try:
            ip = iface.ifaddresses(test_iface)[iface.AF_INET][0]['addr']
            #print("Interface: " + test_iface + " IP: " + ip)
        except:
            ip = -1
    return ip

def get_netmask_iface(test_iface):
    # In: interface name , Out: subnetmask of the interface
    try:
        iface.ifaddresses(test_iface)
        netmask = 0
    except:
        netmask = -1
    if (netmask==0):
        try:
            netmask = iface.ifaddresses(test_iface)[iface.AF_INET][0]['netmask']
            #print("Interface: " + test_iface + " Subnet mask: " + netmask)
        except:
            netmask = -1
    return netmask

def get_gateway_iface(test_iface):
    # In: interface name , Out: default gateway of the interface
    try:
        gws = iface.gateways()
        gateway = gws['default'][iface.AF_INET]
        #if(test_iface in gateway):
        if(gateway != ''):
            gateway = gateway[0]
        else:
            gateway= -1
    except:
        gateway = -1
    return gateway
