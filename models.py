# models.py - FIXED VERSION WITH NLTK HANDLING
import os
import glob
import torch
import numpy as np
import re
import logging
import time
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    pipeline,
)
from sentence_transformers import SentenceTransformer
import streamlit as st
import nltk
from huggingface_hub import snapshot_download

# --- YOUR WORKING IMPORTS (keep these since they work) ---
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_huggingface.llms import HuggingFacePipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════
# NLTK DATA DOWNLOAD & SETUP (FIXED VERSION)
# ════════════════════════════════════════════════════════════════

def download_nltk_data():
    """Download all required NLTK data with proper error handling."""
    try:
        # Set NLTK data path
        nltk_data_path = os.getenv('NLTK_DATA', '/root/nltk_data')
        os.makedirs(nltk_data_path, exist_ok=True)
        nltk.data.path.append(nltk_data_path)
        
        # Download required NLTK data
        required_packages = ['punkt_tab', 'punkt', 'stopwords']
        
        for package in required_packages:
            try:
                nltk.data.find(f'tokenizers/{package}' if 'punkt' in package else f'corpora/{package}')
                print(f"✅ NLTK {package} already available")
            except LookupError:
                print(f"📥 Downloading NLTK {package}...")
                nltk.download(package, quiet=True, download_dir=nltk_data_path)
                print(f"✅ Downloaded NLTK {package}")
                
    except Exception as e:
        print(f"⚠️ NLTK download warning: {e}")
        # Fallback: try basic punkt if punkt_tab fails
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass

# Download NLTK data immediately when module loads
download_nltk_data()

# Safe tokenizer functions with fallbacks
def safe_sent_tokenize(text):
    """Safe sentence tokenizer with fallback."""
    try:
        return nltk.sent_tokenize(text)
    except Exception as e:
        print(f"⚠️ NLTK sentence tokenizer failed, using fallback: {e}")
        # Simple fallback: split on periods and question marks
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

def safe_word_tokenize(text):
    """Safe word tokenizer with fallback."""
    try:
        return nltk.word_tokenize(text)
    except Exception as e:
        print(f"⚠️ NLTK word tokenizer failed, using fallback: {e}")
        # Simple fallback: split on whitespace
        return text.split()

# ════════════════════════════════════════════════════════════════
# MODEL DOWNLOADING & MANAGEMENT
# ════════════════════════════════════════════════════════════════

MODELS_DIR = os.path.abspath("models_cache")

# Model definitions
FLAN_ID = "google/flan-t5-base"
EMB_ID = "sentence-transformers/all-MiniLM-L6-v2"
BART_LARGE_ID = "facebook/bart-large-cnn"
DISTILBART_ID = "sshleifer/distilbart-cnn-12-6"

MODEL_LIST = [EMB_ID, FLAN_ID, BART_LARGE_ID, DISTILBART_ID]

def download_models():
    """Download all required models for the application."""
    print(f"Starting model downloads into: {MODELS_DIR}")
    os.makedirs(MODELS_DIR, exist_ok=True)

    def download_model(repo_id):
        """Download a single model and its tokenizer files into the cache."""
        print(f"\n🚀 Downloading: {repo_id}")
        try:
            snapshot_download(
                repo_id=repo_id,
                cache_dir=MODELS_DIR,
                local_files_only=False,
                force_download=False,
                resume_download=True,
                allow_patterns=["*.json", "*.txt", "*.bin", "*.model", "*.py", "tokenizer*"],
                ignore_patterns=["*.h5", "*.msgpack", "*.ckpt", "*.safetensors"]
            )
            print(f"✅ Successfully downloaded {repo_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to download {repo_id}. Error: {e}")
            return False

    print("📥 Starting download of all models...")
    success_count = 0
    for model_id in MODEL_LIST:
        if download_model(model_id):
            success_count += 1
        time.sleep(2)

    print(f"\n--- Download process complete. ---")
    print(f"📊 Successfully downloaded: {success_count}/{len(MODEL_LIST)} models")
    return success_count == len(MODEL_LIST)

# ════════════════════════════════════════════════════════════════
# MODEL PATH MANAGEMENT (Enhanced version)
# ════════════════════════════════════════════════════════════════

BASE_PATH = os.path.join(os.getcwd(), "models_cache")

