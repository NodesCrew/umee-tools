# coding: utf-8
import datetime
import os
import glob
import json
import click
import config
import random
import datetime

from subprocess import PIPE
from subprocess import Popen
from subprocess import CalledProcessError


def fatal_error(message):
    print("\nFatal error: %s\n" % message)
    exit(-1)


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

    print("Execute command: %s" % (" ".join(*popenargs)))

    process = Popen(*popenargs, stdout=PIPE, stderr=PIPE, **kwargs)
    try:
        output, unused_err = process.communicate(inputdata)
        if output and not unused_err:
            pass

        if not output and unused_err:
            output = unused_err
            unused_err = b''
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if retcode:
        print("An error happens")
        print("stdout: %s" % output)
        print("stderr: %s" % unused_err)

        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output


def read_key(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        fatal_error("Unable to read key '%s': file not found." % path)


def get_balance(account):
    output = check_output_input([config.BINARY, "q", "bank", "balances",
                                 account,
                                 "--output", "json",
                                 "--node", config.RPC_URL],
                                input=config.KEYRING_PASSWORD).decode()
    balances = json.loads(output)["balances"]

    try:
        assert balances[0]["denom"] == "uumee"
    except (IndexError, KeyError):
        return 0

    return int(balances[0]["amount"])


def umeed_add_key(name):
    output = check_output_input(
        [config.BINARY, "keys", "add", name, "--output", "json"],
        input=config.KEYRING_PASSWORD
    ).decode()

    with open("keys/%s.json" % name, "w+") as w:
        w.write(output)


def umeed_import_key(name, mnemonic):
    input_ = b"%s\n%s" % (mnemonic.encode(), config.KEYRING_PASSWORD)
    output = check_output_input(
        [config.BINARY, "keys", "add", name, "--recover", "--output", "json"],
        input=input_
    ).decode()


def umeed_read_keys():
    output = check_output_input(
        [config.BINARY, "keys", "list", "--output", "json"],
        input=config.KEYRING_PASSWORD
    ).decode()
    return json.loads(output)


def umeed_send_tx(source, target, amount, fee):
    output = check_output_input([config.BINARY, "tx", "bank", "send",
                                 source,
                                 target,
                                 "%duumee" % amount,
                                 "--fees", "%duumee" % fee,
                                 "--output", "json",
                                 "--node", config.RPC_URL,
                                 "--chain-id", config.CHAIN_ID,
                                 "--yes"],
                                input=config.KEYRING_PASSWORD).decode()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--keys-number", type=click.IntRange(1, 100), required=True)
def create_keys(keys_number):
    if not os.path.exists("keys"):
        os.makedirs("keys")

    prefix = str(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    for i in range(0, keys_number):
        account_name = "%s_%s" % (prefix, i)
        click.echo("Create account %s" % account_name)
        umeed_add_key(account_name)
    click.echo("Done")


@cli.command()
def import_keys():
    click.echo("Read exists keys from umeed")
    exists_keys_names = set(k["name"] for k in umeed_read_keys())
    click.echo("Total %d exists keys found" % len(exists_keys_names))

    click.echo("Import keys from 'keys' directory into ummed wallets list")
    for key_path in glob.glob("keys/*.json"):
        if key_path.endswith("main.json"):
            continue

        key = read_key(key_path)
        if key["name"] in exists_keys_names:
            click.echo("Skip import exists key %s" % key["name"])
            continue

        click.echo("Start import for key %s" % key["name"])
        umeed_import_key(key["name"], key["mnemonic"])



@cli.command()
@click.option("--limit", type=click.IntRange(100, 100000000000), required=True,
              help="How many funds will be loaded to ALL keys from 'keys' dir")
@click.option("--fee", type=click.IntRange(0, 1000), required=True)
@click.option("--no-skip-funded", is_flag=True,
              help="Load already funded accounts")
def load_funds(limit, fee, no_skip_funded):
    click.echo("Check balance on main account")
    main_key = read_key("keys/main.json")
    main_addr = main_key["address"]
    main_balance = get_balance(main_addr)
    click.echo(">... %d" % main_balance)

    if main_balance < limit:
        fatal_error("main balance less than limit")

    click.echo("Read keys for loading")
    addresses = set()
    for key_path in glob.glob("keys/*.json"):
        if key_path.endswith("main.json"):
            continue
        curr_key = read_key(key_path)
        addresses.add(curr_key["address"])
    click.echo("Found %d keys" % len(addresses))

    total_comission = len(addresses) * fee
    click.echo("Total commission: %d" % total_comission)

    limit -= total_comission
    if limit < len(addresses):
        fatal_error("Total limit - total_commission < addresses count")

    load_size = int(limit / len(addresses))
    click.echo("%d tokens will sent to every address" % load_size)

    # Load funds
    addresses = list(sorted(addresses))
    while addresses:
        target = addresses.pop()

        if not no_skip_funded:
            balance = get_balance(target)
            if balance:
                click.echo("Skip %s with balance %s" % (target, balance))
                continue

        click.echo("Load %d tokens to %s" % (load_size, target))
        umeed_send_tx(main_addr, target, amount=load_size, fee=fee)


@cli.command()
def generate_workers():
    if not os.path.exists("workers"):
        os.makedirs("workers")

    click.echo("Get balances for all keys")
    balances = {}
    for key in umeed_read_keys():
        key_address = key["address"]
        key_balance = get_balance(key_address)

        if key_balance < 200:
            click.echo("Skip %s (balance %d)" % (key_address, key_balance))
            continue

        balances[key_address] = get_balance(key_address)
        click.echo("%s: %s" % (key_address, key_balance))

    click.echo("Total %d keys with balances" % (len(balances)))

    with open("spam.sh") as f:
        template = f.read()

    for key_address in balances:
        with open("workers/%s.sh" % key_address, "w+") as w:
            w.write(
                template.replace("CHAIN_ID", config.CHAIN_ID)
                        .replace("BINARY", config.BINARY)
                        .replace("RPC_URL", config.RPC_URL)
                        .replace("KEYRING_PASSWORD", config.KEYRING_PASSWORD)
                        .replace("SEND_FROM", key_address)
                        .replace("SEND_TO", random.choice(balances.keys()))
                        .replace()
            )


if __name__ == "__main__":
    cli()
