import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os

# Set API key
os.environ["GROQ_API_KEY"] = "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"

# Create a prompt template
prompt_template = """
You are a JavaScript code formatter. Your task is to take minified JavaScript code and format it for improved readability and also only give code no explaination needed.
Rules:
1. Add proper indentation
2. Add new lines between logical code blocks
3. Add meaningful spacing
4. Do not change variable or function names
5. Maintain the original functionality

Minified code:
{minified_code}

Formatted code:
"""

prompt = PromptTemplate(
    input_variables=["minified_code"],
    template=prompt_template
)

@st.cache_resource
def initialize_chain():
    """Initialize the LLM chain"""
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.1-70b-versatile",
    )
    
    chain = (
        {"minified_code": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    return chain

def unminify_js(minified_code, chain):
    """
    Unminify JavaScript code using LangChain with Groq
    """
    try:
        with st.spinner('Formatting code...'):
            response = chain.invoke(minified_code)
            return response.content.strip()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def main():
    st.title("CodeClarity")
    st.write("""
    This tool formats minified JavaScript code to improve readability. 
    Upload file containing minified code or paste your code directly.
    """)

    chain = initialize_chain()

    uploaded_file = st.file_uploader("Choose a JavaScript file", type=['js'])
    
    manual_input = st.text_area(
        "Or paste minified JavaScript code here:",
        height=150,
        help="You can either upload a file above or paste code here"
    )


    if st.button("Format Code"):
        minified_code = ""
        
        if uploaded_file is not None:
            try:
                minified_code = uploaded_file.getvalue().decode("utf-8")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return
        elif manual_input:
            minified_code = manual_input
        
        if minified_code:
            st.markdown("---")
            # Display original code
            st.subheader("Original Code")
            st.code(minified_code, language='javascript')
            
            # Display formatted code
            formatted_code = unminify_js(minified_code, chain)
            
            if formatted_code:
                st.markdown("---")
                st.subheader("Formatted Code")
                st.code(formatted_code)
                
                # Add download button for formatted code
                st.download_button(
                    label="Download Formatted Code",
                    data=formatted_code,
                    file_name="formatted_code.js",
                    mime="text/javascript"
                )
        else:
            st.warning("Please either upload a file or enter code manually.")
    st.markdown("""
    ### How to use:
    1. Upload file containing minified code, or
    2. Paste your minified code directly into the text area
    3. Click 'Format Code' to see the formatted version
    4. Use the 'Download Formatted Code' button to save the result
    
    ### Tips:
    - The tool maintains all functionality while improving readability
    - Large files may take longer to process
    - You can try the example code to see how it works
    """)
if __name__ == "__main__":
    main()
   	