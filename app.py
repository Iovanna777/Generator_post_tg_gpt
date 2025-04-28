import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests
from dotenv import load_dotenv
import uvicorn

# Настройка логирования для отслеживания работы приложения
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Инициализация FastAPI приложения
app = FastAPI(title="Blog Post Generator", description="API for generating blog posts based on recent news")

# Получение API ключей из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")

# Проверка наличия API ключей
if not openai.api_key:
    logger.error("OPENAI_API_KEY is not set")
    raise ValueError("OPENAI_API_KEY environment variable must be set")
if not currentsapi_key:
    logger.error("CURRENTS_API_KEY is not set")
    raise ValueError("CURRENTS_API_KEY environment variable must be set")

# Модель данных для входящего запроса с темой поста
class Topic(BaseModel):
    topic: str  # Тема, на основе которой будет генерироваться пост

# Функция для получения последних новостей по теме через Currents API
def get_recent_news(topic: str) -> str:
    """
    Fetches recent news articles for a given topic using Currents API.
    
    Args:
        topic (str): The topic to search for news articles.
    
    Returns:
        str: A string containing titles of up to 5 recent news articles, or a message if no news is found.
    
    Raises:
        HTTPException: If the API request fails.
    """
    logger.info(f"Fetching news for topic: {topic}")
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",  # Language of the news articles
        "keywords": topic,  # Keywords to filter news
        "apiKey": currentsapi_key  # API key for authentication
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
        
        # Extract titles of up to 5 news articles
        news_titles = [article["title"] for article in news_data[:5]]
        logger.info(f"Found {len(news_titles)} news articles for topic: {topic}")
        return "\n".join(news_titles)
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

# Функция для генерации контента поста с использованием новостей и OpenAI
def generate_content(topic: str) -> dict:
    """
    Generates a blog post (title, meta description, and content) based on a topic and recent news.
    
    Args:
        topic (str): The topic for the blog post.
    
    Returns:
        dict: A dictionary containing the title, meta description, and post content.
    
    Raises:
        HTTPException: If content generation fails.
    """
    logger.info(f"Generating content for topic: {topic}")
    
    # Fetch recent news to use as context
    recent_news = get_recent_news(topic)
    
    try:
        # Generate article title
        title_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Create an engaging and accurate title for an article on '{topic}', "
                          f"considering recent news:\n{recent_news}. "
                          "The title should be interesting and clearly convey the topic."
            }],
            max_tokens=60,
            temperature=0.5,
            stop=["\n"]
        )
        title = title_response.choices[0].message.content.strip()
        if not title:
            logger.error("Empty title generated")
            raise HTTPException(status_code=500, detail="Failed to generate title: empty response")
        logger.info(f"Generated title: {title}")

        # Generate meta description
        meta_response = openai.ChatCompletion.create(
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

        # Generate full article content
        content_response = openai.ChatCompletion.create(
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
            max_tokens=1500,
            temperature=0.5,
            presence_penalty=0.6,
            frequency_penalty=0.6
        )
        post_content = content_response.choices[0].message.content.strip()
        if not post_content or len(post_content) < 1500:
            logger.error(f"Generated content too short: {len(post_content)} characters")
            raise HTTPException(status_code=500, detail="Generated content is too short or empty")
        logger.info(f"Generated article with {len(post_content)} characters")

        # Return the generated content
        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }
    
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during content generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Эндпоинт для генерации поста
@app.post("/generate-post", summary="Generate a blog post based on a topic")
async def generate_post_api(topic: Topic):
    """
    API endpoint to generate a blog post based on the provided topic.
    
    Args:
        topic (Topic): A Pydantic model containing the topic string.
    
    Returns:
        dict: The generated title, meta description, and post content.
    
    Raises:
        HTTPException: If content generation fails.
    """
    logger.info(f"Received request to generate post for topic: {topic.topic}")
    return generate_content(topic.topic)

# Корневой эндпоинт для проверки работоспособности
@app.get("/", summary="Check if the service is running")
async def root():
    """
    Root endpoint to verify that the service is operational.
    
    Returns:
        dict: A message indicating the service status.
    """
    logger.info("Root endpoint accessed")
    return {"message": "Service is running"}

# Эндпоинт для проверки состояния сервиса
@app.get("/heartbeat", summary="Check service health")
async def heartbeat_api():
    """
    Heartbeat endpoint to check the health of the service.
    
    Returns:
        dict: A status indicating the service is operational.
    """
    logger.info("Heartbeat endpoint accessed")
    return {"status": "OK"}

# Запуск приложения
if __name__ == "__main__":
    """
    Main entry point to run the FastAPI application using Uvicorn.
    The port is configurable via the PORT environment variable (default: 8000).
    """
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
