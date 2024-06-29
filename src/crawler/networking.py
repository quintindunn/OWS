try:
    from .exceptions import CouldntFindNetworkInfoException
    from .urls import get_protocol_and_domain_from_url
except ImportError as e:
    from exceptions import CouldntFindNetworkInfoException
    from urls import get_protocol_and_domain_from_url

from ipaddress import IPv4Network, IPv4Address
import socket
import psutil


def _get_network_info() -> tuple[str, str]:
    """
    Gets the information on your network adapters
    :return:
    """
    net_if_addrs = psutil.net_if_addrs().items()

    if len(net_if_addrs) == 0:
        raise CouldntFindNetworkInfoException()

    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                network_ip = IPv4Network(
                    f"{addr.address}/{addr.netmask}", strict=False
                ).network_address
                yield network_ip, addr.netmask


def _is_ip_in_range(ip: IPv4Address, network_ip: str, subnet_mask: str) -> bool:
    """
    Checks if ip address is in an ip range.
    :param ip: Ip to check
    :param network_ip: Ip of the network
    :param subnet_mask: subnet mask of the network
    :return: True if the ip is in the range.
    """
    network = IPv4Network(f"{network_ip}/{subnet_mask}", strict=False)
    ip_addr = IPv4Address(ip)
    return ip_addr in network


def _is_ip_private(ip: IPv4Address) -> bool:
    """
    Checks if an ip address is private
    :param ip: Ip address to check
    :return: True if ip is in the private range
    """
    for network_ip, subnet_mask in _get_network_info():
        if _is_ip_in_range(ip, network_ip, subnet_mask) or ip.is_private:
            return True
    return False


def _resolve_domain_to_ip(domain: str) -> IPv4Address:
    """
    Performs a DNS lookup to get the IP address of a domain.
    :param domain: The domain to lookup
    :return: IPv4Address object of the domain
    """
    ip_address = IPv4Address(socket.gethostbyname(domain))
    return ip_address


def is_host_private(host: str) -> bool:
    """
    Checks if a host resolves to a private ip address.
    :param host: Host to check
    :return: True if the host resolves to a private ip address.
    """

    if "[" in host or "]" in host:
        return True

    ip = _resolve_domain_to_ip(host)
    return _is_ip_private(ip)
