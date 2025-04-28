# Generator_post_tg_gpt
Telegram Post Generator
This is a FastAPI-based application designed to generate blog posts or social media content automatically based on a given topic. It fetches recent news using the Currents API and generates engaging articles with titles, meta descriptions, and detailed content using OpenAI's GPT-4o-mini model. The generated content can be used for posting on platforms like Telegram.
Features

Fetch recent news articles based on a specified topic.
Generate SEO-friendly article titles and meta descriptions.
Create detailed, structured articles (1500+ characters) with clear subheadings, trends analysis, and examples from recent news.
REST API endpoints for generating posts and checking service status.
Configurable via environment variables for API keys and port.

Prerequisites

Python 3.8+
API keys for:
OpenAI (for GPT-4o-mini)
Currents API (for news fetching)


Git (optional, for cloning the repository)

Installation

Clone the repository:
git clone https://github.com/your-username/your-repository.git
cd your-repository


Set up a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install dependencies:
pip install -r requirements.txt


Set up environment variables:Create a .env file in the root directory or export the variables directly:
export OPENAI_API_KEY="your-openai-api-key"
export CURRENTS_API_KEY="your-currents-api-key"
export PORT=8000  # Optional, defaults to 8000

Alternatively, add these to a .env file:
OPENAI_API_KEY=your-openai-api-key
CURRENTS_API_KEY=your-currents-api-key
PORT=8000


Run the application:
python app.py

The API will be available at http://localhost:8000.


Usage
API Endpoints

GET /: Check if the service is running.
Response: {"message": "Service is running"}


GET /heartbeat: Check the service status.
Response: {"status": "OK"}


POST /generate-post: Generate a post based on a topic.
Request body:{
  "topic": "artificial intelligence"
}


Response:{
  "title": "The Future of AI: Trends and Innovations",
  "meta_description": "Explore the latest advancements in artificial intelligence, including recent breakthroughs and their impact on industries.",
  "post_content": "Detailed article content here..."
}





Example Request
Use curl or a tool like Postman to test the API:
curl -X POST http://localhost:8000/generate-post -H "Content-Type: application/json" -d '{"topic": "artificial intelligence"}'

Integration with Telegram
To use the generated content in Telegram:

Set up a Telegram bot using BotFather to get a bot token.
Integrate the API with a Telegram bot framework (e.g., python-telegram-bot).
Call the /generate-post endpoint to fetch content and send it to a Telegram channel or chat using the bot.

Project Structure
your-repository/
│
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── .env                # Environment variables (not tracked in Git)

Dependencies
See requirements.txt for the full list of dependencies.
Contributing

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes and commit (`git commit -m "Add feature

