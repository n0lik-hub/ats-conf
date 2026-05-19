# Мастер конфигурации IP-АТС Т76-С

Программа для создания конфигурационных файлов IP-АТС Т76-С в пошаговом режиме.

## Требования

- Python 3.10+
- customtkinter

## Установка зависимостей

```bash
pip install -r requirements.txt
```

На Linux также может потребоваться установить пакет tkinter:

```bash
# Debian/Ubuntu
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter
```

## Запуск

```bash
python main.py
```

## Использование

1. Заполните обязательные разделы:
   - **SYSTEM** - имя хоста устройства
   - **NETWORK** - хотя бы один сетевой интерфейс
   - **EXTENSIONS** - хотя бы один контекст с расширением

2. Необязательные разделы можно пропустить.

3. Наведите курсор на поле ввода, чтобы увидеть подсказку.

4. На последней странице нажмите "Сохранить файл" для сохранения конфигурации.

## Структура проекта

- `main.py` - главный файл приложения
- `config_master.py` - классы данных и генератор конфигурации
- `gui_pages.py` - классы страниц интерфейса
- `requirements.txt` - зависимости

## Формат конфигурационного файла

Программа генерирует файл в формате `.conf` с кодировкой UTF-8 (без BOM) и переводом строк LF.

Пример минимальной конфигурации:

```
SYSTEM {
 HOSTNAME=ats1
}

NETWORK {
 IFACE {
  IFACE_NAME=eth0
  IP=192.168.10.10
  NETMASK=255.255.255.0
 }
}

EXTENSIONS {
 GENERAL {
  STATIC=false
  AUTOFALLTHROUGH=true
 }
 EXTENGROUP {
  NAME=main
  EXTEN="101:SIP/101::"
 }
}
```