import argparse
import requests
from api_key import api_key, ssh_pub

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
    args = parser.parse_args()
    # print(args)
    if args.c:
        get_credit()


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
    ans = requests.get(f"{url_prefix}/regions", headers=headers_api,).json()
    for region in sorted(ans["regions"], key=lambda x:x["country"]):
        print(f"{region['id']}, {region['city']}, {region['country']}")

def list_plans():
    ans = requests.get(f"{url_prefix}/plans", headers=headers_api, ).json()
    print(ans)






if __name__ == '__main__':
    # get_credit()
    # get_ssh_key()
    list_plans()