def find_snapshot_dir(model_folder):
    """Finds the actual snapshot directory containing model files."""
    # First try the direct path
    direct_path = os.path.join(BASE_PATH, model_folder)
    if os.path.exists(direct_path):
        return direct_path
    
    # Then try the snapshots directory
    snapshots_dir = os.path.join(BASE_PATH, model_folder, "snapshots")
    if os.path.isdir(snapshots_dir):
        matches = glob.glob(os.path.join(snapshots_dir, "*"))
        if matches and os.path.isdir(matches[0]):
            return matches[0]
    
    return os.path.join(BASE_PATH, model_folder)

def get_model_paths():
    """Dynamically get model paths with better error handling."""
    model_paths = {}
    
    model_folders = {
        "distilbart": "models--sshleifer--distilbart-cnn-12-6",
        "bart_large": "models--facebook--bart-large-cnn", 
        "flan_t5": "models--google--flan-t5-base",
        "embed": "models--sentence-transformers--all-MiniLM-L6-v2",
    }
    
    for key, folder in model_folders.items():
        path = find_snapshot_dir(folder)
        if os.path.exists(path):
            model_paths[key] = path
            print(f"✅ Found model path for {key}: {path}")
        else:
            print(f"❌ Model path not found for {key}: {path}")
            model_paths[key] = None
    
    return model_paths

# Initialize model paths
MODEL_PATHS = get_model_paths()
PIPELINES = {}  # Cache for loaded pipelines

# ════════════════════════════════════════════════════════════════
# TEXT SIMPLIFICATION (Fixed with safe NLTK tokenizer)
# ════════════════════════════════════════════════════════════════

def get_simplify_pipeline(model_choice: str):
    """Load summarization/simplification model pipeline with enhanced error handling."""
    if model_choice in PIPELINES:
        return PIPELINES[model_choice]
    
    try:
        task = "summarization"
        model_dir = None
        
        if model_choice == "DistilBART":
            model_dir = MODEL_PATHS["distilbart"]
        elif model_choice == "BART-Large":
            model_dir = MODEL_PATHS["bart_large"]
        elif model_choice == "FLAN-T5":
            model_dir = MODEL_PATHS["flan_t5"]
            task = "text2text-generation"
        else:
            return f"Error: Unknown model choice '{model_choice}'"
        
        # Enhanced path validation
        if not model_dir or not os.path.exists(model_dir):
            return f"Error: Model directory not found → {model_dir}"

        # Load model with better error handling
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_dir)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
        except Exception as e:
            return f"Error: Failed to load model/tokenizer → {e}"

        device = 0 if torch.cuda.is_available() else -1
        print(f"Device set to use {'cuda:' + str(device) if device != -1 else 'cpu'}")

        try:
            pipe = pipeline(task, model=model, tokenizer=tokenizer, device=device)
            PIPELINES[model_choice] = pipe
            return pipe
        except Exception as e:
            return f"Error: Pipeline creation failed → {e}"
            
    except Exception as e:
        error_msg = f"Error: Unexpected error in get_simplify_pipeline → {e}"
        print(error_msg)
        PIPELINES[model_choice] = error_msg
        return error_msg

