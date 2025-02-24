import os
import re
import time
from .openai_context import openai_client

def assistant_talk_request(search_type):
    assistant_id = os.environ["OPENAI_ASSISTANT_KEY"]
    
    with openai_client() as client:
        thread = client.beta.threads.create()
        
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=search_type,
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )
        
        request_id = [thread.id, run.id]
    
    return request_id

def assistant_talk_get(target_thread_id, target_run_id):
    timeout = 30
    start_time = time.time()
    
    with openai_client() as client:
        # Run 상태 확인 및 타임아웃 처리
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=target_thread_id, 
                run_id=target_run_id
            )
            if run.status == "completed":
                break
            elif run.status in ["failed", "error"]:
                raise Exception(f"Run failed with status: {run.status}")
            elif time.time() - start_time > timeout:
                raise TimeoutError("Run did not complete within the timeout period.")
            time.sleep(0.5)
        
        # 메시지 리스트 가져오기
        messages = client.beta.threads.messages.list(thread_id=target_thread_id)
        
        formatted_text = []
        
        # 메시지 필터링
        non_empty_messages = [m for m in messages if m.content and len(m.content) > 0]
        
        # 가장 먼저 온 메세지만 처리
        if len(non_empty_messages) > 0:
            first_message = non_empty_messages[0]
            if first_message.role == "assistant":
                raw_text = first_message.content[0].text.value
                if raw_text:
                    cleaned_text = re.sub(r'【.*?】', '', raw_text)
                    formatted_text.append(cleaned_text.replace('. ', '.\n'))
    
    formatted_text = "\n".join(formatted_text)
    
    return formatted_text