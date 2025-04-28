import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests
from dotenv import load_dotenv
import uvicorn

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Инициализация FastAPI приложения
app = FastAPI(title="Blog Post Generator", description="API for generating blog posts based on recent news")

# Инициализация клиента OpenAI с API-ключом
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
currentsapi_key = os.getenv("CURRENTS_API_KEY")

# Проверка наличия API ключей
if not openai_client.api_key:
    logger.error("OPENAI_API_KEY is not set")
    raise ValueError("OPENAI_API_KEY environment variable must be set")
if not currentsapi_key:
    logger.error("CURRENTS_API_KEY is not set")
    raise ValueError("CURRENTS_API_KEY environment variable must be set")

# Модель данных для входящего запроса
class Topic(BaseModel):
    topic: str

# Функция для получения последних новостей
def get_recent_news(topic: str) -> str:
    logger.info(f"Fetching news for topic: {topic}")
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            logger.error(f"Currents API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Currents API error: {response.text}")
        
        news_data = response.json().get("news", [])
        if not news_data:
            logger.warning(f"No news found for topic: {topic}")
            return "No recent news found."
        
        news_titles = [article["title"] for article in news_data[:5]]
        logger.info(f"Found {len(news_titles)} news articles for topic: {topic}")
        return "\n".join(news_titles)
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

# Функция для генерации контента
def generate_content(topic: str) -> dict:
    logger.info(f"Generating content for topic: {topic}")
    recent_news = get_recent_news(topic)
    
    try:
        # Генерация заголовка
        title_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Create an engaging and accurate title for an article on '{topic}', "
                          f"considering recent news:\n{recent_news}. "
                          "The title should be interesting and clearly convey the topic."
            }],
            max_tokens=40,
            temperature=0.5,
            stop=["\n"]
        )
        title = title_response.choices[0].message.content.strip()
        if not title:
            logger.error("Empty title generated")
            raise HTTPException(status_code=500, detail="Failed to generate title: empty response")
        logger.info(f"Generated title: {title}")

        # Генерация мета-описания
        meta_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Write a meta description for an article titled '{title}'. "
                          "It should be informative, include key topic words, and be engaging."
            }],
            max_tokens=120,
            temperature=0.5,
            stop=["."]
        )
        meta_description = meta_response.choices[0].message.content.strip()
        if not meta_description:
            logger.error("Empty meta description generated")
            raise HTTPException(status_code=500, detail="Failed to generate meta description: empty response")
        logger.info(f"Generated meta description: {meta_description}")

        # Генерация контента
        content_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Write a detailed article on '{topic}' using recent news:\n{recent_news}. "
                          "The article must be:\n"
                          "1. Informative and logical\n"
                          "2. At least 1500 characters\n"
                          "3. Structured with subheadings\n"
                          "4. Include analysis of current trends\n"
                          "5. Have an introduction, main body, and conclusion\n"
                          "6. Include examples from recent news\n"
                          "7. Each paragraph should have at least 3-4 sentences\n"
                          "8. Be easy to read and insightful"
            }],
            max_tokens=1000,  # Уменьшено для скорости
            temperature=0.5,
            presence_penalty=0.6,
            frequency_penalty=0.6
        )
        post_content = content_response.choices[0].message.content.strip()
        if not post_content or len(post_content) < 1500:
            logger.error(f"Generated content too short: {len(post_content)} characters")
            raise HTTPException(status_code=500, detail="Generated content is too short or empty")
        logger.info(f"Generated article with {len(post_content)} characters")

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }
    
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during content generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/generate-post", summary="Generate a blog post based on a topic")
async def generate_post_api(topic: Topic):
    logger.info(f"Received request to generate post for topic: {topic.topic}")
    return generate_content(topic.topic)

@app.get("/", summary="Check if the service is running")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Service is running"}

@app.get("/heartbeat", summary="Check service health")
async def heartbeat_api():
    logger.info("Heartbeat endpoint accessed")
    return {"status": "OK"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
