import time
import paramiko
import requests

# importing data from config.py
from config import SOURCES, ROUTER_IP, DEFAULT_USER, CHUNK_SIZE, VPN_INTERFACE, PASSWORD

import re

def safe_group_name(name: str) -> str:
    """Делает имя object-group безопасным для CLI (без пробелов и спецсимволов)."""
    name = name.strip().lower()
    name = name.replace(' ', '-')
    name = re.sub(r'[^a-z0-9._-]+', '-', name)  # только безопасные символы
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name or "group"

def get_clean_domains(url):

    print(f"    [WEB] Загрузка списка: {url}...")

    # Маскируемся под браузер, чтобы нас не заблокировали
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code == 404:
            print("    [ОШИБКА 404] Файл не найден.")
            return []

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"    [СБОЙ СЕТИ] {e}")
        return []

    content = response.text
    lines = content.splitlines()
    clean_list = []
    seen = set()  # Множество для проверки дубликатов на лету

    for line in lines:
        line = line.strip()

        # Пропускаем пустоту и комментарии
        if not line or line.startswith('#'):
            continue

        # Логика очистки от "*"
        if line.startswith('*.'):
            clean_domain = line[2:]
        elif line.startswith('*'):
            clean_domain = line[1:]
        else:
            clean_domain = line

        # Дополнительная защита: убираем возможные пробелы внутри строки
        clean_domain = clean_domain.split()[0]

        # Добавляем только если такого домена еще не было
        if clean_domain not in seen:
            clean_list.append(clean_domain)
            seen.add(clean_domain)

    return clean_list


def get_clean_subnets(url):
    print(f"    [WEB] Загрузка списка подсетей: {url}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code == 404:
            print("    [ОШИБКА 404] Файл не найден.")
            return []

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"    [СБОЙ СЕТИ] {e}")
        return []

    content = response.text
    lines = content.splitlines()
    clean_list = []
    seen = set()

    for line in lines:
        line = line.strip()

        if not line or line.startswith('#'):
            continue

        subnet = line.split()[0]

        if subnet not in seen:
            clean_list.append(subnet)
            seen.add(subnet)

    return clean_list


def send_command(shell, cmd, sleep_time=0.1):
    """Отправляет команду в SSH-консоль и ждёт выполнения.

    Возвращает True при успехе, False если канал закрыт/оборван.
    """
    try:
        shell.send(cmd + "\n")
    except Exception as e:
        print(f"[SSH] Канал закрыт при отправке команды '{cmd}': {e}")
        return False

    time.sleep(sleep_time)

    # Вычитываем доступный вывод, чтобы буфер не забивался
    try:
        while shell.recv_ready():
            shell.recv(4096)
    except Exception:
        return False

    return True

def process_domain_list(prefix, valid_domains, shell, interface):
    if not valid_domains:
        print("    [ПУСТО] Нет валидных доменов или ошибка загрузки. Пропуск.")
        return

    count = len(valid_domains)
    print(f"    [OK] Получено записей: {count}")

    total_chunks = (count + CHUNK_SIZE - 1) // CHUNK_SIZE

    for i in range(total_chunks):
        chunk_num = i + 1
        base = safe_group_name(prefix)
        group_name = base if total_chunks == 1 else f"{base}-{chunk_num}"

        start = i * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk = valid_domains[start:end]

        print(f"    -> Отправка {chunk_num}/{total_chunks} в '{group_name}' ({len(chunk)} шт)... ", end='')

        if not send_command(shell, f"no object-group fqdn {group_name}", 0.05):
            print("    [SSH] Сессия оборвалась. Останов.")
            return
        if not send_command(shell, f"object-group fqdn {group_name}", 0.05):
            print("    [SSH] Сессия оборвалась. Останов.")
            return

        cmd_buffer = ""
        for d in chunk:
            cmd_buffer += f"include {d}\n"

        shell.send(cmd_buffer)

        wait_time = 0.5 + (len(chunk) / 50.0)
        time.sleep(wait_time)

        if shell.recv_ready():
            while shell.recv_ready():
                shell.recv(4096)

        route_cmd = f"dns-proxy route object-group {group_name} {interface} auto"
        if not send_command(shell, route_cmd, 0.1):
            print("    [SSH] Сессия оборвалась на маршрутизации. Останов.")
            return

        print("OK")


