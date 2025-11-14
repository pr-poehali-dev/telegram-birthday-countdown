import json
import os
import requests
import psycopg2
from datetime import datetime, date
from typing import Dict, Any, List

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Scheduler for auto-updating realtime messages and sending daily notifications
    Args: event with httpMethod (GET to trigger updates)
    Returns: HTTP response with update status
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method == 'GET':
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        db_url = os.environ.get('DATABASE_URL')
        
        if not bot_token or not db_url:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing configuration'})
            }
        
        query_params = event.get('queryStringParameters', {}) or {}
        action = query_params.get('action', 'update_realtime')
        
        if action == 'update_realtime':
            updated = update_realtime_messages(bot_token, db_url)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'updated': updated})
            }
        
        elif action == 'daily_notifications':
            sent = send_daily_notifications(bot_token, db_url)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'sent': sent})
            }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Method not allowed'})
    }

def get_next_birthday(birth_date: date) -> date:
    today = date.today()
    this_year_birthday = date(today.year, birth_date.month, birth_date.day)
    if this_year_birthday < today:
        return date(today.year + 1, birth_date.month, birth_date.day)
    return this_year_birthday

def calculate_time_until(birth_date: date) -> Dict[str, int]:
    next_birthday = get_next_birthday(birth_date)
    delta = datetime.combine(next_birthday, datetime.min.time()) - datetime.now()
    total_seconds = int(delta.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}

def is_birthday_today(birth_date: date) -> bool:
    today = date.today()
    return birth_date.month == today.month and birth_date.day == today.day

def get_all_realtime_messages(db_url: str) -> List[Dict]:
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

def get_all_users_for_notification(db_url: str) -> List[Dict]:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT user_id, chat_id, user_name, birth_date FROM t_p25838731_telegram_birthday_co.users WHERE chat_id IS NOT NULL")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{'user_id': r[0], 'chat_id': r[1], 'user_name': r[2], 'birth_date': r[3]} for r in rows]

def edit_message(chat_id: int, message_id: int, text: str, bot_token: str, reply_markup: Dict = None):
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def send_message(chat_id: int, text: str, bot_token: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def update_realtime_messages(bot_token: str, db_url: str) -> int:
    messages = get_all_realtime_messages(db_url)
    updated = 0
    
    for msg in messages:
        time_data = calculate_time_until(msg['birth_date'])
        keyboard = {
            'inline_keyboard': [
                [{'text': '❌ Остановить', 'callback_data': 'stop_realtime'}]
            ]
        }
        
        text = (
            f'⏱ <b>РЕАЛЬНОЕ ВРЕМЯ</b>\n'
            f'<i>Обновляется автоматически каждые 5 секунд</i>\n\n'
            f'📅 <b>{time_data["days"]}</b> дней\n'
            f'⏰ <b>{time_data["hours"]}</b> часов\n'
            f'⏱ <b>{time_data["minutes"]}</b> минут\n'
            f'⏲ <b>{time_data["seconds"]}</b> секунд'
        )
        
        edit_message(msg['chat_id'], msg['message_id'], text, bot_token, keyboard)
        updated += 1
    
    return updated

def send_daily_notifications(bot_token: str, db_url: str) -> int:
    users = get_all_users_for_notification(db_url)
    sent = 0
    
    for user in users:
        if is_birthday_today(user['birth_date']):
            text = (
                f'🎉🎂🎈 <b>С ДНЁМ РОЖДЕНИЯ, {user["user_name"]}!</b> 🎈🎂🎉\n\n'
                f'Поздравляю тебя с этим особенным днём!\n'
                f'Желаю счастья, здоровья и исполнения всех желаний! 🎁✨'
            )
            send_message(user['chat_id'], text, bot_token)
            sent += 1
        else:
            time_data = calculate_time_until(user['birth_date'])
            days = time_data['days']
            
            text = (
                f'⏰ <b>Доброе утро, {user["user_name"]}!</b>\n\n'
                f'🎂 До твоего дня рождения осталось:\n'
                f'<b>{days} {get_days_word(days)}</b>'
            )
            send_message(user['chat_id'], text, bot_token)
            sent += 1
    
    return sent

def get_days_word(days: int) -> str:
    if days % 10 == 1 and days % 100 != 11:
        return 'день'
    elif days % 10 in [2, 3, 4] and days % 100 not in [12, 13, 14]:
        return 'дня'
    else:
        return 'дней'
