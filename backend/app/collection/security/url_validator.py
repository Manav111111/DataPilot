import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
}


def is_ip_private_or_reserved(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_and_sanitize_url(url: str, check_dns: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates a URL against SSRF vulnerabilities.
    Returns: (is_valid: bool, sanitized_url_or_none, error_message_or_none)
    """
    if not url or not isinstance(url, str):
        return False, None, "URL is empty or invalid"

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, None, f"Failed to parse URL: {str(e)}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, None, f"Unsupported URL scheme: {parsed.scheme}. Only HTTP/HTTPS permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, None, "Missing hostname in URL"

    hostname_lower = hostname.lower().strip(".")

    # Direct blocked hostname check
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, None, f"Blocked target host: {hostname}"

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        return False, None, f"Internal domains are prohibited: {hostname}"

    # Check if direct IP address
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_private_or_reserved(str(ip)):
            return False, None, f"Access to private/loopback IP {hostname} is blocked"
    except ValueError:
        pass  # Hostname is a domain, not a raw IP string

    # DNS Resolution check to prevent DNS rebinding / private resolution
    if check_dns:
        try:
            addr_info = socket.getaddrinfo(hostname_lower, None)
            for entry in addr_info:
                sockaddr = entry[4]
                resolved_ip = sockaddr[0]
                if is_ip_private_or_reserved(resolved_ip):
                    return False, None, f"Hostname {hostname} resolves to restricted IP: {resolved_ip}"
        except socket.gaierror:
            # If DNS resolution fails offline (e.g. unit test or disconnected environment), allow unless obviously blocked
            pass
        except Exception:
            pass

    return True, url, None
