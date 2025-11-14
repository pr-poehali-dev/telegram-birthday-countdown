import json
import os
import requests
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, Optional

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram bot webhook handler for birthday countdown
    Args: event with httpMethod, body from Telegram
    Returns: HTTP response
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method == 'POST':
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        db_url = os.environ.get('DATABASE_URL')
        
        if not bot_token:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not configured'})
            }
        
        update = json.loads(event.get('body', '{}'))
        
        if 'message' in update:
            handle_message(update['message'], bot_token, db_url)
        elif 'callback_query' in update:
            handle_callback(update['callback_query'], bot_token, db_url)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Method not allowed'})
    }

def send_message(chat_id: int, text: str, bot_token: str, reply_markup: Optional[Dict] = None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    requests.post(url, json=payload)

def answer_callback(callback_id: str, bot_token: str, text: str = ''):
    url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
    requests.post(url, json={'callback_query_id': callback_id, 'text': text})

def edit_message(chat_id: int, message_id: int, text: str, bot_token: str, reply_markup: Optional[Dict] = None):
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    requests.post(url, json=payload)

def get_user_data(user_id: int, db_url: str) -> Optional[Dict]:
    if not db_url:
        return None
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT user_id, user_name, birth_date FROM t_p25838731_telegram_birthday_co.users WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {'user_id': row[0], 'user_name': row[1], 'birth_date': row[2]}
    return None

def save_user_data(user_id: int, user_name: str, birth_date: str, db_url: str, chat_id: int = None):
    if not db_url:
        return
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    if chat_id:
        cur.execute("""
            INSERT INTO t_p25838731_telegram_birthday_co.users (user_id, user_name, birth_date, chat_id, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE 
            SET user_name = EXCLUDED.user_name, 
                birth_date = EXCLUDED.birth_date,
                chat_id = EXCLUDED.chat_id,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, user_name, birth_date, chat_id))
    else:
        cur.execute("""
            INSERT INTO t_p25838731_telegram_birthday_co.users (user_id, user_name, birth_date, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE 
            SET user_name = EXCLUDED.user_name, 
                birth_date = EXCLUDED.birth_date,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, user_name, birth_date))
    conn.commit()
    cur.close()
    conn.close()

def delete_user_data(user_id: int, db_url: str):
    if not db_url:
        return
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("DELETE FROM t_p25838731_telegram_birthday_co.users WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def save_realtime_message(user_id: int, chat_id: int, message_id: int, db_url: str):
    if not db_url:
        return
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO t_p25838731_telegram_birthday_co.realtime_messages (user_id, chat_id, message_id, created_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE 
        SET chat_id = EXCLUDED.chat_id, 
            message_id = EXCLUDED.message_id,
            created_at = CURRENT_TIMESTAMP
    """, (user_id, chat_id, message_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_realtime_message(user_id: int, db_url: str):
    if not db_url:
        return
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("DELETE FROM t_p25838731_telegram_birthday_co.realtime_messages WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_all_realtime_messages(db_url: str):
    if not db_url:
        return []
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        SELECT r.user_id, r.chat_id, r.message_id, u.birth_date 
        FROM t_p25838731_telegram_birthday_co.realtime_messages r
        JOIN t_p25838731_telegram_birthday_co.users u ON r.user_id = u.user_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'user_id': r[0], 'chat_id': r[1], 'message_id': r[2], 'birth_date': r[3]} for r in rows]

def get_all_users_for_notification(db_url: str):
    if not db_url:
        return []
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT user_id, chat_id, user_name, birth_date FROM t_p25838731_telegram_birthday_co.users WHERE chat_id IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'user_id': r[0], 'chat_id': r[1], 'user_name': r[2], 'birth_date': r[3]} for r in rows]

def get_next_birthday(birth_date: date) -> date:
    today = date.today()
    this_year_birthday = date(today.year, birth_date.month, birth_date.day)
    if this_year_birthday < today:
        return date(today.year + 1, birth_date.month, birth_date.day)
    return this_year_birthday

def calculate_days_until(birth_date: date) -> int:
    next_birthday = get_next_birthday(birth_date)
    return (next_birthday - date.today()).days

def calculate_time_until(birth_date: date) -> Dict[str, int]:
    next_birthday = get_next_birthday(birth_date)
    delta = datetime.combine(next_birthday, datetime.min.time()) - datetime.now()
    total_seconds = int(delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}

def handle_message(message: Dict, bot_token: str, db_url: str):
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    text = message.get('text', '')
    
    if text == '/start':
        user_data = get_user_data(user_id, db_url)
        if user_data and user_data['birth_date']:
            show_main_menu(chat_id, user_data['user_name'], user_data['birth_date'], bot_token)
        else:
            send_message(chat_id, 
                '🎂 <b>Привет! Я бот обратного отсчёта до дня рождения</b>\n\n'
                'Давай начнём! Введи дату своего рождения в формате:\n'
                '<code>ДД.ММ.ГГГГ</code>\n\n'
                'Например: <code>15.05.1990</code>',
                bot_token)
    
    elif '.' in text and len(text.split('.')) == 3:
        try:
            day, month, year = text.split('.')
            birth_date = date(int(year), int(month), int(day))
            
            send_message(chat_id,
                f'Отлично! Дата рождения: <b>{birth_date.strftime("%d.%m.%Y")}</b>\n\n'
                'Теперь введи своё имя:',
                bot_token)
            
            save_user_data(user_id, '', birth_date.isoformat(), db_url)
        except:
            send_message(chat_id, '❌ Неверный формат даты. Попробуй ещё раз:\n<code>ДД.ММ.ГГГГ</code>', bot_token)
    
    else:
        user_data = get_user_data(user_id, db_url)
        if user_data and user_data['birth_date'] and not user_data['user_name']:
            save_user_data(user_id, text, user_data['birth_date'].isoformat(), db_url, chat_id)
            show_confirmation(chat_id, text, user_data['birth_date'], bot_token)

def show_confirmation(chat_id: int, user_name: str, birth_date: date, bot_token: str):
    keyboard = {
        'inline_keyboard': [
            [{'text': '✅ Готово', 'callback_data': 'confirm'}]
        ]
    }
    send_message(chat_id,
        f'👤 <b>Имя:</b> {user_name}\n'
        f'📅 <b>Дата рождения:</b> {birth_date.strftime("%d.%m.%Y")}\n\n'
        'Всё верно?',
        bot_token, keyboard)

def show_main_menu(chat_id: int, user_name: str, birth_date: date, bot_token: str):
    days_until = calculate_days_until(birth_date)
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '⏱ Реальное время', 'callback_data': 'realtime'}],
            [{'text': '📆 Просто дата', 'callback_data': 'simple'}],
            [{'text': '🔄 Сбросить', 'callback_data': 'reset'}]
        ]
    }
    
    send_message(chat_id,
        f'👋 Привет, <b>{user_name}</b>!\n\n'
        f'🎂 До твоего дня рождения:\n'
        f'<b>{days_until} дней</b>',
        bot_token, keyboard)

def handle_callback(callback: Dict, bot_token: str, db_url: str):
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    user_id = callback['from']['id']
    data = callback['data']
    
    user_data = get_user_data(user_id, db_url)
    
    if data == 'confirm':
        answer_callback(callback['id'], bot_token)
        if user_data:
            show_main_menu(chat_id, user_data['user_name'], user_data['birth_date'], bot_token)
    
    elif data == 'realtime':
        if user_data:
            save_realtime_message(user_id, chat_id, message_id, db_url)
            time_data = calculate_time_until(user_data['birth_date'])
            keyboard = {
                'inline_keyboard': [
                    [{'text': '❌ Остановить', 'callback_data': 'stop_realtime'}]
                ]
            }
            edit_message(chat_id, message_id,
                f'⏱ <b>РЕАЛЬНОЕ ВРЕМЯ</b>\n'
                f'<i>Обновляется автоматически каждые 5 секунд</i>\n\n'
                f'📅 <b>{time_data["days"]}</b> дней\n'
                f'⏰ <b>{time_data["hours"]}</b> часов\n'
                f'⏱ <b>{time_data["minutes"]}</b> минут\n'
                f'⏲ <b>{time_data["seconds"]}</b> секунд',
                bot_token, keyboard)
        answer_callback(callback['id'], bot_token)
    
    elif data == 'stop_realtime':
        delete_realtime_message(user_id, db_url)
        if user_data:
            show_main_menu(chat_id, user_data['user_name'], user_data['birth_date'], bot_token)
        answer_callback(callback['id'], bot_token, '⏸ Остановлено')
    
    elif data == 'simple':
        if user_data:
            days_until = calculate_days_until(user_data['birth_date'])
            next_bd = get_next_birthday(user_data['birth_date'])
            keyboard = {
                'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back'}]]
            }
            edit_message(chat_id, message_id,
                f'📆 <b>До дня рождения:</b>\n\n'
                f'🎂 <b>{days_until} дней</b>\n'
                f'📅 Дата: {next_bd.strftime("%d.%m.%Y")}',
                bot_token, keyboard)
        answer_callback(callback['id'], bot_token)
    
    elif data == 'reset':
        delete_user_data(user_id, db_url)
        edit_message(chat_id, message_id,
            '🔄 Данные сброшены!\n\n'
            'Введи дату рождения в формате:\n'
            '<code>ДД.ММ.ГГГГ</code>',
            bot_token)
        answer_callback(callback['id'], bot_token, '✅ Сброшено')
    
    elif data == 'back':
        if user_data:
            show_main_menu(chat_id, user_data['user_name'], user_data['birth_date'], bot_token)
        answer_callback(callback['id'], bot_token)