def process_source(name, data, shell, interface):
    prefix = data['prefix']

    print(f"\n>>> Модуль: {name}")

    valid_domains = []
    if 'list' in data:
        print("    [MODE] Локальный список (без скачивания)")
        valid_domains = data['list']
    elif 'url' in data:
        url = data['url']
        valid_domains = get_clean_domains(url)
    elif 'list' not in data and 'url' not in data:
        print("    [ОШИБКА] Не указан ни url, ни list.")

    subnet_list = []
    if 'subnets' in data:
        print("    [MODE] Локальный список подсетей (без скачивания)")
        subnet_list = data['subnets']
    elif 'subnets_url' in data:
        subnet_list = get_clean_subnets(data['subnets_url'])

    if not valid_domains and not subnet_list:
        print("    [ПУСТО] Нет валидных доменов или подсетей. Пропуск.")
        return
    if subnet_list:
        print(f"    [OK] Подсетей к добавлению: {len(subnet_list)}")

    combined = []
    seen = set()
    for item in valid_domains + subnet_list:
        if item not in seen:
            combined.append(item)
            seen.add(item)

    process_domain_list(prefix, combined, shell, interface)


def get_sorted_menu():
    """Сортировка меню для красоты"""
    all_keys = list(SOURCES.keys())
    priority = ["Antifilter (Community)", "ITDog (Russia)", "no-russia-hosts"]
    others = sorted([k for k in all_keys if k not in priority])
    return [k for k in priority if k in all_keys] + others


def main():
    print(r"""
   ______                __
  / ____/___  ________  / /_  _________
 / /   / _ \/ ___/ _ \/ __ \/ ___/ __ \
/ /___/  __/ /  /  __/ /_/ / /  / /_/ /
\____/\___/_/   \___/_.___/_/   \____/ 
    """)

    # 1. МЕНЮ
    sorted_sources = get_sorted_menu()

    print("Доступные источники:")
    for idx, key in enumerate(sorted_sources):
        print(f"{idx + 1}. {key}")

    print("\n Введите номера через запятую (напр: 1, 3) или 'all'.")
    choice = input("Cerebro > ").strip().lower()

    selected_keys = []
    if choice == 'all':
        selected_keys = sorted_sources
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            for i in indices:
                if 0 <= i < len(sorted_sources):
                    selected_keys.append(sorted_sources[i])
        except:
            print("[!] Ошибка ввода.")
            return

    if not selected_keys: return

    # 3. ПОДКЛЮЧЕНИЕ SSH
    print(f"\nСоединение с {ROUTER_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(ROUTER_IP, username=DEFAULT_USER, password=PASSWORD, timeout=10)
        shell = client.invoke_shell()
        time.sleep(1)
        if shell.recv_ready(): shell.recv(4096)

    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось подключиться: {e}")
        return

    # 4. ЗАПУСК ОБРАБОТКИ
    start_time = time.time()
    print(f"\n--- НАЧАЛО ОПЕРАЦИИ ({len(selected_keys)} задач) ---")

    for source_name in selected_keys:
        process_source(source_name, SOURCES[source_name], shell, VPN_INTERFACE)

    # 5. СОХРАНЕНИЕ НА РОУТЕРЕ
    print("\n[SYSTEM] Сохранение настроек (system configuration save)...")
    if not send_command(shell, "system configuration save", 5):
        print("[SSH] Сессия оборвалась при сохранении конфигурации.")
        return

    elapsed = round(time.time() - start_time, 1)
    print(f"\n=== ГОТОВО ({elapsed} сек) ===")

    client.close()
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()
