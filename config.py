# --- router settings ---
CHUNK_SIZE = 300
ROUTER_IP = "192.168.1.1"
DEFAULT_USER = "admin"

# --- catalog ---
SOURCES = {
    "Test": {
        "prefix": "test",
        "list": [
            "2ip.io",
            "fast.com",
            "speedtest.net",
            "ookla.com",
            "whoer.net"
        ]
    },
    "Antifilter": {
        "prefix": "antifilter",
        "url": "https://community.antifilter.download/list/domains.lst"
    },
    "ITDog inside": {
        "prefix": "itdog-inside",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"
    },
    "ITDog outside": {
        "prefix": "itdog-outside",
        "url": "https://raw.githubusercontent.com/itdoginfo/allow-domains/refs/heads/main/Russia/outside-raw.lst"
    },
    "no-russia-hosts": {
        "prefix": "no-russia",
        "url": "https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts-wildcard.txt"
    },
    "facebook": {
        "prefix": "facebook",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/facebook"
    },
    "instagram": {
        "prefix": "instagram",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/instagram"
    },
    "whatsapp": {
        "prefix": "whatsapp",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/whatsapp"
    },
    "youtube": {
        "prefix": "youtube",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/youtube"
    },
    "telegram": {
        "prefix": "telegram",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/telegram"
    },
    "twitter": {
        "prefix": "twitter",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/twitter"
    },
    "gemini": {
        "prefix": "gemini",
        "url": "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/google-deepmind"
    }
}