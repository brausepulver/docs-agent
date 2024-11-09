from dotenv import load_dotenv
load_dotenv()
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from utils.docs import create_service, add_comment

Settings.embed_model = NVIDIAEmbedding(model="nvidia/nv-embed-v1")

# documents = SimpleDirectoryReader("data").load_data()
# index = VectorStoreIndex.from_documents(documents, show_progress=True)
# query_engine = index.as_query_engine()
# response = query_engine.query("What are the main contributions?")
# print(response)

def main():
    try:
        service = create_service()
    except Exception as e:
        print(f"Error creating docs service: {e}")
        return

    add_comment(service, '1kJOP9HEj3uqgxJq0AW6TD8QQ1-1uFBzjf8OdtHXgsZQ', 'Test')

if __name__ == "__main__":
    main()
