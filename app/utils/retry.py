import time
from openai import OpenAI, APIStatusError

def call_with_retry(client: OpenAI, **kwargs) -> dict:
    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except APIStatusError as e:
            if e.status_code != 429 or attempt == 2:
                raise
            time.sleep(2 ** attempt)
