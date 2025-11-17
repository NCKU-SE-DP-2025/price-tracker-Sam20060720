# External imports
from openai import OpenAI
import json
import requests
from bs4 import BeautifulSoup

class AIUtility:
    """Utility wrapper around OpenAI calls used in this app."""

    def __init__(self, api_key: str = "xxx"):
        self.client = OpenAI(api_key=api_key)

    def evaluate_relevance(self, title: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": title},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return response.choices[0].message.content

    def extract_keywords(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
            },
            {"role": "user", "content": prompt},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return response.choices[0].message.content

    def summarize_news(self, content: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
            },
            {"role": "user", "content": content},
        ]
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        return json.loads(response.choices[0].message.content)

class ScrapingUtility:
    """Utility for HTTP fetching and HTML parsing of news articles."""

    @staticmethod
    def fetch_and_parse_article(url: str):
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.find("h1", class_="article-content__title").text
        time = soup.find("time", class_="article-content__time").text
        content_section = soup.find("section", class_="article-content__editor")
        paragraphs = [
            p.text
            for p in content_section.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]
        return title, time, paragraphs
