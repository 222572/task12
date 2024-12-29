import socket
import os
import mimetypes
import threading
from datetime import datetime

# Конфигурация сервера
HOST = ''  # Это означает, что сервер будет слушать все интерфейсы
PORT = 8080
DOCUMENT_ROOT = './www'  # Папка с веб-контентом
MAX_REQUEST_SIZE = 8192  # Максимальный размер запроса

# Логирование запросов
def log_request(ip, file_name, status_code):
    with open('server.log', 'a') as log_file:
        log_file.write(f"{datetime.now()} - {ip} - {file_name} - {status_code}\n")

# Определение MIME-типа файла
def get_content_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type if mime_type else 'application/octet-stream'

# Обработка запроса клиента
def handle_request(conn):
    data = conn.recv(MAX_REQUEST_SIZE)
    if not data:
        return
    request = data.decode()
    print("Request received:")
    print(request)

    # Парсим запрос
    lines = request.splitlines()
    request_line = lines[0].split()
    method, path = request_line[0], request_line[1]
    
    # Путь к файлу
    if path == '/':
        path = '/index.html'
    
    file_path = os.path.join(DOCUMENT_ROOT, path.lstrip('/'))
    
    # Проверка типа файла (например, только .html, .css, .js)
    allowed_extensions = ['.html', '.css', '.js']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        response = (
            "HTTP/1.1 403 Forbidden\r\n"
            "Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n"
            "<h1>403 Forbidden</h1>"
        ).encode()
        conn.send(response)
        conn.close()
        return

    # Пытаемся найти запрашиваемый файл
    if os.path.exists(file_path) and os.path.isfile(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()

        content_type = get_content_type(file_path)
        
        # Заголовки ответа
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(content)}\r\n"
            f"Connection: close\r\n\r\n"
        ).encode() + content

        # Логируем успешный запрос
        log_request(conn.getpeername()[0], path, "200 OK")
    else:
        # Если файл не найден
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n\r\n"
            "<h1>404 Not Found</h1>"
        ).encode()

        # Логируем ошибку
        log_request(conn.getpeername()[0], path, "404 Not Found")

    conn.send(response)
    conn.close()

# Запуск сервера
def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"Server running on http://localhost:{PORT}")
        
        while True:
            conn, addr = sock.accept()
            print(f"Connected by {addr}")
            # Обрабатываем запрос в новом потоке
            threading.Thread(target=handle_request, args=(conn,)).start()

if __name__ == "__main__":
    run_server()
