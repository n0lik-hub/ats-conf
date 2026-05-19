"""
Модуль валидации данных для конфигурации IP-АТС Т76-С.
Содержит функции проверки корректности вводимых данных.
"""

import re
from typing import Tuple, Optional


def validate_hostname(hostname: str) -> Tuple[bool, str]:
    """
    Проверка имени хоста.
    Допустимы: латиница, цифры, _, -, .
    Максимум 63 символа.
    """
    if not hostname:
        return False, "Имя хоста не может быть пустым"
    
    if len(hostname) > 63:
        return False, "Имя хоста не должно превышать 63 символа"
    
    pattern = r'^[a-zA-Z0-9._-]+$'
    if not re.match(pattern, hostname):
        return False, "Имя хоста должно содержать только латиницу, цифры, символы '_', '-', '.'"
    
    return True, ""


def validate_ipv4(ip: str) -> Tuple[bool, str]:
    """
    Проверка IPv4 адреса.
    Четыре октета 0-255, без ведущих нулей (кроме самого 0).
    """
    if not ip:
        return False, "IP-адрес не может быть пустым"
    
    parts = ip.split('.')
    if len(parts) != 4:
        return False, "IP-адрес должен состоять из четырех октетов, разделенных точками"
    
    for part in parts:
        if not part:
            return False, "Октет не может быть пустым"
        
        # Проверка на ведущие нули (кроме "0")
        if len(part) > 1 and part[0] == '0':
            return False, f"Октет '{part}' содержит ведущие нули"
        
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False, f"Октет '{part}' должен быть в диапазоне 0-255"
        except ValueError:
            return False, f"Октет '{part}' должен быть числом"
    
    return True, ""


def validate_netmask(mask: str) -> Tuple[bool, str]:
    """
    Проверка маски подсети.
    Должна быть корректной маской (последовательность единиц слева).
    """
    valid, msg = validate_ipv4(mask)
    if not valid:
        return False, msg
    
    # Преобразуем маску в двоичный вид
    parts = mask.split('.')
    binary = ''.join(format(int(p), '08b') for p in parts)
    
    # Проверяем, что единицы идут подряд слева
    if '01' in binary:
        return False, "Некорректная маска подсети: единицы должны идти подряд слева"
    
    return True, ""


def validate_mac(mac: str) -> Tuple[bool, str]:
    """
    Проверка MAC-адреса.
    Формат: XX:XX:XX:XX:XX:XX (шестнадцатеричные цифры).
    """
    if not mac:
        return False, "MAC-адрес не может быть пустым"
    
    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    if not re.match(pattern, mac):
        return False, "MAC-адрес должен быть в формате XX:XX:XX:XX:XX:XX (шестнадцатеричные цифры)"
    
    return True, ""


def validate_iface_name(name: str) -> Tuple[bool, str]:
    """
    Проверка имени интерфейса.
    Допустимы: eth0, eth1, eth0:0..eth0:9, eth1:0..eth1:9
    """
    if not name:
        return False, "Имя интерфейса не может быть пустым"
    
    # eth0 или eth1
    if name in ['eth0', 'eth1']:
        return True, ""
    
    # eth0:0 .. eth0:9 или eth1:0 .. eth1:9
    pattern = r'^eth[01]:[0-9]$'
    if re.match(pattern, name):
        return True, ""
    
    return False, "Имя интерфейса должно быть eth0, eth1, eth0:0..eth0:9 или eth1:0..eth1:9"


def validate_integer(value: str, min_val: int, max_val: int, allow_empty: bool = False) -> Tuple[bool, str]:
    """
    Проверка целого числа в диапазоне.
    """
    if not value:
        if allow_empty:
            return True, ""
        return False, "Значение не может быть пустым"
    
    try:
        num = int(value)
        if num < min_val or num > max_val:
            return False, f"Число должно быть в диапазоне {min_val}-{max_val}"
        return True, ""
    except ValueError:
        return False, "Значение должно быть целым числом"


def validate_port_range(port_range: str, min_port: int = 1, max_port: int = 65535) -> Tuple[bool, str]:
    """
    Проверка диапазона портов.
    Формат: "1-15,17-31" или отдельные номера через запятую.
    """
    if not port_range:
        return False, "Диапазон портов не может быть пустым"
    
    parts = port_range.split(',')
    all_ports = set()
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Диапазон
            range_parts = part.split('-')
            if len(range_parts) != 2:
                return False, f"Некорректный диапазон: {part}"
            
            try:
                start = int(range_parts[0])
                end = int(range_parts[1])
                
                if start < min_port or end > max_port or start > end:
                    return False, f"Диапазон {part} выходит за пределы {min_port}-{max_port}"
                
                for p in range(start, end + 1):
                    if p in all_ports:
                        return False, f"Пересечение портов: {p}"
                    all_ports.add(p)
                    
            except ValueError:
                return False, f"Некорректный диапазон: {part}"
        else:
            # Отдельный порт
            try:
                port = int(part)
                if port < min_port or port > max_port:
                    return False, f"Порт {port} выходит за пределы {min_port}-{max_port}"
                if port in all_ports:
                    return False, f"Порт {port} указан повторно"
                all_ports.add(port)
            except ValueError:
                return False, f"Некорректный номер порта: {part}"
    
    return True, ""


