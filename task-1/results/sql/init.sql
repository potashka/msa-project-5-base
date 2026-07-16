CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    payment_status TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    paid_at TIMESTAMP
);

INSERT INTO users (user_id, email, full_name, city, created_at) VALUES
    (1, 'anna@example.local', 'Anna Petrova', 'Moscow', '2026-07-01 09:00:00'),
    (2, 'ivan@example.local', 'Ivan Sokolov', 'Saint Petersburg', '2026-07-01 10:15:00'),
    (3, 'maria@example.local', 'Maria Smirnova', 'Kazan', '2026-07-02 11:30:00'),
    (4, 'oleg@example.local', 'Oleg Volkov', 'Novosibirsk', '2026-07-03 15:45:00')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO orders (order_id, user_id, status, total_amount, created_at) VALUES
    (1001, 1, 'created', 1200.00, '2026-07-04 09:10:00'),
    (1002, 1, 'paid', 850.00, '2026-07-04 10:20:00'),
    (1003, 2, 'paid', 430.00, '2026-07-04 11:40:00'),
    (1004, 3, 'cancelled', 990.00, '2026-07-04 13:00:00'),
    (1005, 4, 'paid', 1220.00, '2026-07-05 14:30:00'),
    (1006, 2, 'paid', 560.00, '2026-07-05 16:10:00')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO payments (payment_id, order_id, payment_status, amount, paid_at) VALUES
    (5001, 1001, 'pending', 1200.00, NULL),
    (5002, 1002, 'paid', 850.00, '2026-07-04 10:25:00'),
    (5003, 1003, 'paid', 430.00, '2026-07-04 11:45:00'),
    (5004, 1004, 'refunded', 990.00, '2026-07-04 13:30:00'),
    (5005, 1005, 'paid', 1220.00, '2026-07-05 14:35:00'),
    (5006, 1006, 'paid', 560.00, '2026-07-05 16:15:00')
ON CONFLICT (payment_id) DO NOTHING;
