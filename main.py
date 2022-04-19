import argparse
import requests
from api_key import api_key

url_prefix = "https://api.vultr.com/v2"
headers_api = {"Authorization": f"Bearer {api_key}"}


def get_credit():
    ans = requests.get(f"{url_prefix}/account", headers=headers_api).json()
    account = ans["account"]
    email = account["email"]
    credit = -round(account["balance"] + account["pending_charges"], 2)
    print(f"${credit}\t{email}\tlast_pay@{account['last_payment_date'].split('+')[0]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="python main.py")
    parser.add_argument('other', metavar='', type=str, nargs='*', help='other args')
    parser.add_argument('-c', '--credit', dest="c", action="store_true", default=False, help="显示余额")
    args = parser.parse_args()
    # print(args)
    if args.c:
        get_credit()
