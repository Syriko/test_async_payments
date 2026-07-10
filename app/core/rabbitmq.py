from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange, ExchangeType
from app.core.config import settings

broker = RabbitBroker(
    settings.RABBITMQ_URL
)

# Определяем обменники и очереди
PAYMENTS_EXCHANGE = RabbitExchange(
    name="payments.exchange",
    type=ExchangeType.DIRECT,
    durable=True
)

PAYMENTS_QUEUE = RabbitQueue(
    name="payments.queue",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.dlq",
        "x-message-ttl": 60000  # 60 секунд для повторных попыток
    }
)

PAYMENTS_DLQ = RabbitQueue(
    name="payments.dlq",
    durable=True
)

PAYMENTS_DLX = RabbitExchange(
    name="payments.dlx",
    type=ExchangeType.DIRECT,
    durable=True
)

PAYMENTS_RETRY_1S = RabbitQueue(
    name="payments.retry.1s",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payments.new",
        "x-message-ttl": 1000  # 1 секунда задержки
    }
)

PAYMENTS_RETRY_2S = RabbitQueue(
    name="payments.retry.2s",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payments.new",
        "x-message-ttl": 2000  # 2 секунды задержки
    }
)

PAYMENTS_RETRY_4S = RabbitQueue(
    name="payments.retry.4s",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.exchange",
        "x-dead-letter-routing-key": "payments.new",
        "x-message-ttl": 4000  # 4 секунды задержки
    }
)










