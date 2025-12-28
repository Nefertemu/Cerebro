import requests


def get_clean_domains(url):
    print(f"Скачиваю список с: {url}...")

    # 1. Делаем запрос к сайту
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка, что скачалось без ошибок (код 200)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании: {e}")
        return []

    # 2. Получаем текст ответа
    content = response.text

    # Разбиваем весь текст на отдельные строки
    lines = content.splitlines()

    clean_list = []  # Сюда будем складывать готовые домены

    # 3. Обрабатываем каждую строку
    for line in lines:
        # Удаляем пробелы и символы переноса строки по краям (на всякий случай)
        line = line.strip()

        # Пропускаем пустые строки или комментарии (если они есть)
        if not line or line.startswith('#'):
            continue

        # 4. Логика очистки от "*"
        # Если строка начинается с "*.", мы отрезаем первые 2 символа
        if line.startswith('*.'):
            clean_domain = line[2:]
            # Если вдруг строка начинается просто с "*", отрезаем 1 символ
        elif line.startswith('*'):
            clean_domain = line[1:]
        else:
            # Если звездочек нет, оставляем как есть
            clean_domain = line

        clean_list.append(clean_domain)

    print(f"Готово! Обработано доменов: {len(clean_list)}")
    return clean_list


# --- Запуск функции ---
url_source = "https://raw.githubusercontent.com/dartraiden/no-russia-hosts/refs/heads/master/hosts-wildcard.txt"
domains = get_clean_domains(url_source)

# Выведем первые 10 штук для проверки
print("\nПример первых 10 доменов:")
for d in domains[:10]:
    print(d)