# coding: utf-8
import datetime
import os
import glob
import json
import click
import config
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


def create_account(name):
    output = check_output_input(
        [config.BINARY, "keys", "add", name, "--output", "json"],
        input=config.KEYRING_PASSWORD
    ).decode()

    with open("keys/%s.json" % name, "w+") as w:
        w.write(output)


def send_funds(source, target, amount, fee):
    output = check_output_input([config.BINARY, "tx", "bank", "send",
                                 source,
                                 target,
                                 "%duumee" % amount,
                                 "--fees", "%duumee" % fee,
                                 "--output", "json",
                                 "--node", config.RPC_URL,
                                 "--chain-id", config.CHAIN_ID],
                                input=config.KEYRING_PASSWORD).decode()

    print(output)


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
        create_account(account_name)
    click.echo("Done")


@cli.command()
@click.option("--limit", type=click.IntRange(100, 100000000), required=True,
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
    for key_file in glob.glob("keys/*.json"):
        if key_file.endswith("main.json"):
            continue
        curr_key = read_key(key_file)
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
        send_funds(main_addr, target, amount=load_size, fee=fee)


if __name__ == "__main__":
    cli()
