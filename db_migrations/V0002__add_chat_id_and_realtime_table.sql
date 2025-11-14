ALTER TABLE t_p25838731_telegram_birthday_co.users ADD COLUMN IF NOT EXISTS chat_id BIGINT;

CREATE TABLE IF NOT EXISTS t_p25838731_telegram_birthday_co.realtime_messages (
    user_id BIGINT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_realtime_user_id ON t_p25838731_telegram_birthday_co.realtime_messages(user_id);