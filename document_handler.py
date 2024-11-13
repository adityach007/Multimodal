import pandas as pd
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, CSVLoader
import tempfile
import os

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def process_file(self, file_obj, file_type):
        """Process different file types and return text content."""
        if file_type == 'txt':
            return self._process_text(file_obj)
        elif file_type == 'csv':
            return self._process_csv(file_obj)
        elif file_type in ['xlsx', 'xls']:
            return self._process_excel(file_obj)
        elif file_type == 'docx':
            return self._process_docx(file_obj)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _process_text(self, file_obj):
        """Process text files."""
        content = file_obj.read().decode('utf-8')
        return self.text_splitter.split_text(content)
    
    def _process_csv(self, file_obj):
        """Process CSV files."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_file.write(file_obj.read())
            temp_file.flush()
            
            try:
                loader = CSVLoader(temp_file.name)
                documents = loader.load()
                return [doc.page_content for doc in documents]
            finally:
                os.unlink(temp_file.name)
    
    def _process_excel(self, file_obj):
        """Process Excel files."""
        df = pd.read_excel(file_obj)
        return [df.to_string()]
    
    def _process_docx(self, file_obj):
        """Process Word documents."""
        doc = Document(file_obj)
        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return self.text_splitter.split_text(content)
