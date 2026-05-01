#!/bin/bash
# Запуск системы ТЭС Оптимизация

cd "$(dirname "$0")"

echo "Запуск сервера..."
python3 server.py &
SERVER_PID=$!
sleep 2

echo "Запуск клиента..."
python3 client.py

echo "Завершение сервера..."
kill $SERVER_PID 2>/dev/null
