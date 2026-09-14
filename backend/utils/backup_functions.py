import logging
import subprocess
import os
from typing import Optional
import threading
from collections.abc import Iterator


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


                