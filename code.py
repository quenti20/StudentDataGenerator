# student_data_app.py
import streamlit as st
import base64
import tempfile
import os
from google import genai
from google.genai import types
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  


def generate_student_data(prompt):
    
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-pro-exp-03-25"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    full_response = ""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    chunks = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    for i, chunk in enumerate(chunks):
        if chunk.text:
            full_response += chunk.text
            progress = min((i + 1) * 10, 100)
            progress_bar.progress(progress)
            status_text.text(f"Generating data... {progress}%")
    
    progress_bar.empty()
    status_text.empty()
    
    return full_response

def create_download_link(df, filename="student_data.csv"):
    """Create a download link for the DataFrame as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href

def main():
    st.title("Student Data Generator")
    st.markdown("""
    This app generates sample student data using Google's Gemini API. 
    Click the button below to generate data and download it as a CSV file.
    """)
    
    prompt = """
    Generate me a student table with student_id,student_name,student_class,
    student_section,number_of_subjects,Maths,Science,English. Only generate 
    the DATA and the column fields as mentioned above, do not write anything 
    else so that I can store the data in a dataframe/dictionary.
    Generate at least 15 records.
    """
    
    if st.button("Generate Student Data"):
        with st.spinner("Generating student data..."):
            try:
                # Generate the data
                csv_data = generate_student_data(prompt)
                
                # Use temporary directory for file operations
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_file_path = os.path.join(temp_dir, "student_data.csv")
                    
                    # Save to temporary CSV file
                    with open(temp_file_path, "w") as f:
                        f.write(csv_data)
                    
                    # Convert to DataFrame for display
                    try:
                        df = pd.read_csv(temp_file_path)
                    except pd.errors.EmptyDataError:
                        st.error("No data was generated. Please try again.")
                        return
                    
                    # Display success message
                    st.success("Student data generated successfully!")
                    
                    # Display the data
                    st.subheader("Generated Student Data")
                    st.dataframe(df)
                    
                    # Show download button (reads from the DataFrame, not the file)
                    st.markdown(create_download_link(df), unsafe_allow_html=True)
                
            except PermissionError:
                st.error("Permission denied when trying to create file. Using in-memory operations instead.")
                # Fallback to in-memory operations
                from io import StringIO
                try:
                    df = pd.read_csv(StringIO(csv_data))
                    st.success("Student data generated successfully!")
                    st.subheader("Generated Student Data")
                    st.dataframe(df)
                    st.markdown(create_download_link(df), unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to process data: {str(e)}")
            
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()