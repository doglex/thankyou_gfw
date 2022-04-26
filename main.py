import argparse
import requests
from api_key import api_key, ssh_pub
from datetime import datetime
from time import sleep
import pyperclip

url_prefix = "https://api.vultr.com/v2"
headers_api = {"Authorization": f"Bearer {api_key}"}


def get_credit():
    ans = requests.get(f"{url_prefix}/account", headers=headers_api).json()
    account = ans["account"]
    email = account["email"]
    credit = -round(account["balance"] + account["pending_charges"], 2)
    print(f"${credit}\t{email}\tlast_pay@{account['last_payment_date'].split('+')[0]}")


def run_by_shell():
    parser = argparse.ArgumentParser(prog="python main.py")
    parser.add_argument('other', metavar='', type=str, nargs='*', help='other args')
    parser.add_argument('-c', '--credit', dest="c", action="store_true", default=False, help="显示余额")
    parser.add_argument('-i', '--install', dest="i", action="store_true", default=False, help="新建节点")
    parser.add_argument('-d', '--destroy', dest="d", action="store_true", default=False, help="删除所有节点")
    parser.add_argument('-l', '--list', dest="l", action="store_true", default=False, help="列出节点")
    args = parser.parse_args()
    # print(args)
    if args.c:
        get_credit()
    if args.i:
        create_instance()
    if args.d:
        remove_all_instances()
    if args.l:
        list_instances()


def list_ssh_keys():
    ans = requests.get(f"{url_prefix}/ssh-keys", headers=headers_api).json()
    print(ans)


def create_ssh_key():
    ans = requests.post(f"{url_prefix}/ssh-keys", headers=headers_api,
                        json={"name": "thankyou_gfw", "ssh_key": ssh_pub}).json()
    print(ans)


def get_ssh_key(n=0):
    ans = requests.get(f"{url_prefix}/ssh-keys", headers=headers_api).json()
    key_n = ans["ssh_keys"][n]["id"]
    print(f"ssh_key: {key_n}")
    return key_n


def list_regions():
    ans = requests.get(f"{url_prefix}/regions", headers=headers_api, ).json()
    for region in sorted(ans["regions"], key=lambda x: x["country"]):
        print(f"{region['id']}, {region['city']}, {region['country']}")


def list_plans():
    ans = requests.get(f"{url_prefix}/plans", headers=headers_api, ).json()
    plans = ans["plans"]
    plans = [p for p in plans if p["id"].startswith("vc2") or p["id"].startswith("vhp")]
    plans = [p for p in plans if p["monthly_cost"] < 32]
    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    df = pd.DataFrame(plans)
    df.to_csv("plans.csv", index=False)
    print(df)
    #  vhp-1c-2gb-amd ,   vhp-1c-2gb-amd ,   vc2-1c-2gb,  vc2-1c-1gb


def list_os():
    ans = requests.get(f"{url_prefix}/os", headers=headers_api, ).json()
    print(ans)


def create_instance(remove_old=True):
    if remove_old:
        remove_all_instances()
    the_name = "x-" + str(datetime.now())[:19].replace(" ", "-").replace(":", "-")
    print(the_name)
    json = {
        "region": "lax",
        "plan": "vc2-1c-2gb",
        "label": "x",
        "os_id": 352,
        "backups": "disabled",
        "enable_ipv6": True,
        "hostname": the_name,
        "sshkey_id": [get_ssh_key(), ]
    }
    ans = requests.post(f"{url_prefix}/instances", headers=headers_api, json=json)
    print(ans.json())
    sleep(3)
    the_ip = None
    while 1:
        try:
            ans2 = requests.get(f"{url_prefix}/instances", headers=headers_api, timeout=3).json()
        except:
            print("busy")
            sleep(3)
            continue
        ok = False
        for instance in ans2["instances"]:
            iid = instance["id"]
            hostname = instance["hostname"]
            if hostname != the_name:
                continue
            ip = instance["main_ip"]
            status = instance["status"]
            power_status = instance["power_status"]
            info = [iid, hostname, ip, status, power_status]
            print(" | ".join(info))
            if power_status == "running" and status == "active":
                the_ip = ip
                ok = True
        if ok:
            break
        sleep(5)
    try_times = 10
    while try_times:
        try_times -= 1
        print("waiting 15 second")
        sleep(15)
        try:
            ssh_install_wireguard(the_ip)
            break
        except Exception as e:
            print(e)


def list_instances():
    ans = requests.get(f"{url_prefix}/instances", headers=headers_api, ).json()
    for instance in ans["instances"]:
        iid = instance["id"]
        hostname = instance["hostname"]
        ip = instance["main_ip"]
        status = instance["status"]
        power_status = instance["power_status"]
        info = [iid, hostname, ip, status, power_status]
        print(" | ".join(info))


def remove_all_instances():
    ans = requests.get(f"{url_prefix}/instances", headers=headers_api, ).json()
    for instance in ans["instances"]:
        iid = instance["id"]
        hostname = instance["hostname"]
        print(f"Removing {iid} | {hostname}")
        ans = requests.delete(f"{url_prefix}/instances/{iid}", headers=headers_api, )
        print(ans)

def ssh_install_wireguard(host="66.42.101.79"):
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        username="root",
        hostname=host,
        timeout=10
    )
    cmd = "wget --no-check-certificate -O /opt/wireguard.sh https://raw.githubusercontent.com/teddysun/across/master/wireguard.sh; chmod 755  /opt/wireguard.sh"
    print(cmd)
    stdin, stdout,  stderr = client.exec_command(cmd)
    stdin.close()
    std_ans = stdout.read().decode() + stderr.read().decode()
    print("std_ans=>", std_ans)


    cmd = "/opt/wireguard.sh -n"
    print(cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()
    while not stdout.channel.exit_status_ready():
        result = stdout.readline()
        print(result.strip("\n"))
    std_ans = stdout.read().decode() + stderr.read().decode()
    print("std_ans=>", std_ans)

    installed = False
    cmd = "/opt/wireguard.sh -r"  # todo
    print(cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()
    while not stdout.channel.exit_status_ready():
        result = stdout.readline()
        if "Enjoy it" in result:
            installed = True
        print(result.strip("\n"))
    std_ans = stdout.read().decode() + stderr.read().decode()
    print("std_ans=>", std_ans)

    if not installed:
        cmd = "/opt/wireguard.sh -s"
        print(cmd)
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.close()
        while not stdout.channel.exit_status_ready():
            result = stdout.readline()
            if "Enjoy it" in result:
                installed = True
            print(result.strip("\n"))
        std_ans = stdout.read().decode() + stderr.read().decode()
        print("std_ans=>", std_ans)

    if not installed:
        print("Unable to Install Wireguard. Please change vps !!!")
    else:
        cmd = "cat /etc/wireguard/wg0_client "
        print(cmd)
        print(host)
        print("\n\n")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.close()
        std_ans = stdout.read().decode() + stderr.read().decode()
        print(std_ans)
        pyperclip.copy(std_ans)


if __name__ == '__main__':
    # get_credit()
    # get_ssh_key()
    # list_os()
    # create_instance()
    # list_instances()
    # remove_all_instances()
    # ssh_install_wireguard()
    run_by_shell()
