from fastapi import FastAPI, Request
from supabase import create_client, Client
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
import openai
import requests
from fastapi.middleware.cors import CORSMiddleware
from newspaper import Article
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
import json
import re
import numpy as np
import nltk
import trafilatura
from pydantic import BaseModel
nltk.download('punkt')
nltk.download("punkt_tab")

### langchain imports and variables ###
''' Antiquated imports, kept for reference
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents.base import Document
'''
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

### starting app ###
@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(process_articles_loop())
    task2 = asyncio.create_task(ingest_loop())
    yield
    task1.cancel()
    task2.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Loading environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
embedder = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_api_key
)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
### supabase variables ###
SUPABASE_URL =  os.getenv("SUPABASE_URL")
SUPABASE_KEY =  os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

### initialising langchain for keyword extraction ###
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)
prompt = PromptTemplate(
    input_variables=["text"],
    template=(
        "Extract 5 diverse and high-level keywords from the following article text. "
        "Avoid duplicates or overly generic terms. Return them as a comma-separated list.\n\n"
        "Text: {text}\n\nKeywords:"
    )
)

keyword_chain = prompt | llm | StrOutputParser()



###root endpoint
@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}

#article ingestion endpoint
@app.post("/ingest")
async def ingest_url(request: Request):
    print("/ingest endpoint was triggered")
    data = await request.json()
    raw_url = data.get("url")
    print(f"Received URL: {raw_url}")

    if not raw_url:
        return {"status": "error", "message": "URL missing"}

    norm_url = normalise_url(raw_url)

    try:
        supabase.table("articles").insert({
            "url": norm_url,
            "status": "pending"
        }).execute()
        print(f"Inserted into Supabase: {norm_url}")
        return {"status": "queued", "url": norm_url}
    except Exception as e:
        print(f"URL already exists or insert failed: {e}")
        return {"status": "skipped", "error": str(e)}

###for frontend search queries against notes & articles tables###
class SearchRequest(BaseModel):
    query: str

@app.post("/search")
def search_all(payload: SearchRequest):
    query_embedding = embed_text(payload.query)
    try:
        results = supabase.rpc("match_vectors", {"query_embedding": query_embedding}).execute()
        print("Supabase RPC raw response:", results)
        print("RPC data:", results.data)
        matches = results.data
        enriched = []
        for item in matches:
            if item.get("source") == "articles":
                article_id = item.get("record_id") or item.get("id")  
                content_query = (
                    supabase.table("articles")
                    .select("content_cleaned")
                    .eq("id", article_id)
                    .maybe_single()
                    .execute()
                )
                item["content_cleaned"] = content_query.data["content_cleaned"] if content_query.data else None
            enriched.append(item)
        return {"results": enriched}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Search error:", str(e))
        return {"error": "Search failed: {str(e)}"}

#newspaper URL processing function
def process_url(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError("Failed to fetch URL")

    result = trafilatura.extract(downloaded, with_metadata=True, output_format="json")
    if not result:
        raise ValueError("Extraction failed")

    data = json.loads(result)
    return data["text"], {
        "title": data.get("title"),
        "authors": [data.get("author")] if data.get("author") else [],
        "publish_date": data.get("date") or str(datetime.now()),
        "url": url
    }


### url normalisation function ###
def normalise_url(raw_url):
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query)
    filtered_query = {k: v for k, v in query.items() if not k.startswith('utm_')}
    clean_query = urlencode(filtered_query, doseq=True)
    normalised = parsed._replace(query=clean_query, fragment='')
    path = normalised.path.rstrip('/')
    return urlunparse(normalised._replace(path=path))

