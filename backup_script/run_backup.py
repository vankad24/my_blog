import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv


DB_LIMIT = 15
MEDIA_RETRIES = 10
RETRY_DELAY = 1
REQUEST_TIMEOUT = 300

DB_DIR = Path("db")
MEDIA_DIR = Path("media")


def download_db_backup(servername: str, access_key: str) -> None:
    url = f"https://{servername}/backup/db"
    params = {"access_key": access_key}

    print("Скачивание DB backup...")

    try:
	    response = requests.get(
	        url,
	        params=params,
	        timeout=REQUEST_TIMEOUT,
	    )

	    if response.status_code == 403:
	        raise RuntimeError("BACKUP_KEY неверный")

	    response.raise_for_status()

	except requests.RequestException as exc:
	    raise RuntimeError(f"Ошибка при скачивании DB backup: {exc}") from exc

    # Получаем имя файла из Content-Disposition.
    filename = None
    content_disposition = response.headers.get(
        "Content-Disposition",
        "",
    )

    if "filename=" in content_disposition:
        filename = content_disposition.split(
            "filename=",
            1,
        )[1].strip('"')

    if not filename:
        raise RuntimeError(
            "Сервер не передал имя DB backup файла "
            "через Content-Disposition"
        )

    filepath = DB_DIR / filename

    with filepath.open("wb") as f:
        for chunk in response.iter_content(
            chunk_size=1024 * 1024,
        ):
            if chunk:
                f.write(chunk)

    print(f"DB backup сохранён: {filepath}")

    cleanup_old_db_backups()


def cleanup_old_db_backups() -> None:
    files = [
        item
        for item in DB_DIR.iterdir()
        if item.is_file()
    ]

    if len(files) <= DB_LIMIT:
        return

    # Если дата находится в имени файла в формате,
    # который сортируется лексикографически (например YYYY-MM-DD),
    # этого достаточно.
    files.sort(key=lambda item: item.name)

    for filepath in files[:-DB_LIMIT]:
        print(f"Удаление старого backup: {filepath}")
        filepath.unlink()


def get_existing_media() -> list[str]:
    """
    Возвращает имена/пути всех локальных файлов относительно MEDIA_DIR.

    Например:
        media/
            a.png
            photos/
                b.jpg

    даст:
        ["a.png", "photos/b.jpg"]
    """

    return [
        item.relative_to(MEDIA_DIR).as_posix()
        for item in MEDIA_DIR.rglob("*")
        if item.is_file()
    ]


def get_media_list(
    servername: str,
    access_key: str,
) -> list[str]:
    url = f"https://{servername}/backup/list-media/"
    params = {"access_key": access_key}

    exclude = get_existing_media()

    print(
        f"Запрос списка media. "
        f"Локально уже есть: {len(exclude)} файлов"
    )

    try:
	    response = requests.post(
	        url,
	        params=params,
	        json={"exclude": exclude},
	        timeout=REQUEST_TIMEOUT,
	    )

	    if response.status_code == 403:
	        raise RuntimeError("BACKUP_KEY неверный")

	    response.raise_for_status()

	except requests.RequestException as exc:
	    raise RuntimeError(f"Ошибка при получении списка media: {exc}") from exc

    result = response.json()
    files = result.get("files", [])

    print(
        f"Сервер вернул файлов для скачивания: "
        f"{len(files)}"
    )

    return files


def download_media_file(
    servername: str,
    filename: str,
    access_key: str,
) -> bool:
    """
    Скачивает один media-файл с retry.

    filename может быть:
        a.png
        photos/a.png
        documents/2026/file.pdf
    """

    # quote нужен для корректной обработки пробелов,
    # кириллицы и прочих специальных символов в URL.
    encoded_filename = quote(
        filename,
        safe="/",
    )

    url = f"https://{servername}/media/{encoded_filename}"
    filepath = MEDIA_DIR / filename

    # Создаём необходимые вложенные директории.
    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_filepath = filepath.with_name(
        filepath.name + ".tmp"
    )

    for attempt in range(1, MEDIA_RETRIES + 1):
        try:
            print(
                f"Скачивание: {filename} "
                f"[{attempt}/{MEDIA_RETRIES}]"
            )

            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                stream=True,
            )
            response.raise_for_status()

            with temp_filepath.open("wb") as f:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024,
                ):
                    if chunk:
                        f.write(chunk)

            # Только после полного успешного скачивания
            # заменяем старый файл.
            temp_filepath.replace(filepath)

            print(f"Готово: {filename}")
            return True

        except (
            requests.RequestException,
            OSError,
        ) as exc:
            print(
                f"Ошибка при скачивании {filename}: {exc}"
            )

            # Удаляем потенциально повреждённый временный файл.
            if temp_filepath.exists():
                temp_filepath.unlink()

            if attempt < MEDIA_RETRIES:
                print(
                    f"Повтор через {RETRY_DELAY} секунд..."
                )
                time.sleep(RETRY_DELAY)

    print(
        f"ОШИБКА: {filename} не удалось скачать "
        f"после {MEDIA_RETRIES} попыток"
    )

    return False


def download_media(
    servername: str,
    access_key: str,
) -> None:
    files = get_media_list(
        servername,
        access_key,
    )

    failed = []

    for filename in files:
        success = download_media_file(
            servername,
            filename,
            access_key,
        )

        if not success:
            failed.append(filename)

    if failed:
        print()
        print("Не удалось скачать:")
        for filename in failed:
            print(f"  - {filename}")


def main() -> None:
    load_dotenv()

    servername = os.getenv("SERVER_NAME")
    access_key = os.getenv("BACKUP_KEY")

    if not servername:
        raise RuntimeError(
            "В .env отсутствует SERVER_NAME"
        )

    if not access_key:
        raise RuntimeError(
            "В .env отсутствует BACKUP_KEY"
        )

    servername = servername.rstrip("/")

    DB_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MEDIA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 1. DB backup
    download_db_backup(
        servername,
        access_key,
    )

    # 2. Media
    download_media(
        servername,
        access_key,
    )

    print()
    print("Backup завершён.")


if __name__ == "__main__":
    main()