def validate_cidr(cidr: str) -> Tuple[bool, str]:
    """
    Проверка CIDR нотации (например, 192.168.1.0/24).
    """
    if not cidr:
        return False, "CIDR не может быть пустым"
    
    parts = cidr.split('/')
    if len(parts) != 2:
        return False, "CIDR должен быть в формате IP/маска (например, 192.168.1.0/24)"
    
    ip, prefix = parts
    
    valid, msg = validate_ipv4(ip)
    if not valid:
        return False, f"Некорректный IP в CIDR: {msg}"
    
    try:
        prefix_num = int(prefix)
        if prefix_num < 0 or prefix_num > 32:
            return False, "Префикс CIDR должен быть в диапазоне 0-32"
    except ValueError:
        return False, "Префикс CIDR должен быть числом"
    
    return True, ""


def validate_extension_mask(mask: str) -> Tuple[bool, str]:
    """
    Проверка маски расширения.
    Может быть номером (цифры) или маской с _ и спецсимволами.
    Примеры: 101, _1XX, _20[1-5], _XXX.
    """
    if not mask:
        return False, "Маска/номер расширения не может быть пустым"
    
    # Простой номер (только цифры)
    if mask.isdigit():
        return True, ""
    
    # Маска начинается с _
    if not mask.startswith('_'):
        return False, "Маска должна начинаться с '_' или быть простым номером"
    
    # Проверяем допустимые символы в маске
    # X - любая цифра, Z - 1-9, N - 2-9, [0-9] - диапазон, . - любое количество цифр
    pattern = r'^_[XZN0-9.\[\]-]+$'
    if not re.match(pattern, mask):
        return False, "Недопустимые символы в маске. Используйте X, Z, N, [0-9], ."
    
    # Проверка корректности диапазонов в []
    if '[' in mask:
        bracket_pattern = r'\[([0-9]-[0-9]|[0-9]+)\]'
        brackets = re.findall(r'\[[^\]]*\]', mask)
        for bracket in brackets:
            if not re.match(bracket_pattern, bracket):
                return False, f"Некорректный диапазон в маске: {bracket}"
    
    return True, ""


def validate_logical_value(value: str, allowed: list) -> Tuple[bool, str]:
    """
    Проверка логического значения из списка допустимых.
    """
    if value.lower() in [v.lower() for v in allowed]:
        return True, ""
    return False, f"Значение должно быть одним из: {', '.join(allowed)}"


def validate_speed(speed: str) -> Tuple[bool, str]:
    """Проверка скорости интерфейса."""
    if not speed:
        return True, ""  # Опционально
    
    if speed in ['10', '100', '1000']:
        return True, ""
    return False, "Скорость должна быть 10, 100 или 1000"


def validate_duplex(duplex: str) -> Tuple[bool, str]:
    """Проверка дуплекса."""
    if not duplex:
        return True, ""  # Опционально
    
    if duplex.lower() in ['full', 'half']:
        return True, ""
    return False, "Дуплекс должен быть 'full' или 'half'"


def validate_autoneg(autoneg: str) -> Tuple[bool, str]:
    """Проверка автосогласования."""
    if not autoneg:
        return True, ""  # Опционально
    
    if autoneg.lower() in ['on', 'off']:
        return True, ""
    return False, "Автосогласование должно быть 'on' или 'off'"


def validate_channel_range(channel_range: str) -> Tuple[bool, str]:
    """
    Проверка диапазона каналов Zap.
    Формат: "1-15,17-31" или отдельный номер.
    """
    return validate_port_range(channel_range, min_port=1, max_port=110)


def validate_float(value: str, min_val: float = -1000.0, max_val: float = 1000.0, allow_empty: bool = True) -> Tuple[bool, str]:
    """
    Проверка числа с плавающей точкой.
    """
    if not value:
        if allow_empty:
            return True, ""
        return False, "Значение не может быть пустым"
    
    try:
        num = float(value)
        if num < min_val or num > max_val:
            return False, f"Число должно быть в диапазоне {min_val}-{max_val}"
        return True, ""
    except ValueError:
        return False, "Значение должно быть числом"