### cleaning article content ###
def clean_article_text(raw_text):
    
    cleaned = raw_text.strip()
    
    # Remove common ad/boilerplate markers (case-insensitive)
    cleaned = re.sub(r"(?im)^(Advertisement|Sponsored Content|Sponsored)\b.*\n?", "", cleaned)
    
    # Remove lines that likely belong to footers, typically with phrases like "Follow us on", "Subscribe", or copyright notices.
    footer_patterns = [r"Follow us on", r"Subscribe to", r"© \d{4}", r"All Rights Reserved"]
    for pattern in footer_patterns:
        parts = re.split(pattern, cleaned, flags=re.IGNORECASE)
        if len(parts) > 1:
            cleaned = parts[0]
    
    # Remove excessive newlines and spaces
    cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)
    
    return cleaned


### article processing function ###
def process_article(url):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError("Failed to fetch URL")

    result = trafilatura.extract(downloaded, with_metadata=True, output_format="json")
    if not result:
        raise ValueError("Extraction failed")

    data = json.loads(result)
    content_raw = data["text"]
    content_cleaned = clean_article_text(content_raw)

    metadata = {
        "title": data.get("title"),
        "authors": [data.get("author")] if data.get("author") else [],
        "publish_date": data.get("date") or str(datetime.now()),
        "url": url
    }

    return content_raw, content_cleaned, metadata

### using LLM chain to extract keywords from article content ###
def extract_keywords_with_langchain(text):
    try:
        return keyword_chain.invoke({"text": text}).strip()
    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return ""

    
async def process_articles_loop(poll_every=15):
    ###Polls for pending articles in the 'articles' table, processes each article with
    ###newspaper3k (including advanced cleaning), uses LangChain to extract keywords, and
    ###updates the record in Supabase with the extracted content, metadata, and a 'processed'
    ###status. Errors update the status to 'error'.
    
    while True:
        # Fetch one pending article record
        res = supabase.table("articles").select("*").eq("status", "pending").limit(1).execute()
        if res.data:
            entry = res.data[0]
            article_id = entry["id"]
            raw_url = entry["url"]
            norm_url = normalise_url(raw_url)
            print(f"Processing URL: {norm_url}")
            
            try:
                # Process the article via newspaper3k
                # Process raw and cleaned content
                content_raw, content_cleaned, metadata = process_article(norm_url)

                # Split cleaned content into chunks
                print("Splitter class:", type(splitter))
                ############# DEBUGGING PRINT AHHHHHHHHHHHH
                ### chunking content with RecursiveCharacterTextSplitter
                docs = splitter.split_documents([
                    Document(page_content=content_cleaned, metadata={"article_id": article_id})
                ])
                #loop through chunks and embed them
                chunk_vectors = []
                for i, doc in enumerate(docs):
                    try:
                        vector = embedder.embed_query(doc.page_content)
                        chunk_vectors.append(vector)

                        supabase.table("article_chunks").insert({
                            "article_id": article_id,
                            "chunk_index": i,
                            "chunk_text": doc.page_content,
                            "embedding": vector,
                            "metadata": doc.metadata
                        }).execute()
                        print(f"Stored chunk {i}")
                    except Exception as e:
                        print(f"Embedding failed on chunk {i}: {e}")
                if chunk_vectors:
                    article_vector = np.mean(chunk_vectors, axis=0).tolist()
                    supabase.table("articles").update({
                        "article_embedding": article_vector
                    }).eq("id", article_id).execute()

                # Use LangChain to extract keywords from the cleaned content
                keywords = extract_keywords_with_langchain(content_cleaned)
                metadata["keywords"] = keywords
                
                # Prepare the update payload; JSON-serialize metadata as needed for Postgres JSONB
                update_data = {
                    "title": metadata.get("title"),
                    "content_raw": content_raw,
                    "content_cleaned": content_cleaned,
                    "published_at": metadata.get("publish_date"),
                    "metadata": json.dumps(metadata),
                    "status": "processed"
                }
                print("Update payload:", json.dumps(update_data, indent=2))

                # Update the Supabase record accordingly
                supabase.table("articles").update(update_data).eq("id", article_id).execute()
                print(f"Successfully processed: {metadata.get('title')}")
            except Exception as e:
                print(f"Failed processing URL {norm_url}: {e}")
                supabase.table("articles").update({
                    "status": "error",
                    "error_message": str(e)
                }).eq("id", article_id).execute()
        else:
            print("No pending URLs found. Waiting...")
        await asyncio.sleep(poll_every)
    

