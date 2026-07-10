"""
tools/web_search.py -> web search via Tavily

Requires TAVILY_API_KEY in the .env file
ref: https://tavily.com
"""

from langchain_tavily import TavilySearch

web_search = TavilySearch(
    max_results = 5,
    description = ( # NOTE: tool description
        "Cerca informazioni aggiornate sul web."
        "Usa questo tool quando hai bisogno di dati recenti, notizie"
        "o informazioi non presenti nella tua conoscenza di base"
    )
)
