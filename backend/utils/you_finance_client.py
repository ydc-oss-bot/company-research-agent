import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class YouFinanceResearchClient:
    """Async client for the You.com Finance Research API."""

    def __init__(self, api_key: str, base_url: str = "https://api.you.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, research_effort: str = "deep") -> Dict[str, Any]:
        """Call the You.com Finance Research API.

        Args:
            query: The financial research question.
            research_effort: "deep" or "exhaustive". Defaults to "deep".

        Returns:
            The JSON response from the API.
        """
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "input": query,
            "research_effort": research_effort,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/finance_research",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"You.com finance research response for query '{query}': {len(data.get('output', {}).get('content', ''))} chars")
            return data

    def to_documents(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Convert a You.com Finance Research response into the standard document dict.

        The returned dict is keyed by URL so it can be merged with other search results.
        """
        docs: Dict[str, Any] = {}
        output = result.get("output", {})
        content = output.get("content", "")
        sources = output.get("sources", [])

        if content:
            # Use a synthetic URL for the synthesized answer so it can be merged.
            synthesis_url = f"you-finance://synthesis/{hash(query) & 0xFFFFFFFF}"
            docs[synthesis_url] = {
                "title": "Finance Research Summary",
                "content": content,
                "query": query,
                "url": synthesis_url,
                "source": "you_finance",
                "score": 0.95,
            }

        for source in sources:
            url = source.get("url")
            if not url or url in docs:
                continue
            snippets = source.get("snippets", [])
            docs[url] = {
                "title": source.get("title", ""),
                "content": "\n\n".join(snippets) if snippets else "",
                "query": query,
                "url": url,
                "source": "you_finance",
                "score": 0.9,
            }

        return docs
