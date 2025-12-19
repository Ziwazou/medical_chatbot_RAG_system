import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalChatbot: 
    def __init__(self):
        load_dotenv()
        
        self.embeddings = self._initialize_embeddings()
        
        self.vectorstore = self._initialize_vectorstore()
        
        self.llm = self._initialize_llm()
        
        self.agent = self._initialize_agent()
        
    
    def _initialize_embeddings(self):
        try:
            api_key = os.getenv('HUGGING_FACE_KEY')
            if not api_key:
                raise ValueError("HUGGING_FACE_KEY not found in environment variables")
            
            embeddings = HuggingFaceEndpointEmbeddings(
                model="sentence-transformers/all-MiniLM-L6-v2",
                huggingfacehub_api_token=api_key
            )
            logger.info("Embeddings initialized successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def _initialize_vectorstore(self):
        try:
            index_name = "medical-chatbot"
            vectorstore = PineconeVectorStore(
                index_name=index_name,
                embedding=self.embeddings,
            )
            logger.info(f"Vector store '{index_name}' initialized successfully")
            return vectorstore
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def _initialize_llm(self):
        try:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            model = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash",
                google_api_key=google_api_key,
                temperature=0.3,
                timeout=60
            )
            logger.info("Language model initialized successfully")
            return model
        except Exception as e:
            logger.error(f"Error initializing language model: {str(e)}")
            raise
    
    def _initialize_agent(self):
        
        vectorstore = self.vectorstore
        
        @tool(
            response_format="content_and_artifact",
            description="Retrieve relevant medical information from the Pinecone knowledge base."
        )
        def retrieve_medical_context(query: str):
            """Retrieve relevant medical information from the knowledge base."""
            try:
                logger.info(f"Retrieving context for query: {query[:50]}...")
                
                # Validate vectorstore
                if not vectorstore:
                    logger.error("Vectorstore is not initialized")
                    return "Knowledge base is not available.", []
                
                retrieved_docs = vectorstore.similarity_search(query, k=3)
                
                if not retrieved_docs:
                    logger.warning("No documents retrieved from vectorstore")
                    return "No relevant medical information found in the knowledge base.", []
                
                serialized = "\n\n".join(
                    f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}"
                    for doc in retrieved_docs
                )
                logger.info(f"Retrieved {len(retrieved_docs)} documents successfully")
                return serialized, retrieved_docs
            except Exception as e:
                logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
                return f"Error accessing knowledge base: {str(e)}", []
        
        # System prompt for the medical assistant
        system_prompt = """You are a knowledgeable and empathetic Medical Information Assistant. Your role is to provide accurate, evidence-based medical information based on authoritative medical documents.

                        🎯 CORE RESPONSIBILITIES:
                        1. Always use the retrieval tool to search for relevant medical information before answering
                        2. Base your responses on the retrieved medical literature and documents
                        3. Provide clear, accurate, and well-structured medical information
                        4. Use simple language that patients can understand while maintaining accuracy

                        📋 RESPONSE GUIDELINES:
                        - Structure responses with clear sections (Definition, Symptoms, Causes, Treatment, etc.)
                        - Use bullet points for lists to improve readability
                        - Include relevant medical terminology but explain complex terms
                        - Cite sources when providing specific medical information
                        - Be empathetic and supportive in your tone

                        ⚠️ SAFETY & LIMITATIONS:
                        - Always state that information is educational and not a substitute for professional medical advice
                        - If retrieved context is insufficient, clearly acknowledge this limitation
                        - Never make up or fabricate medical information
                        - For urgent symptoms, advise seeking immediate medical attention
                        - Never provide specific diagnoses or treatment plans
                        - Remind users to consult healthcare professionals for personalized advice

                        💡 RESPONSE FORMAT:
                        - Start with a clear, direct answer to the question
                        - Provide detailed explanation with supporting information
                        - Use relevant medical facts from retrieved documents
                        - End with appropriate disclaimers and recommendations

                        Remember: Your goal is to educate and inform, empowering users with knowledge while encouraging appropriate medical care."""

        try:
            agent = create_agent(
                self.llm,
                tools=[retrieve_medical_context],
                system_prompt=system_prompt
            )
            logger.info("Agent initialized successfully")
            return agent
        except Exception as e:
            logger.error(f"Error initializing agent: {str(e)}")
            raise
    
    @staticmethod
    def _extract_text_content(message_content):
        """
        Normalize agent message content (str/list/dict) into a plain text string.
        Returns None if no textual content is present.
        """
        if message_content is None:
            return None
        
        if isinstance(message_content, str):
            text = message_content.strip()
            return text if text else None
        
        if isinstance(message_content, dict):
            # LangChain tool responses often wrap text blocks in {"type": "text", "text": "..."}
            if message_content.get("type") == "text":
                text = message_content.get("text", "").strip()
                return text if text else None
            
            # Fall back to common keys
            for key in ("content", "text", "value"):
                if key in message_content:
                    return MedicalChatbot._extract_text_content(message_content[key])
            return None
        
        if isinstance(message_content, list):
            parts = []
            for block in message_content:
                block_text = MedicalChatbot._extract_text_content(block)
                if block_text:
                    parts.append(block_text)
            if parts:
                return "\n\n".join(parts).strip()
            return None
        
        return None
    
    def get_response(self, user_message: str) -> str:
        try:
            if not user_message or not user_message.strip():
                return "Please provide a valid question."
            
            logger.info(f"Processing user message: {user_message[:50]}...")
            
            # Stream events from the agent
            final_response = None
            event_count = 0
            
            logger.info("Starting agent stream...")
            for event in self.agent.stream(
                {"messages": [{"role": "user", "content": user_message}]},
                stream_mode="values"
            ):
                event_count += 1
                logger.debug(f"Received event {event_count}")
                
                # Get the last message from the event
                messages = event.get("messages", [])
                if not messages:
                    continue
                    
                last_message = messages[-1]
                
                if hasattr(last_message, 'type'):
                    message_type = last_message.type
                elif isinstance(last_message, dict):
                    message_type = last_message.get('type') or last_message.get('role')
                else:
                    message_type = None
                
                if hasattr(last_message, 'content'):
                    raw_content = last_message.content
                elif isinstance(last_message, dict):
                    raw_content = last_message.get('content')
                else:
                    raw_content = None
                
                text_content = self._extract_text_content(raw_content)
                
                is_ai_message = False
                if message_type in ('ai', 'assistant'):
                    is_ai_message = True
                elif hasattr(last_message, '__class__'):
                    cls_name = last_message.__class__.__name__.lower()
                    if 'aimessage' in cls_name:
                        is_ai_message = True
                
                if is_ai_message and text_content:
                    final_response = text_content
                    logger.debug(f"Captured AI response: {text_content[:50]}...")
            
            logger.info(f"Agent stream completed with {event_count} events")
            
            # Return the final response
            if final_response:
                logger.info("Response generated successfully")
                return final_response
            else:
                logger.warning("No valid AI response generated")
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question or ask something else."
                
        except TimeoutError as e:
            logger.error(f"Timeout generating response: {str(e)}")
            return "The request timed out. Please try again with a shorter question."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your request. Please try again or rephrase your question."
    
    def get_relevant_sources(self, query: str, k: int = 3) -> List[Dict]:
        
        try:
            docs = self.vectorstore.similarity_search(query, k=k)
            sources = []
            for doc in docs:
                sources.append({
                    'source': doc.metadata.get('source', 'Unknown'),
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            return sources
        except Exception as e:
            logger.error(f"Error retrieving sources: {str(e)}")
            return []


# Singleton instance for reuse
_chatbot_instance = None


def get_chatbot() -> MedicalChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = MedicalChatbot()
    return _chatbot_instance

