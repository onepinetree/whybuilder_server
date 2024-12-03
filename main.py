from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from openai import OpenAI
import time
from api_info import API_KEY, whybuilder_assistant_id
import asyncio
import os
from starlette import status

app = FastAPI()
client = OpenAI(api_key = API_KEY)
assistant_id = whybuilder_assistant_id





@app.get("/get_new_threadId")
async def makeThreadId() -> dict:
    '''클라이언트가 요청하면 새로운 쓰레드 아이디를 return 하는 함수'''

    max_try = 3
    current_try = 0

    while True:
        try:
            empty_thread = await asyncio.to_thread(client.beta.threads.create)
            return { 'new_threadId' : empty_thread.id }
        
        except Exception as e:
            if current_try<max_try :
                current_try += 1
                continue
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f'The thread has not been created due to Internal Server Error, {e}'
                )








def createMessageInThread(threadId: str, role: str, content: str):
    client.beta.threads.messages.create(thread_id=threadId,
                                        role=role,
                                        content=content)


def createRun(thread_id: str, assistant_id: str ):
    return client.beta.threads.runs.create(thread_id = thread_id,
                                     assistant_id = assistant_id)


def retrieveRun(thread_id : str, run_id : str):
    return client.beta.threads.runs.retrieve(thread_id = thread_id,
                                        run_id = run_id)




class MessageModel(BaseModel):
    thread_id : str
    new_user_message : str


@app.post("/get_whybuilder_message")
def getWhyBuilderMessage(model: MessageModel)-> dict:
    '''클라이언트가 threadId와 유저프롬프트를 보내면 gpt프롬프트를 return 하는 함수 '''
    thread_id = model.thread_id
    user_prompt = model.new_user_message

    try: 
        createMessageInThread(
        threadId=thread_id,
        role="user",
        content=user_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail=f'Invalid ThreadId, {e}')
    
    try: 
        run = createRun(thread_id = thread_id,
                        assistant_id = whybuilder_assistant_id)
        run_id = run.id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail=f'Run Failed due to Internal Server Error, {e}')

    while True:
        try:
            retrieve_run = retrieveRun(thread_id = thread_id,
                                        run_id = run_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 description = f'Retrieving run failed due to Internal Server Error, {e}')
        
        if(retrieve_run.status == 'completed'):
            thread_messages = client.beta.threads.messages.list(thread_id)
            whybuilder_message = thread_messages.data[0].content[0].text.value
            return {'whybuilder_message' : whybuilder_message }
        
        elif(retrieve_run.status in ['queued', 'in_progress']):
            time.sleep(0.5)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 description = f'Run was finished with unexpected status, {Exception}')


#로컬환경 설정
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))











