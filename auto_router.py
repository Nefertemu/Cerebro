import requests
import paramiko
import time
import getpass
import socket

# importing data from config.py
from config import SOURCES, ROUTER_IP, DEFAULT_USER, CHUNK_SIZE

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


def send_command(shell, cmd, sleep_time=0.1):
    """Отправляет команду в SSH консоль и ждет выполнения"""
    shell.send(cmd + "\n")
    time.sleep(sleep_time)
    if shell.recv_ready():
        while shell.recv_ready():
            shell.recv(4096)


def process_source(name, data, shell, interface):
    prefix = data['prefix']

    print(f"\n>>> Модуль: {name}")

    # --- НОВАЯ ЛОГИКА ---
    # Проверяем: если в настройках есть 'list', берем его
    if 'list' in data:
        print(f"    [MODE] Локальный список (без скачивания)")
        valid_domains = data['list']

    # Если списка нет, ищем 'url' и скачиваем
    elif 'url' in data:
        url = data['url']
        valid_domains = get_clean_domains(url)

    else:
        print("    [ОШИБКА] Не указан ни url, ни list.")
        return
    # --------------------

    if not valid_domains:
        print("    [ПУСТО] Нет валидных доменов или ошибка загрузки. Пропуск.")
        return

    count = len(valid_domains)
    print(f"    [OK] Получено чистых доменов: {count}")

    # Разбивка на чанки (порции)
    total_chunks = (count + CHUNK_SIZE - 1) // CHUNK_SIZE

    for i in range(total_chunks):
        chunk_num = i + 1
        group_name = prefix if total_chunks == 1 else f"{prefix}-{chunk_num}"

        start = i * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk = valid_domains[start:end]

        print(f"    -> Отправка {chunk_num}/{total_chunks} в '{group_name}' ({len(chunk)} шт)... ", end='')

        # Удаляем старую группу и создаем новую
        send_command(shell, f"no object-group fqdn {group_name}", 0.05)
        send_command(shell, f"object-group fqdn {group_name}", 0.05)

        # Формируем буфер команд
        cmd_buffer = ""
        for d in chunk:
            cmd_buffer += f"include {d}\n"

        shell.send(cmd_buffer)

        # Динамическая пауза: чем больше список, тем дольше ждем, чтобы роутер не захлебнулся
        wait_time = 0.5 + (len(chunk) / 50.0)
        time.sleep(wait_time)

        # Очистка буфера вывода (чтобы не забивать память)
        if shell.recv_ready():
            while shell.recv_ready(): shell.recv(4096)

        send_command(shell, "exit")

        # Настройка маршрутизации для этой группы
        route_cmd = f"dns-proxy route object-group {group_name} {interface} auto"
        send_command(shell, route_cmd, 0.1)

        print("OK")


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

    # 2. ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    try:
        user_pass = user_pass = input(f"\nВведите пароль для {DEFAULT_USER}: ")
        if not user_pass: return
        user_interface = input("Имя интерфейса (VPN), куда заворачивать (напр. Wireguard0): ").strip()
        if not user_interface: return
    except KeyboardInterrupt:
        return

    # 3. ПОДКЛЮЧЕНИЕ SSH
    print(f"\nСоединение с {ROUTER_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(ROUTER_IP, username=DEFAULT_USER, password=user_pass, timeout=10)
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
        process_source(source_name, SOURCES[source_name], shell, user_interface)

    # 5. СОХРАНЕНИЕ НА РОУТЕРЕ
    print("\n[SYSTEM] Сохранение настроек (system configuration save)...")
    send_command(shell, "system configuration save", 5)

    elapsed = round(time.time() - start_time, 1)
    print(f"\n=== ГОТОВО ({elapsed} сек) ===")

    client.close()
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()