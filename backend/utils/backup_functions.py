import logging
import subprocess
import os
from typing import Optional
import threading
from collections.abc import Iterator, Sequence


logger = logging.getLogger("postgre_dump")


# Пример
# save_pg_dump(FileHelper.temp.path/"dumpfile.bin", Settings.DB_NAME, Settings.DB_HOST, Settings.DB_PORT, Settings.DB_USER, Settings.DB_PASS)
def save_pg_dump(
        output_path: str,
        db_name: str,
        host: str = "localhost",
        port: int = 5432,
        user: Optional[str] = None,
        password: Optional[str] = None,
        format: str = 'c'  # 'c' (custom postgresql bin file, recommended), 'p' (plain SQL text), 't' (tar archive)
) -> bool:
    """
    Создает дамп базы данных PostgreSQL с использованием pg_dump.

    Args:
        db_name: Имя базы данных для дампа.
        output_path: Полный путь к файлу, куда будет сохранен дамп.
        host: Хост базы данных. По умолчанию 'localhost'.
        port: Порт базы данных. По умолчанию 5432.
        user: Пользователь базы данных. Если None, используется переменная окружения PGPASSWORD
              или метод аутентификации по умолчанию.
        password: Пароль пользователя. Если задан, передается через переменную окружения PGPASSWORD.
        format: Формат дампа. По умолчанию 'c' (custom).

    Returns:
        True, если дамп успешно создан, False в противном случае.
    """
    # 1. Формирование списка аргументов для команды pg_dump
    command = [
        "pg_dump",
        f"--host={host}",
        f"--port={port}",
        f"--format={format}",
        f"--file={output_path}",
        db_name
    ]

    if user:
        command.insert(1, f"--username={user}")

    # 2. Установка переменной окружения для пароля (рекомендуемый способ)
    # Это позволяет избежать передачи пароля в виде аргумента командной строки.
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password

    logger.info("Запуск pg_dump для базы '%s'...", db_name)
    logger.info("Параметры: host=%s, port=%d, format=%s", host, port, format)
    logger.info("Сохранение в файл: %s", output_path)

    # 3. Запуск процесса
    try:
        # Убираем проверку 'check=True', чтобы явно обрабатывать stderr
        process = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            check=False  # Отключаем автоматическое исключение, чтобы логгировать stderr
        )

        # 4. Проверка кода возврата и вывод логов
        if process.returncode == 0:
            logger.info("Дамп базы данных успешно создан.")
            return True
        else:
            # Ошибка выполнения pg_dump
            logger.error("Ошибка при выполнении pg_dump (код возврата %d):", process.returncode)

            # Вывод сообщения об ошибке из stderr
            error_output = process.stderr.strip()
            if error_output:
                logger.error("--- stderr ---\n%s\n--------------", error_output)

            # Логгирование полной команды (без пароля)
            command_for_log = [arg for arg in command if 'PGPASSWORD' not in arg]
            logger.error("Использованная команда (без пароля): %s", ' '.join(command_for_log))
            return False

    except FileNotFoundError:
        logger.error("Ошибка: Утилита 'pg_dump' не найдена.")
        logger.error("Убедитесь, что PostgreSQL установлен, и 'pg_dump' доступен в PATH.")
        return False