def simplify_text(text: str, model_choice: str = "DistilBART", level: str = "Intermediate") -> str:
    """Your excellent simplification with safe NLTK tokenizer"""
    try:
        pipe = get_simplify_pipeline(model_choice)
        if isinstance(pipe, str) and pipe.startswith("Error:"): 
            return pipe
        
        if not text or not text.strip(): 
            return "Error: Input text is empty."

        # Use safe sentence tokenizer instead of nltk.sent_tokenize
        chunks = safe_sent_tokenize(text)
        outputs = []

        # Your excellent level-specific logic
        if level == "Basic": 
            min_sum_ratio, max_sum_ratio = (0.3, 0.7)
        elif level == "Advanced": 
            min_sum_ratio, max_sum_ratio = (0.6, 1.0) 
        else: 
            min_sum_ratio, max_sum_ratio = (0.5, 0.9)

        for i, chunk in enumerate(chunks):
            # Use safe word tokenizer instead of len(chunk.split())
            chunk_words = safe_word_tokenize(chunk)
            chunk_word_count = len(chunk_words)
            
            if chunk_word_count < 8:
                outputs.append(chunk)
                continue

            # Your excellent prompt engineering
            if pipe.task == "text2text-generation":
                min_len = int(chunk_word_count * 0.8)
                max_len = int(chunk_word_count * 1.5)
                min_len = max(10, min_len)
                max_len = max(min_len + 20, max_len)
                
                # Your great level-specific prompts
                if level == "Basic":
                    level_instruction = "Rewrite the following text to be extremely simple, as if explaining to a 10-year-old. Use very short sentences and everyday words. Replace legal jargon with simple explanations."
                elif level == "Advanced":
                    level_instruction = "Rewrite the following text to be professional, modern, and clear, while maintaining all legal nuance. Focus on improving flow and readability. Do not shorten or summarize."
                else:
                    level_instruction = "Rewrite the following text in simple, plain English. Replace complex legal words with common equivalents (e.g., 'heretofore' means 'previously', 'terminate' means 'end'). Do not summarize the text, just rewrite it to be easier to understand."

                prompt = f"{level_instruction}\n\nOriginal Text: \"{chunk}\"\n\nSimplified Text:"
            else:
                min_len = max(10, int(chunk_word_count * min_sum_ratio))
                max_len = max(min_len + 10, int(chunk_word_count * max_sum_ratio))
                prompt = chunk
            
            try:
                if pipe.task == "text2text-generation":
                    output = pipe(prompt, max_new_tokens=max_len, min_new_tokens=min_len, num_beams=4, early_stopping=True)
                    if output and isinstance(output, list) and 'generated_text' in output[0]:
                        outputs.append(output[0]['generated_text'])
                    else:
                        outputs.append(chunk)
                else:
                    output = pipe(chunk, max_new_tokens=max_len, min_new_tokens=min_len, num_beams=4, early_stopping=True)
                    if output and isinstance(output, list) and 'summary_text' in output[0]:
                        outputs.append(output[0]['summary_text'])
                    else:
                        outputs.append(chunk)
            except Exception as chunk_e:
                print(f"Error processing chunk {i+1}: {chunk_e}")
                outputs.append(chunk)
        
        simplified = " ".join(outputs)
        cleaned_simplified = re.sub(r'\n\s*\n', '\n\n', simplified)
        cleaned_simplified = re.sub(r'(\n\n){2,}', '\n\n', cleaned_simplified)
        return cleaned_simplified.strip()

    except Exception as e:
        return f"Error: Simplification failed → {e}"

# ════════════════════════════════════════════════════════════════
# RAG IMPLEMENTATION (Your excellent version with enhanced robustness)
# ════════════════════════════════════════════════════════════════

PROMPT_TEMPLATE = """
You are a helpful and conversational assistant. Use the provided context to answer the user's question.
The user's recent chat history (if any) is provided before the main question.
ONLY use the information from the 'Document Context'. Do not make up answers.
If the answer is not in the context, say "I'm sorry, that information is not in the document."

Document Context:
{context}

Chat History & Question:
{question}

Helpful Answer:"""

