# coding: utf-8

CHAIN_ID = "umeevengers-1c"
BINARY = "umeed"
RPC_URL = "tcp://localhost:26657/"

KEYRING_PASSWORD = b"password\n"
VALOPER = ""


try:
    from config_local import *
except ImportError:
    print("config_local not created")