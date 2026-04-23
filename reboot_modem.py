#!/usr/bin/env python3
"""Reboot an Arris BGW210-700 modem via its HTTP management interface."""

import argparse
import hashlib
import logging
import os
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

LOGIN_PATH = "/cgi-bin/login.ha"
RESTART_PATH = "/cgi-bin/restart.ha"
RESTARTING_PATH = "/cgi-bin/restarting.ha"

logger = logging.getLogger("reboot_modem")


class NonceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nonce = None

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            attrs_dict = dict(attrs)
            if attrs_dict.get("name") == "nonce" and attrs_dict.get("type") == "hidden":
                self.nonce = attrs_dict.get("value")


def extract_nonce(html: str) -> str:
    nonce_parser = NonceParser()
    nonce_parser.feed(html)
    if not nonce_parser.nonce:
        raise ValueError("Could not find nonce in page")
    return nonce_parser.nonce


def hash_password(password: str, nonce: str) -> str:
    return hashlib.md5((password + nonce).encode()).hexdigest()


def reboot_modem(base_url: str, password: str, verify_ssl: bool = True) -> None:
    session = requests.Session()
    session.verify = verify_ssl
    # just get the initial SessionID cookie
    resp = session.get(urljoin(base_url, "/"), allow_redirects=True)
    resp.raise_for_status()

    # GET restart page — expect login form instead of restart form
    resp = session.get(urljoin(base_url, RESTART_PATH), allow_redirects=True)
    resp.raise_for_status()

    nonce = extract_nonce(resp.text)
    logger.debug(f"Login nonce: {nonce}...")

    # POST login credentials
    hashpwd = hash_password(password, nonce)
    login_data = {
        "nonce": nonce,
        "password": "*" * len(password),
        "hashpassword": hashpwd,
        "Continue": "Continue",
    }
    resp = session.post(urljoin(base_url, LOGIN_PATH), data=login_data, allow_redirects=True)
    resp.raise_for_status()

    if RESTART_PATH not in resp.url:
        raise RuntimeError(f"Login failed or unexpected redirect: {resp.url}")

    logger.info("Login successful.")

    # GET restart confirmation page to grab its nonce
    resp = session.get(urljoin(base_url, RESTART_PATH), allow_redirects=True)
    resp.raise_for_status()

    restart_nonce = extract_nonce(resp.text)
    logger.debug(f"Restart nonce: {restart_nonce}...")

    # POST restart
    restart_data = {
        "nonce": restart_nonce,
        "Restart": "Restart",
    }
    resp = session.post(urljoin(base_url, RESTART_PATH), data=restart_data, allow_redirects=True)
    resp.raise_for_status()

    if RESTARTING_PATH in resp.url:
        logger.info("Modem is rebooting.")
    else:
        raise RuntimeError(f"Restart did not trigger — landed on: {resp.url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reboot an Arris BGW210-700 modem.")
    parser.add_argument(
        "-c", "--host",
        default="192.168.1.254",
        help="Modem hostname or IP",
    )
    parser.add_argument("-p", "--password",
                        help="Modem device password. Required, but can be "
                             "specified with the MODEM_REBOOT_PASSWORD "
                             "environment variable instead.")
    parser.add_argument("-i", "--insecure", action="store_true",
                        help="Disable SSL certificate verification.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output.")
    args = parser.parse_args()
    logging.basicConfig(
        format="[%(asctime)s] %(name)s|%(levelname)s: %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO
    )
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    if not args.password:
        args.password = os.environ.get("MODEM_REBOOT_PASSWORD")
        if not args.password:
            raise RuntimeError("Password not provided and MODEM_REBOOT_PASSWORD environment variable not set")
    url = urlparse(args.host)
    if url.scheme:  # if the user specified a scheme (like "https://192.168.1.254")
        base_url = f"{url.scheme}://{url.netloc}"
    else:  # if user didn't specify a scheme (like "192.168.1.254"), urlparse will treat it as a path
        base_url = f"http://{url.path}"

    reboot_modem(base_url, args.password, verify_ssl=not args.insecure)