class ClauseEaseRAG:
    """Your excellent RAG implementation with enhanced error handling"""
    
    def __init__(self, document_text: str):
        # Enhanced validation
        if not document_text or len(document_text.strip()) < 10:
            raise ValueError("Document text is too short or empty for RAG initialization.")
        
        self.full_text = document_text 
        self.chat_history = []
        
        try:
            # Your text splitting logic
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=500, 
                chunk_overlap=50, 
                separators=["\n\n", "\n", ". ", " "]
            )
            docs = self.splitter.create_documents([document_text])
            if not docs:
                raise ValueError("Text splitting resulted in zero documents.")
            
            # Enhanced path validation
            embed_dir = MODEL_PATHS["embed"]
            if not embed_dir or not os.path.exists(embed_dir):
                raise ValueError(f"Embedding model not found at {embed_dir}")
                
            self.embedding_model = HuggingFaceEmbeddings(model_name=embed_dir)
            self.vectorstore = FAISS.from_documents(docs, self.embedding_model)
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            
            # Generator pipeline with enhanced error handling
            gen_dir = MODEL_PATHS["flan_t5"]
            if not gen_dir or not os.path.exists(gen_dir):
                raise ValueError(f"Generator model not found at {gen_dir}")
            
            rag_pipeline_key = "FLAN-T5-RAG"
            if rag_pipeline_key not in PIPELINES:
                try:
                    generator_tokenizer = AutoTokenizer.from_pretrained(gen_dir)
                    generator_model = AutoModelForSeq2SeqLM.from_pretrained(gen_dir)
                    device_num = 0 if torch.cuda.is_available() else -1
                    
                    pipe = pipeline(
                        "text2text-generation",
                        model=generator_model,
                        tokenizer=generator_tokenizer,
                        max_new_tokens=512,
                        device=device_num,
                    )
                    PIPELINES[rag_pipeline_key] = pipe
                except Exception as e:
                    raise ValueError(f"Failed to create RAG pipeline: {e}")
            
            pipe = PIPELINES[rag_pipeline_key]
            if isinstance(pipe, str) and pipe.startswith("Error:"):
                raise ValueError(f"RAG pipeline has error: {pipe}")
            
            llm = HuggingFacePipeline(pipeline=pipe)
            
            # Your prompt template
            prompt = PromptTemplate(
                template=PROMPT_TEMPLATE, 
                input_variables=["context", "question"]
            )
            
            # Your QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=self.retriever,
                chain_type="stuff",
                return_source_documents=False,
                chain_type_kwargs={"prompt": prompt}
            )
            
        except Exception as e:
            raise ValueError(f"RAG initialization failed: {e}")

    def query(self, question: str) -> str:
        """Your excellent query method with enhanced error handling"""
        if not question or not question.strip():
            return "Please provide a question."
        
        try:
            # Your chat history formatting
            history_string = "\n".join(f"User: {q}\nAI: {a}" for q, a in self.chat_history)
            combined_input = f"{history_string}\n\nUser: {question}"
            
            # Get response
            response = self.qa_chain.invoke({"query": combined_input.strip()})
            answer = response.get("result", "No answer generated.")
            
            # Update history
            self.chat_history.append((question, answer))
            self.chat_history = self.chat_history[-3:]
            
            return answer
            
        except Exception as e:
            return f"Error processing your question: {str(e)}"

def create_rag_chain(text):
    """Enhanced version with better error handling"""
    try:
        return ClauseEaseRAG(text)
    except Exception as e:
        return f"Error: Failed to create RAG system → {str(e)}"

# ------------------------------------------------------------------
# --- YOUR EXCELLENT CHATBOT INTELLIGENCE (Keep exactly as is) ---
# ------------------------------------------------------------------

CHITCHAT_RESPONSES = {
    "greeting": "Hello! I'm ready to help you with your document. What would you like to know?",
    "thanks": "You're welcome! Do you have any other questions about the document?",
    "goodbye": "Goodbye! Let me know if you need more help later.",
    "help": "I am a legal assistant. You can ask me specific questions about the document you uploaded, like 'What is the termination date?' or 'Summarize the liability clause'.",
}

GREETINGS = {'hi', 'hello', 'hey', 'howdy', 'greetings', 'good morning', 'good afternoon', 'good evening'}
THANKS = {'thanks', 'thank you', 'thx', 'appreciate it'}
GOODBYES = {'bye', 'goodbye', 'see you', 'later'}
HELP_QUESTIONS = {'what can you do', 'help', 'how do you work', 'help me'}

META_QUESTIONS = {
    "what is this": "meta",
    "what is this about": "meta",
    "what is this document": "meta", 
    "what is this document about": "meta",
    "the document is about what": "meta",
    "summarize this": "meta",
    "give me a summary": "meta",
}

DEFINITION_TRIGGERS = ['what is', "what's", 'what does', 'define', 'meaning of']

def get_query_type(prompt: str) -> tuple:
    """Your excellent query classification"""
    lower_prompt = prompt.lower().strip().rstrip('?!.')
    
    if lower_prompt in GREETINGS:
        return (CHITCHAT_RESPONSES["greeting"], 'chitchat')
    if lower_prompt in THANKS:
        return (CHITCHAT_RESPONSES["thanks"], 'chitchat')
    if lower_prompt in GOODBYES:
        return (CHITCHAT_RESPONSES["goodbye"], 'chitchat')
    if lower_prompt in HELP_QUESTIONS:
        return (CHITCHAT_RESPONSES["help"], 'chitchat')
    
    if lower_prompt.startswith("summarize") or lower_prompt in META_QUESTIONS:
        return (None, 'meta')

    for trigger in DEFINITION_TRIGGERS:
        if lower_prompt.startswith(trigger):
            rag_keywords = [
                "this document", "in this document", "this agreement", 
                "in this agreement", "this resume", "in this resume", 
                "the clause", "the file", "the document", "contain", "contains"
            ]
            
            is_rag_question = any(keyword in lower_prompt for keyword in rag_keywords)
            if not is_rag_question:
                return (None, 'definition')
            break

    return (None, 'rag')