def stream_pg_dump(
    db_name: str,
    host: str = "localhost",
    port: int = 5432,
    user: Optional[str] = None,
    password: Optional[str] = None,
    format: str = "c",
    chunk_size: int = 1024 * 1024,  # 1 MB
) -> Iterator[bytes]:
    """
    Запускает pg_dump и потоково возвращает его stdout.

    Дамп НЕ сохраняется на диск.
    Данные pg_dump передаются непосредственно вызывающему коду.

    Args:
        db_name: Имя базы данных.
        host: Хост PostgreSQL.
        port: Порт PostgreSQL.
        user: Пользователь PostgreSQL.
        password: Пароль PostgreSQL.
        format: Формат дампа:
            'c' - custom, рекомендуемый;
            'p' - plain SQL;
            't' - tar.
        chunk_size: Размер одного передаваемого чанка.

    Yields:
        Чанки pg_dump в виде bytes.

    Raises:
        FileNotFoundError: если pg_dump отсутствует.
        RuntimeError: если pg_dump завершился с ошибкой.
    """

    command = [
        "pg_dump",
        f"--host={host}",
        f"--port={port}",
        f"--format={format}",
        db_name,
    ]

    if user:
        command.insert(1, f"--username={user}")

    env = os.environ.copy()

    if password:
        env["PGPASSWORD"] = password

    logger.info(
        "Запуск pg_dump для базы '%s' (host=%s, port=%d, format=%s)",
        db_name,
        host,
        port,
        format,
    )

    process = None
    stderr_data = bytearray()

    try:
        process = subprocess.Popen(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        # stderr нужно читать параллельно, иначе теоретически pipe
        # может заполниться и pg_dump заблокируется.
        def read_stderr():
            assert process is not None
            assert process.stderr is not None

            while True:
                data = process.stderr.read(4096)

                if not data:
                    break

                stderr_data.extend(data)

        stderr_thread = threading.Thread(
            target=read_stderr,
            daemon=True,
        )
        stderr_thread.start()

        assert process.stdout is not None

        # Читаем stdout pg_dump кусками и сразу отдаём наружу.
        while True:
            chunk = process.stdout.read(chunk_size)

            if not chunk:
                break

            yield chunk

        # Дожидаемся завершения pg_dump.
        return_code = process.wait()

        # stderr thread должен успеть дочитать последние данные.
        stderr_thread.join()

        if return_code != 0:
            error_output = stderr_data.decode(
                "utf-8",
                errors="replace",
            ).strip()

            logger.error(
                "Ошибка при выполнении pg_dump (код возврата %d)",
                return_code,
            )

            if error_output:
                logger.error(
                    "--- stderr ---\n%s\n--------------",
                    error_output,
                )

            command_for_log = " ".join(command)

            logger.error(
                "Использованная команда: %s",
                command_for_log,
            )

            raise RuntimeError(
                f"pg_dump завершился с кодом {return_code}"
            )

        logger.info(
            "pg_dump успешно завершён для базы '%s'.",
            db_name,
        )

    except FileNotFoundError:
        logger.error(
            "Ошибка: утилита 'pg_dump' не найдена. "
            "Убедитесь, что PostgreSQL установлен "
            "и pg_dump доступен в PATH."
        )

        raise

    finally:
        if process is not None:
            # Если генератор был закрыт раньше окончания pg_dump
            # (например, клиент разорвал HTTP-соединение),
            # обязательно убиваем дочерний процесс.
            if process.poll() is None:
                logger.warning(
                    "Остановка pg_dump из-за прерывания streaming."
                )

                process.kill()

            if process.stdout:
                process.stdout.close()

            if process.stderr:
                process.stderr.close()



def stream_tar(
    base_dir: str,
    files: Sequence[str] | None = None,
    compression: bool = True,
    chunk_size: int = 1024 * 1024,  # 1 MB
) -> Iterator[bytes]:
    """
    Потоково создаёт tar/tar.gz из директории или выбранных файлов.

    Архив НЕ сохраняется на диск.

    Если files пустой или None, в архив попадает вся base_dir.

    Args:
        base_dir:
            Базовая директория.

        files:
            Список относительных путей файлов относительно base_dir.
            Если список пустой или None — архивируется вся директория.

        compression:
            Использовать gzip-сжатие (tar.gz).

        chunk_size:
            Размер одного передаваемого чанка.

    Yields:
        Чанки tar/tar.gz в виде bytes.

    Raises:
        FileNotFoundError:
            Если base_dir или один из файлов не существует.

        ValueError:
            Если путь выходит за пределы base_dir.

        IsADirectoryError:
            Если один из указанных путей является директорией.

        RuntimeError:
            Если tar завершился с ошибкой.
    """

    base_dir = os.path.abspath(base_dir)

    if not os.path.isdir(base_dir):
        raise FileNotFoundError(
            f"Базовая директория не существует: {base_dir}"
        )

    command = ["tar", "-c"]

    if compression:
        command.append("-z")

    command.extend(["-f", "-"])

    if not files:
        # Архивируем всю директорию.
        #
        # Используем родительскую директорию, чтобы в архиве
        # сохранилось имя самой base_dir:
        #
        # /data/files/
        #     -> files/
        #         -> ...
        parent_dir = os.path.dirname(base_dir)
        folder_name = os.path.basename(base_dir)

        command.extend([
            "-C",
            parent_dir,
            folder_name,
        ])

        item_count = "all"

    else:
        # Архивируем только указанные файлы.
        normalized_files: list[str] = []

        for file_path in files:
            if not file_path:
                raise ValueError(
                    "Имя файла не может быть пустым."
                )

            if os.path.isabs(file_path):
                raise ValueError(
                    f"Абсолютный путь запрещён: {file_path}"
                )

            full_path = os.path.abspath(
                os.path.join(base_dir, file_path)
            )

            # Защита от ../
            try:
                relative_path = os.path.relpath(
                    full_path,
                    base_dir,
                )
            except ValueError:
                raise ValueError(
                    f"Некорректный путь: {file_path}"
                )

            if (
                relative_path == os.pardir
                or relative_path.startswith(os.pardir + os.sep)
            ):
                raise ValueError(
                    f"Путь выходит за пределы base_dir: {file_path}"
                )

            if not os.path.exists(full_path):
                raise FileNotFoundError(
                    f"Файл не существует: {file_path}"
                )

            if os.path.isdir(full_path):
                raise IsADirectoryError(
                    f"Ожидался файл, получена директория: {file_path}"
                )

            normalized_files.append(relative_path)

        command.extend([
            "-C",
            base_dir,
            *normalized_files,
        ])

        item_count = len(normalized_files)

    logger.info(
        "Запуск tar для %s элементов из '%s' (compression=%s)",
        item_count,
        base_dir,
        compression,
    )

    process = None
    stderr_data = bytearray()

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        # Читаем stderr параллельно, чтобы pipe не переполнился
        # и tar не заблокировался.
        def read_stderr() -> None:
            assert process is not None
            assert process.stderr is not None

            while True:
                data = process.stderr.read(4096)

                if not data:
                    break

                stderr_data.extend(data)

        stderr_thread = threading.Thread(
            target=read_stderr,
            daemon=True,
        )
        stderr_thread.start()

        assert process.stdout is not None

        # Потоково отдаём stdout tar вызывающему коду.
        while True:
            chunk = process.stdout.read(chunk_size)

            if not chunk:
                break

            yield chunk

        return_code = process.wait()

        # Ждём завершения чтения stderr.
        stderr_thread.join()

        if return_code != 0:
            error_output = stderr_data.decode(
                "utf-8",
                errors="replace",
            ).strip()

            logger.error(
                "Ошибка при выполнении tar (код возврата %d)",
                return_code,
            )

            if error_output:
                logger.error(
                    "--- stderr ---\n%s\n--------------",
                    error_output,
                )

            logger.error(
                "Использованная команда: %s",
                " ".join(command),
            )

            raise RuntimeError(
                f"tar завершился с кодом {return_code}"
            )

        logger.info(
            "tar успешно завершён для '%s'.",
            base_dir,
        )

    except FileNotFoundError:
        # Если base_dir существует, значит ошибка, скорее всего,
        # связана с отсутствием самого tar.
        if os.path.isdir(base_dir):
            logger.error(
                "Утилита 'tar' не найдена в PATH."
            )

        raise

    finally:
        if process is not None:
            # Если генератор закрыли раньше времени
            # (например, клиент разорвал HTTP-соединение),
            # останавливаем дочерний процесс.
            if process.poll() is None:
                logger.warning(
                    "Остановка tar из-за прерывания streaming."
                )

                process.kill()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            if process.stdout:
                process.stdout.close()

            if process.stderr:
                process.stderr.close()



                