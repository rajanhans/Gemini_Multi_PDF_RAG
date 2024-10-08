#Rajan Hans - Jan 08 2024
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv


#load_dotenv()

#genai.configure(api_key = os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key=st.secrets["api_key"])
# one or more pdf files can be dropped into the files sections, 
# for each pdf file read each page add to the text string
def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

# split the complete text string into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    chunks=text_splitter.split_text(text)
    return chunks

# create vector embeddings of each of the chunks
def get_vector_store(text_chunks):
    embeddings=GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    vector_store=FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")
    
    
# initialize and create the chain using the prompt template and gemini-pro model 
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context"\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:"""

    #added to centralize the model settings 
    # Set up the model
    generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
    }

    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
    ]

    model =ChatGoogleGenerativeAI(model="gemini-pro", generation_config=generation_config,safety_settings=safety_settings)
    prompt=PromptTemplate(template=prompt_template, input_variables=["context","question"])

    chain=load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain


#this is  the question and answer section. First load the local database and 
def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')

    #added to centralize the model settings 
    # Set up the model
    generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
    }

    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
    ]

    new_db = FAISS.load_local("faiss_index", embeddings)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()
    response = chain({"input_documents":docs, "question":user_question}, return_only_outputs=True)

    print(response)
    st.write("Reply:", response["output_text"])


def main():
    st.set_page_config("Rajan's Chat with Multiple PDF")
    st.header("Rajan's Multi-PDF Chat ft. Google Gemini-Pro💁")

    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")



if __name__ == "__main__":
    main()

    

                   
    






