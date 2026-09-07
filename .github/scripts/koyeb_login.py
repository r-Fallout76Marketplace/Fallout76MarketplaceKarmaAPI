#!/usr/bin/env python3
from os import getenv
from urllib import request


def main():

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://app.koyeb.com",
        "priority": "u=1, i",
        "referer": "https://app.koyeb.com/auth/signin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    json_data = {
        "email": getenv("KOYEB_EMAIL"),
        "password": getenv("KOYEB_PASSWORD"),
    }

    req = request.Request(
        "https://app.koyeb.com/v1/account/login",
        headers=headers,
        data=str(json_data).encode(),
    )
    with request.urlopen(req) as response:
        print(response.read().decode())


if __name__ == "__main__":
    main()
