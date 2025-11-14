CREATE TABLE IF NOT EXISTS t_p25838731_telegram_birthday_co.users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    birth_date DATE,
    user_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_user_id ON t_p25838731_telegram_birthday_co.users(user_id);