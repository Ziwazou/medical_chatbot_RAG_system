import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool

from src.prompt import system_prompt
from src.helper import get_embeddings

logger = logging.getLogger(__name__)


class MedicalChatbot:
    def __init__(self):
        load_dotenv()
        self.embeddings = get_embeddings()
        self.vectorstore = self._init_vectorstore()
        self.llm = self._init_llm()
        self.agent = self._init_agent()

    def _init_vectorstore(self):
        index_name = os.getenv("PINECONE_INDEX_NAME", "medical-chatbot")
        return PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings,
        )

    def _init_llm(self):
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        return ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3,
            timeout=60
        )

    def _init_agent(self):
        vectorstore = self.vectorstore

        @tool(
            response_format="content_and_artifact",
            description="Retrieve relevant medical context from the vector database."
        )
        def retrieve_medical_context(query: str):
            """Retrieve medical documents matching the user query."""
            if not vectorstore:
                return "Knowledge base is unavailable.", []

            docs = vectorstore.similarity_search(query, k=3)
            if not docs:
                return "No relevant medical documents found.", []

            serialized = "\n\n".join(
                f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}"
                for doc in docs
            )
            return serialized, docs

        return create_agent(
            self.llm,
            tools=[retrieve_medical_context],
            system_prompt=system_prompt
        )

    @staticmethod
    def _extract_text_content(content):
        if content is None:
            return None
        if isinstance(content, str):
            text = content.strip()
            return text if text else None
        if isinstance(content, dict):
            if content.get("type") == "text":
                text = content.get("text", "").strip()
                return text if text else None
            for key in ("content", "text", "value"):
                if key in content:
                    return MedicalChatbot._extract_text_content(content[key])
            return None
        if isinstance(content, list):
            parts = [MedicalChatbot._extract_text_content(item) for item in content]
            parts = [p for p in parts if p]
            return "\n\n".join(parts) if parts else None
        return None

    def get_response(self, user_message: str) -> str:
        if not user_message or not user_message.strip():
            return "Please provide a valid question."

        try:
            final_response = None
            for event in self.agent.stream(
                {"messages": [{"role": "user", "content": user_message}]},
                stream_mode="values"
            ):
                messages = event.get("messages", [])
                if not messages:
                    continue

                last_message = messages[-1]
                msg_type = getattr(last_message, 'type', None)
                if not msg_type and isinstance(last_message, dict):
                    msg_type = last_message.get('type') or last_message.get('role')

                raw_content = getattr(last_message, 'content', None)
                if raw_content is None and isinstance(last_message, dict):
                    raw_content = last_message.get('content')

                text = self._extract_text_content(raw_content)

                is_ai = msg_type in ('ai', 'assistant')
                if not is_ai and hasattr(last_message, '__class__'):
                    if 'aimessage' in last_message.__class__.__name__.lower():
                        is_ai = True

                if is_ai and text:
                    final_response = text

            if final_response:
                return final_response

            return "No response could be generated. Please try rephrasing your question."

        except TimeoutError:
            return "The request timed out. Please try again with a shorter query."
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "An error occurred while processing your request. Please try again later."

    def get_relevant_sources(self, query: str, k: int = 3) -> List[Dict]:
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            return [
                {
                    'source': doc.metadata.get('source', 'Unknown'),
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"Error retrieving sources: {e}")
            return []


_chatbot_instance = None


def get_chatbot() -> MedicalChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = MedicalChatbot()
    return _chatbot_instance
