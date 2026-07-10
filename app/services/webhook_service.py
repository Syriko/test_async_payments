import httpx
from app.core.config import settings
from app.schemas.payment import WebhookPayload
import asyncio


async def send_webhook(
        webhook_url: str,
        payload: WebhookPayload,
        retry_count: int = 0
):
    max_retries = settings.WEBHOOK_RETRY_COUNT
    timeout = settings.WEBHOOK_TIMEOUT

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload.model_dump(mode='json'),
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                print(f'[INFO] Webhook sent successfully | url: {webhook_url}')
                return True

        except httpx.TimeoutException:
            print(
                f'[Error] Webhook timeout | url: {webhook_url}, attempt {attempt + 1}/{max_retries}'
            )
        except httpx.HTTPStatusError as ex:
            print(
                f'[Error] Webhook send error {ex.response.status_code} | url: {webhook_url}, '
                f'attempt {attempt + 1}/{max_retries}'
            )
        except Exception as ex:
            print(f'[Error] Webhook error {webhook_url}: {ex}')

        # Возрастающая задержка перед повторной попыткой
        if attempt < max_retries - 1:
            delay = 2 ** attempt  # 1, 2, 4 секунды
            await asyncio.sleep(delay)

    print(f'[Error] Webhook failed after {max_retries} attempts to {webhook_url}')
    return False











