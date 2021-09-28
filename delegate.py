# coding: utf-8
import os
import json
from subprocess import check_output


HOLD_UUMEE = 5000
COMM_UUMEE = 1000
VALOPER = "umeevaloper1p25t9pydn2jr5f2gtncwruyen58edaqzkt6un3"
UMEE_CHAIN = os.environ.get("UMEE_CHAIN")


def get_accounts():
    output = check_output(["umeed", "keys", "list"]).decode()

    lines = output.split("\n")
    accounts = list()

    for line in lines:
        line = line.strip()
        if not line.startswith("address:"):
            continue
        accounts.append(line.split(":")[1].strip())

    return accounts


def delegate(from_account, amount):
    output = " ".join(["umeed", "tx", "staking", "delegate", VALOPER, "%duumee" % amount, "--gas", "auto", "--chain-id", UMEE_CHAIN, "--from", from_account, "--fees", "%duumee" % COMM_UUMEE])
    print(output)


def get_balance(account):
    output = check_output(["umeed", "q", "bank", "balances", account, "-o json"]).decode()
    balances = json.loads(output)["balances"]

    try:
        assert balances[0]["denom"] == "uumee"
    except (IndexError, KeyError):
        #print("Unable to get balace for %s: %s" % (account, balances))
        return 0

    return int(balances[0]["amount"])


for account in get_accounts():
    balance = get_balance(account)

    amount = balance - HOLD_UUMEE - COMM_UUMEE

    if amount < 0:
        # print("Not delegate from %s: balance too small: %d" % (account, balance))
        continue

    #print("Delegate %d uumee from %s" % (amount, account))
    delegate(account, amount)