def query_rag_chain(chain, prompt):
    """Your excellent routing logic"""
    try:
        final_answer, query_type = get_query_type(prompt)

        if query_type == 'chitchat':
            return final_answer

        if query_type == 'definition':
            try:
                rag_pipeline_key = "FLAN-T5-RAG"
                if rag_pipeline_key not in PIPELINES:
                    return "General chat model is not available. Please re-upload the document."
                
                general_llm_pipe = PIPELINES[rag_pipeline_key]
                general_prompt = f"Question: {prompt}\n\nHelpful Answer:"
                
                response = general_llm_pipe(general_prompt, max_new_tokens=256)
                
                if response and 'generated_text' in response[0]:
                    return response[0]['generated_text']
                else:
                    return "I'm sorry, I had trouble forming a general answer."
            except Exception as e:
                return f"Error during general chat: {str(e)}"

        if query_type == 'meta':
            if not (hasattr(chain, 'full_text') and chain.full_text):
                return "I cannot summarize because no document text is available."
            
            return simplify_text(chain.full_text, model_choice="FLAN-T5", level="Basic")

        if query_type == 'rag':
            if isinstance(chain, str) and chain.startswith("Error:"):
                return chain
            
            if hasattr(chain, 'query') and callable(chain.query):
                return chain.query(prompt)
            else:
                return "RAG system is not properly initialized."
            
        return "I'm not sure how to handle that request."
    
    except Exception as e:
        return f"Error processing your request: {str(e)}"

# ════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ════════════════════════════════════════════════════════════════

def check_models_available():
    """Check if all required models are available."""
    print("🔍 Checking model availability...")
    all_available = True
    
    for model_key, model_path in MODEL_PATHS.items():
        if model_path and os.path.exists(model_path):
            print(f"✅ {model_key}: Available at {model_path}")
        else:
            print(f"❌ {model_key}: NOT FOUND at {model_path}")
            all_available = False
    
    return all_available

def initialize_models():
    """Pre-load commonly used models."""
    print("🚀 Initializing models...")
    
    if not check_models_available():
        print("⚠️ Some models are missing. The app may not work fully.")
        return False
    
    try:
        # Pre-load FLAN-T5 for RAG
        get_simplify_pipeline("FLAN-T5")
        print("✅ FLAN-T5 model initialized")
        return True
    except Exception as e:
        print(f"❌ Model initialization failed: {e}")
        return False

# ════════════════════════════════════════════════════════════════
# ENHANCED QUERY HANDLER FOR CHAT VIEW
# ════════════════════════════════════════════════════════════════

def handle_user_query(rag_chain, query: str, model_name: str = "FLAN-T5"):
    """Enhanced query handler for chat view with better error handling."""
    try:
        # First try the standard RAG query
        response = query_rag_chain(rag_chain, query)
        
        # If RAG fails or returns error, try simplification as fallback
        if (isinstance(response, str) and 
            any(error_indicator in response.lower() for error_indicator in 
                ['error', 'not in the document', 'sorry', 'failed', 'not available'])):
            
            # Try to get document text and use simplification
            if hasattr(rag_chain, 'full_text') and rag_chain.full_text:
                document_text = rag_chain.full_text
                
                # Check if query is asking about document content
                if any(keyword in query.lower() for keyword in 
                      ['summary', 'overview', 'what is this', 'what does this document']):
                    return simplify_text(document_text, model_choice=model_name, level="Basic")
                
                # For other queries, try to find relevant content
                sentences = safe_sent_tokenize(document_text)
                relevant_sentences = []
                
                query_words = set(safe_word_tokenize(query.lower()))
                for sentence in sentences:
                    sentence_words = set(safe_word_tokenize(sentence.lower()))
                    if len(query_words.intersection(sentence_words)) > 0:
                        relevant_sentences.append(sentence)
                
                if relevant_sentences:
                    relevant_text = " ".join(relevant_sentences[:3])
                    return f"Based on the document content: {relevant_text}"
            
            
            return "I couldn't find specific information about that in the document. The document might not contain detailed information on this topic."
        
        return response
        
    except Exception as e:
        return f"I encountered an error while processing your question: {str(e)}"

if __name__ == "__main__":
    if initialize_models():
        print("✅ All models initialized successfully!")
    else:
        print("❌ Model initialization had issues. Please check model downloads.")