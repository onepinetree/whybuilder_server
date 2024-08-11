from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
import os
from openai import OpenAI
import time
from api_info import API_KEY, whybuilder_assistant_id

app = FastAPI()
client = OpenAI(api_key = API_KEY)
assistant_id = whybuilder_assistant_id




@app.get("/get_new_threadId")
def makeThreadId() -> dict:
    '''클라이언트가 요청하면 새로운 쓰레드 아이디를 return 하는 함수'''
    empty_thread = client.beta.threads.create()
    return { 'new_threadId' : empty_thread.id }



class MessageModel(BaseModel):
    thread_id : str
    new_user_message : str


@app.post("/get_whybuilder_message")
def modifyLink(model: MessageModel)-> dict:
    '''클라이언트가 threadId와 유저프롬프트를 보내면 gpt프롬프트를 return 하는 함수 '''
    thread_id = model.thread_id
    user_prompt = model.new_user_message

    thread_message = client.beta.threads.messages.create(
    thread_id,
    role="user",
    content=user_prompt,
    )

    run = client.beta.threads.runs.create(
    thread_id = thread_id,
    assistant_id = assistant_id
    )
    run_id = run.id

    while True:
        retrieve_run = client.beta.threads.runs.retrieve(
        thread_id = thread_id,
        run_id = run_id
        )
        if(retrieve_run.status == 'completed'):
            thread_messages = client.beta.threads.messages.list(thread_id)
            whybuiler_message = thread_messages.data[0].content[0].text.value

            return {'whybuilder_message' : whybuiler_message }
        else:
            time.sleep(0.5)



#로컬환경 설정
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))