### Async Supabase Polling ###
async def ingest_loop(poll_every=15):
    while True:
        # Pull next queued article
        res = supabase.table("articles").select("*").eq("status", "pending").limit(1).execute()
        if res.data:
            entry = res.data[0]
            article_id = entry["id"]
            raw_url = entry["url"]
            norm_url = normalise_url(raw_url)
            print(f"🔍 Processing: {norm_url}")

            try:
                content, metadata = process_url(norm_url)
                supabase.table("articles").update({
                    "status": "processed",
                    "metadata": metadata
                }).eq("id", article_id).execute()
                print(f"Finished: {metadata['title']}")
            except Exception as e:
                print(f"Error with {norm_url}: {e}")
                supabase.table("articles").update({
                    "status": "error"
                }).eq("id", article_id).execute()
        else:
            print("No queued URLs. Waiting...")

        await asyncio.sleep(poll_every)

#plain text input function
def read_root():
            try:
                result = supabase.table("notes").select("*").limit(1).execute()
                return {"message": "Connected to Supabase", "sample": result.data}
            except Exception as e:
                return {"error": str(e)}

### OpenAI embedding text function ###
def embed_text(text):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

### Store text and it's embedding in Supabase ###
def store_note(text):
    embedding = embed_text(text)  # Generate embedding
    data = {"text": text, "embedding": embedding}

    response = supabase.table("notes").insert(data).execute()
    return response

### Retrieve stored article IDs from Supabase ###
def fetch_stored_articles():
    try:
        response = supabase.table("articles").select("source_id").execute()
        if response.data:
            return {entry["source_id"] for entry in response.data if entry.get("source_id")}
        else:
            return set()
    except Exception as e:
        print("Error fetching stored article source_ids:", e)
        return set()

response = supabase.table("articles").select("id").execute()
print("Supabase Response:", response)

#call & loop manual text input on cli (redundant)
#if __name__ == "__main__":
#    while True:
#        text = input("Enter a note (or type 'exit' to stop): ")
#        if text.lower() == "exit":
#            break
#        response = store_note(text)
#        print("Note uploaded:", response)

### RAG Layer ###
class RAGRequest(BaseModel):
    query: str

@app.post("/rag")
async def rag_handler(request: RAGRequest):
    print("RAG endpoint received a request.")
    print(f"Query: '{request.query}'")
    """
    Handles a RAG request by retrieving relevant context and generating a response.
    """
    # 1. Embed the user's query
    query_embedding = embedder.embed_query(request.query)

    # 2. Retrieve relevant article chunks from Supabase
    try:
        match_response = supabase.rpc(
            "match_article_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.3,
                "match_count": 5,
            },
        ).execute()

        retrieved_chunks = match_response.data
        context_text = "\n\n---\n\n".join([chunk['chunk_text'] for chunk in retrieved_chunks])

    except Exception as e:
        print(f"Error retrieving from Supabase: {e}")
        return {"error": "Failed to retrieve relevant documents."}

    # 3. Formulate the prompt for the LLM
    prompt_template = """
    You are a helpful AI assistant. Based on the following context, please answer the user's question.
    If the context does not contain the answer, say so.

    Context:
    {context}

    Question:
    {question}
    """
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template,
    )

    # 4. Set up the LangChain chain with GPT-4 Turbo
    rag_llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.2, openai_api_key=openai_api_key)
    rag_chain = prompt | rag_llm | StrOutputParser()

    # 5. Invoke the chain to get the answer
    try:
        answer = rag_chain.invoke({"context": context_text, "question": request.query})
        return {"answer": answer, "retrieved_chunks": retrieved_chunks}
    except Exception as e:
        print(f"Error generating response from LLM: {e}")
        return {"error": "Failed to generate a response."}