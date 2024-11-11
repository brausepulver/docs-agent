from sqlalchemy import make_url
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, ExactMatchFilter
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from .db import DATABASE_URL

Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embed-v1")

url = make_url(DATABASE_URL)

gdrive_vector_store = PGVectorStore.from_params(
    database=url.database,
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="embeddings_google_drive",
    embed_dim=4096,
)
gdrive_storage_context = StorageContext.from_defaults(vector_store=gdrive_vector_store)

gh_vector_store = PGVectorStore.from_params(
    database=url.database,
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="embeddings_github",
    embed_dim=4096,
)
gh_storage_context = StorageContext.from_defaults(vector_store=gh_vector_store)

async def get_relevant_chunks(vector_store, not_doc_id: str, query: str, num_chunks: int = 3):
    try:
        index = VectorStoreIndex.from_vector_store(vector_store)
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="google_doc_id",
                    value=not_doc_id,
                    operator="!="
                )
            ]
        )
        retriever = index.as_retriever(similarity_top_k=num_chunks, filters=filters)
        return await retriever.aretrieve(query)
    except Exception as e:
        print(f"Error retrieving chunks: {e}")
        raise
