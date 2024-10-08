import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os
import re

os.environ["GROQ_API_KEY"] = "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"

# Add regex patterns for credentials
PATTERNS = {
    'api_keys': r"""(?i)(?:api[_-]?key|apikey|access[_-]?token|auth[_-]?token)["\s]*(?::|=|>)["\s]*(['\"])?([a-zA-Z0-9]{16,})\1?""",
    'credentials': r"""(?i)(["']?(?:username|password|passwd|user|uid|email)["']?\s*[:=]\s*["']([^"']{3,})["'])""",
    'generic_secrets': r"""(?i)(["']?(?:secret|private_key|secret_key|token)["']?\s*[:=]\s*["']([^"']{3,})["'])"""
}

prompt_template = """
You are a JavaScript code formatter. Your task is to take minified JavaScript code and format it for improved readability and also only give code no explanation needed.
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

def extract_links(js_content):
    # Linkfinder regex remains the same
    regex = r"""
     (?:"|')                               # Start newline delimiter
  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    |
    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be
    |
    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/.]{1,}                # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
    |
    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or 
  )
  (?:"|')                                
    """
    return re.finditer(regex, js_content, re.VERBOSE)

def find_credentials(js_content):
    findings = {
        'API Keys': [],
        'Credentials': [],
        'Other Secrets': []
    }
    
    for pattern_name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, js_content):
            if len(match.groups()) > 1:
                value = match.group(2)
            else:
                value = match.group(1)
                
            category = 'API Keys' if 'api_keys' in pattern_name else \
                      'Credentials' if 'credentials' in pattern_name else \
                      'Other Secrets'
                      
            findings[category].append({
                'value': value,
                'start': match.start(),
                'end': match.end()
            })
    
    return findings

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

def display_findings(js_content, findings, show_context):
    for finding in findings:
        if show_context:
            start = max(0, finding['start'] - 50)
            end = min(len(js_content), finding['end'] + 50)
            context = js_content[start:end].replace('\n', ' ').strip()
            
            st.markdown(f"**Found:** `{finding['value']}`")
            st.markdown("**Context:**")
            st.code(context, language='javascript')
        else:
            st.code(finding['value'])

def main():
    st.set_page_config(
        page_title="CodeClarity",
    )

    st.title("CodeClarity")
    st.write("""
    This tool formats minified JavaScript code, extracts links, and identifies potential credentials. 
    Upload a file containing minified code or paste your code directly.
    """)

    chain = initialize_chain()
    
    show_context = st.checkbox("Show context around findings", value=False)

    uploaded_file = st.file_uploader("Choose a JavaScript file", type=['js'])
    
    manual_input = st.text_area(
        "Or paste minified JavaScript code here:",
        height=150,
        help="You can either upload a file above or paste code here"
    )

    if st.button("Analyze Code"):
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
            st.subheader("Original Code")
            st.code(minified_code, language='javascript')
            
            formatted_code = unminify_js(minified_code, chain)
            
            if formatted_code:
                st.markdown("---")
                st.subheader("Formatted Code")
                st.code(formatted_code)
                
                st.download_button(
                    label="Download Formatted Code",
                    data=formatted_code,
                    file_name="formatted_code.js",
                    mime="text/javascript"
                )
                
                # Extract and display links
                st.markdown("---")
                st.subheader("Extracted Links")
                matches = extract_links(formatted_code)
                found_links = set()
                
                for match in matches:
                    link = match.group(1)
                    if link not in found_links:
                        found_links.add(link)
                        
                        if show_context:
                            start = max(0, match.start() - 50)
                            end = min(len(formatted_code), match.end() + 50)
                            context = formatted_code[start:end].replace('\n', ' ').strip()
                            
                            st.markdown(f"**Link:** `{link}`")
                            st.markdown("**Context:**")
                            st.code(context, language='javascript')
                        else:
                            st.code(link)

                if not found_links:
                    st.info("No links found in the provided JavaScript code.")
                
                credential_findings = find_credentials(formatted_code)
                for category, findings in credential_findings.items():
                    if findings:
                        st.markdown(f"### {category}")
                        display_findings(formatted_code, findings, show_context)
                
                if all(len(findings) == 0 for findings in credential_findings.values()):
                    st.info("No credentials or secrets found in the provided JavaScript code.")
                
        else:
            st.warning("Please either upload a file or enter code manually.")

    st.markdown("""
    ### Tips:
    - The tool maintains all functionality while improving readability
    - Large files may take longer to process
    - The analyzer finds URLs, file paths, and potential credentials in the JavaScript code
    - Be cautious with identified credentials as they may include false positives
    """)

if __name__ == "__main__":
    main()
