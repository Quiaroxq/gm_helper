from flask import Flask, render_template, request
import requests
import json
from bs4 import BeautifulSoup
import threading
import time
import uuid

app = Flask(__name__)

# Учетные данные для получения токена (замените на свои в SBER AI)
auth = "*******"
client_id = "******"
secret = "*******"
giga_token = ""
# Функция для получения токена
def get_token(auth_token, scope='GIGACHAT_API_PERS'):
    rq_uid = str(uuid.uuid4())
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }

    payload = {
        'scope': scope
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f'Ошибка: {str(e)}')
        return None
# Функция для обновления токена каждые 30 минут
def update_token():
    global giga_token
    # Инициализация токена при старте
    response = get_token(auth)
    if response and response.status_code == 200:
        giga_token = response.json()['access_token']
        print("Токен обновлен:")
    else:
        print("Не удалось обновить токен при старте.")

    while True:
        time.sleep(1800) 
        response = get_token(auth)
        if response and response.status_code == 200:
            giga_token = response.json()['access_token']
            print("Токен обновлен:", giga_token)
        else:
            print("Не удалось обновить токен.")

# Запускаем поток для обновления токена
token_thread = threading.Thread(target=update_token)
token_thread.daemon = True
token_thread.start()

# Загрузка html-шаблона
@app.route('/')
def index():
    return render_template('index.html')

# Обработка запроса на генерацию текста
@app.route('/generate_text', methods=['POST'])
def generate_text():
    user_message = request.form['user_message']
    chat_response = get_chat_completion(giga_token, user_message)
    
    if chat_response:
        answer_content = chat_response['choices'][0]['message']['content']
    else:
        answer_content = "Не удалось получить ответ."

    return render_template('index.html', answer=answer_content)


#Обработка запроса на генерацию изображения
@app.route('/generate_image', methods=['POST'])
def generate_image():
    user_message = request.form['image_message']
    chat_response = get_chat_image(giga_token, user_message) # сначала получаем расписанный промпт от текстового помощника

    if chat_response:
        answer_content = chat_response['choices'][0]['message']['content']
    else:
        answer_content = "Не удалось получить ответ."

    response_img_tag = send_chat_request(giga_token, answer_content) # а здесь полученный промпт просим изобразить

    if response_img_tag:
        soup = BeautifulSoup(response_img_tag, 'html.parser')
        img_src = soup.img['src']

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {giga_token}',
        }

        response = requests.get(f'https://gigachat.devices.sberbank.ru/api/v1/files/{img_src}/content', headers=headers, verify=False)

        with open('static/image.jpg', 'wb') as f:
            f.write(response.content)

        return render_template('index.html', image_generated=True)
    else:
        return render_template('index.html', image_generated=False)


# функция для отправки post запроса для генерации изображения
def send_chat_request(giga_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {giga_token}',
    }

    payload = {
        "model": "GigaChat:latest",
        "messages": [
            {
                "role": "system",
                "content": "Ты - Василий Кандинский"
            },
            {
                "role": "user",
                "content": f"Нарисуй {user_message}"
            }
        ],
        "function_call": "auto",
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        print(f"Произошла ошибка: {str(e)}")
        return None


# функция для отправки post запроса для ответа на вопросы по правилам 
def get_chat_completion(auth_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": f"Расскажи про правило Dungeouns and Dragons в котором говорится о том{user_message}"
            }
        ],
        "temperature": 1,
        "top_p": 0.1,
        "n": 1,
        "stream": False,
        "max_tokens": 512,
        "repetition_penalty": 1,
        "update_interval": 0
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response.json()
    except requests.RequestException as e:
        print(f"Произошла ошибка: {str(e)}")
        return None
    
# функция для отправки post запроса на генерацию промпта для изображения
def get_chat_image(auth_token, user_message):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": f"Опипши словами {user_message}, в пределах 40 слов"
            }
        ],
        "temperature": 1,
        "top_p": 0.1,
        "n": 1,
        "stream": False,
        "max_tokens": 512,
        "repetition_penalty": 1,
        "update_interval": 0
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response.json()
    except requests.RequestException as e:
        print(f"Произошла ошибка: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
