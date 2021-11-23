# coding: utf-8
import os
import json
from subprocess import check_output
from subprocess import (PIPE, Popen, CalledProcessError)


HOLD_UUMEE = 1
COMM_UUMEE = 0
VALOPER = "VALOPER_HERE"
UMEE_CHAIN = os.environ.get("UMEE_CHAIN")


PASSWD = b"PASSWORD_HERE\n"


def check_output_input(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    if 'input' in kwargs:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        inputdata = kwargs['input']
        del kwargs['input']
        kwargs['stdin'] = PIPE
    else:
        inputdata = None
    process = Popen(*popenargs, stdout=PIPE, **kwargs)
    try:
        output, unused_err = process.communicate(inputdata)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output



def get_accounts():
    output = check_output_input(["umeed", "keys", "list"], input=PASSWD).decode()

    lines = output.split("\n")
    accounts = list()

    for line in lines:
        line = line.strip()
        if not line.startswith("address:"):
            continue
        accounts.append(line.split(":")[1].strip())

    return accounts


def delegate(from_account, amount):
    output = " ".join(["umeed", "tx", "staking", "delegate", VALOPER,
                       "%duumee" % amount,
                       "--gas", "auto",
                       "--chain-id", UMEE_CHAIN, "--from", from_account,
                       "--fees",
                       "%duumee" % COMM_UUMEE, "-y"])

    command = ["umeed", "tx", "staking", "delegate", VALOPER,
               "%duumee" % amount,
               "--gas", "auto",
               "--chain-id", UMEE_CHAIN,
               "--from", from_account,
               "--fees", "%duumee" % COMM_UUMEE,
               "-y"]

    output = check_output_input(command, input=PASSWD)
    print(output)


def get_balance(account):
    output = check_output_input([
        "umeed", "q", "bank", "balances", account, "-o json"], input=PASSWD
    ).decode()
    balances = json.loads(output)["balances"]

    try:
        assert balances[0]["denom"] == "uumee"
    except (IndexError, KeyError):
        return 0

    return int(balances[0]["amount"])


for account in get_accounts():
    balance = get_balance(account)

    amount = balance - HOLD_UUMEE - COMM_UUMEE

    if amount < 0:
        continue

    #print("Delegate %d uumee from %s" % (amount, account))
    delegate(account, amount)