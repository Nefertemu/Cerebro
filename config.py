# --- router settings ---
CHUNK_SIZE = 300
ROUTER_IP = "suboku.crazedns.ru"
DEFAULT_USER = "admin"
VPN_INTERFACE = "Wireguard0"
PASSWORD = "h6b-F@ss-aX$?J-Z!Ae"

# --- catalog ---
SOURCES = {
    "test": {
        "prefix": "test",
        "list": [
            "2ip.io",
            "whoer.net"
        ]
    },
    "ITDog inside": {
        "prefix": "itdog-inside",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"
    },
    "no-russia-hosts": {
        "prefix": "no-russia",
        "url": "https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts-wildcard.txt"
    },
    "meta": {
        "prefix": "meta",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Services/meta.lst",
        "subnets_url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/meta.lst"
    },
    "youtube": {
        "prefix": "youtube",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Services/youtube.lst"
    },
    "telegram": {
        "prefix": "telegram",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Services/telegram.lst",
        "subnets_url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Subnets/IPv4/telegram.lst"
    },
    "twitter": {
        "prefix": "twitter",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Services/twitter.lst"
    },
    "google AI": {
        "prefix": "google-ai",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Services/google_ai.lst"
    }
}
