
import logging
from openai import OpenAI
from common.config_manager import get_global_config
from utils.logger import Logger

config = get_global_config()
logger = Logger.create_logger('app', 'lang_tools.log', logging.INFO)



api_key = config.get('openai.api_key')
api_base_url = config.get('openai.api_url')

logger.info(f"api_key: {api_key}")
logger.info(f"api_base_url: {api_base_url}")

client = OpenAI(
  base_url=api_base_url,
  api_key=api_key,
)

completion = client.chat.completions.create(
#   extra_headers={
#     "HTTP-Referer": "https://www.langtools.com", # Optional. Site URL for rankings on openrouter.ai.
#     "X-Title": "Lang Tools", # Optional. Site title for rankings on openrouter.ai.
#   },
  model="openai/gpt-4o",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)

print(completion.choices[0].message.content)



