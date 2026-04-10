from typing import Any

import openai
from tenacity import stop_after_attempt, retry, wait_exponential, retry_if_exception_type

from app_v1.commons.concurrency_controller import AsyncConcurrencyController
from app_v1.config.config_keys import CALL_LLM_MAX_CONCURRENT_CALLS, CALL_LLM_RETRY_COUNT, \
    CALL_LLM_INSTRUCTOR_RETRY_COUNT
from app_v1.config.config_loader import fetch_key_value
from app_v1.llm.llm_model.base_llm_model import LLMModel


#TODO: should be config driven
concurrent_llm_calls = fetch_key_value(CALL_LLM_MAX_CONCURRENT_CALLS, int)
llm_call_concurrency_controller = AsyncConcurrencyController(concurrent_llm_calls)

@llm_call_concurrency_controller.limit_concurrency
async def call_llm_with_retry(
        client:Any,
        llm_model:LLMModel,
        response_model:Any,
        messages:list,
        agent_name:str,
        method_name:str
) -> Any:
    retry_count = fetch_key_value(CALL_LLM_RETRY_COUNT, int)
    total_attempts = retry_count + 1
    instructor_retry_count = fetch_key_value(CALL_LLM_INSTRUCTOR_RETRY_COUNT, int)

    #TODO: add more constraints on retry
    @retry(retry = retry_if_exception_type(openai.RateLimitError),
           stop = stop_after_attempt(total_attempts),
           wait = wait_exponential(multiplier=1, min=1, max=60),
           reraise=True)
    async def _call_llm():
        try:
            return await client.chat.completions.create(
                model=llm_model.get_model_name(),
                response_model=response_model,
                messages=messages,
                max_retries=instructor_retry_count # retries by instructor library on wrong llm output
            )
        except Exception as e:
            raise

    parsed_output = await _call_llm()
    return parsed_output
