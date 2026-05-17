import asyncio
import json
import uuid
import sys
import os
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add current working directory to sys.path
sys.path.append(os.getcwd())

import httpx
from src.database import AsyncSessionLocal
from src.models import User, Document, DocumentChunk
from src.config import settings

async def create_embedding(text: str, retry_count: int = 5) -> list:
    """HuggingFace Inference API'sini direkt çağırarak embedding oluşturur."""
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    url = f"https://router.huggingface.co/hf-inference/models/{model_id}/pipeline/feature-extraction"
    
    api_key = os.environ.get('HUGGINGFACE_API_KEY') or settings.huggingface_api_key
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {"inputs": [text], "options": {"wait_for_model": True}}
    
    for attempt in range(retry_count):
        try:
            async with httpx.AsyncClient(verify=False) as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
                
                if resp.status_code == 503:
                    print(f"Model loading... (Attempt {attempt+1})")
                    await asyncio.sleep(15)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        except Exception as e:
            if attempt == retry_count - 1:
                raise e
            print(f"Embedding error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
    
    raise Exception("Embedding failed")

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
DATASET_DOC_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

async def init_system_user(db: AsyncSession):
    # Ensure system user exists
    result = await db.execute(select(User).where(User.id == SYSTEM_USER_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=SYSTEM_USER_ID,
            email="system@developlus.ai",
            username="system",
            hashed_password="system_no_login",
            full_name="System Knowledge Base"
        )
        db.add(user)
        await db.commit()
    return user

async def index_json_dataset(db: AsyncSession, filename: str, doc_name: str):
    path = Path("src/datasets") / filename
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    doc_id = uuid.uuid5(DATASET_DOC_ID, filename)
    
    print(f"Cleaning existing data for {filename}...")
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
    await db.execute(delete(Document).where(Document.id == doc_id))
    await db.commit()

    # Transactional update
    doc = Document(
        id=doc_id,
        user_id=SYSTEM_USER_ID,
        filename=filename,
        file_type="json",
        status="processing",
        doc_metadata={"source": doc_name}
    )
    db.add(doc)
    await db.flush() # Ensure doc is created in DB before chunks

    print(f"Indexing items from {filename}...")
    
    processed_count = 0
    chunks_to_add = []
    for i, item in enumerate(data):
        if "company_name" in item: # TSDS
            text_content = f"Company: {item.get('company_name')}\nIndustry: {item.get('industry')}\nDescription: {item.get('description')}\nStack: {json.dumps(item.get('stack_architecture'))}"
        else: # TDS
            intel = item.get("core_intel", {}) or {}
            criteria = item.get("matching_criteria", {}) or {}
            best_for = criteria.get("best_for", []) if isinstance(criteria, dict) else []
            tags = intel.get("tags", []) if isinstance(intel, dict) else []
            text_content = f"Tool: {item.get('display_name')} ({item.get('slug')})\nDescription: {intel.get('description')}\nBest For: {', '.join(best_for)}\nTags: {', '.join(tags)}"

        try:
            vector = await create_embedding(text_content)
            chunk = DocumentChunk(
                document_id=doc_id,
                user_id=SYSTEM_USER_ID,
                chunk_index=i,
                chunk_text=text_content,
                embedding=vector,
                token_count=len(text_content.split()),
                chunk_metadata={}
            )
            chunks_to_add.append(chunk)
            processed_count += 1
            
            if len(chunks_to_add) >= 5:
                db.add_all(chunks_to_add)
                await db.flush()
                chunks_to_add = []
                print(f"[{filename}] Processed {i+1}/{len(data)} items...")
        except Exception as e:
            print(f"Error embedding item {i} in {filename}: {e}")

    if chunks_to_add:
        db.add_all(chunks_to_add)

    # Update final status on the SAME object tracked in the SAME session
    doc.status = "ready"
    doc.chunk_count = processed_count
    await db.commit()
    print(f"Finished indexing {filename} ({processed_count} chunks)")

async def main():
    async with AsyncSessionLocal() as db:
        await init_system_user(db)
        await index_json_dataset(db, "tsds-final.json", "Tech Stack Dataset")
        await index_json_dataset(db, "tds-prefinal.json", "Technology Dataset")

if __name__ == "__main__":
    asyncio.run(main())
