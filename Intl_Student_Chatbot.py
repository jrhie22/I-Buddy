Intl_Student_Chatbot

from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit chatbot that answers questions using OpenAI and a small FAQ file
import streamlit as st
from langchain.chat_models import ChatOpenAI
# import necessary libraries first
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS 
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import HumanMessage, AIMessage        

user_input = st.text_input("Ask something:")
st.write("Your question was:", user_input)

# Load the FAQ file
loader = TextLoader("faq.txt")
documents = loader.load()
