"""Developlus API — Tavily Search Service"""
from typing import List, Dict, Any
from tavily import AsyncTavilyClient

from src.config import settings

# Initialize client using the key from config
tavily_client = AsyncTavilyClient(api_key=settings.tavily_api_key)

async def search_web(query: str, max_results: int = 3) -> str:
    """
    Tavily kullanarak internette arama yapar.
    RAG sistemi için metin formatında sonuç döner.
    """
    if not settings.tavily_api_key:
        return "Arama motoru aktif değil (API anahtarı eksik)."
        
    try:
        response = await tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_domains=["stackshare.io", "github.com", "reddit.com", "medium.com", "stackoverflow.com"]
        )
        
        results = response.get("results", [])
        if not results:
            return "Arama sonucu bulunamadı."
            
        formatted_results = []
        for i, res in enumerate(results):
            content = res.get("content", "")
            url = res.get("url", "")
            title = res.get("title", "")
            formatted_results.append(f"[{i+1}] BAŞLIK: {title}\nİÇERİK: {content}\nKAYNAK: {url}")
            
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Arama sırasında bir hata oluştu: {str(e)}"
