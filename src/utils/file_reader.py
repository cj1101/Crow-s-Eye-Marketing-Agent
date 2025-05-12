"""
File reader utility for context files.
Extracts text content from different file formats.
"""
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

def read_file_content(file_path: str) -> Optional[str]:
    """
    Read content from a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str or None: File content as string, or None on error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in [".txt"]:
            return read_text_file(file_path)
        elif file_ext in [".pdf"]:
            return read_pdf_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return None
            
    except Exception as e:
        logger.exception(f"Error reading file {file_path}: {e}")
        return None

def read_text_file(file_path: str) -> Optional[str]:
    """
    Read content from a text file.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        str or None: File content as string, or None on error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.exception(f"Error reading text file {file_path}: {e}")
        return None

def read_pdf_file(file_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str or None: Extracted text content, or None on error
    """
    try:
        # First try using PyMuPDF (fitz) which is already a dependency
        import fitz
        text_content = []
        
        with fitz.open(file_path) as pdf:
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text_content.append(page.get_text())
                
        return "\n\n".join(text_content)
        
    except ImportError:
        logger.warning("PyMuPDF not available, trying pypdf as fallback")
        
        try:
            # Fallback to pypdf if available
            import pypdf
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
                    
            return "\n\n".join(text_content)
            
        except ImportError:
            logger.error("No PDF reading library available. Install PyMuPDF or pypdf.")
            return None
        except Exception as e:
            logger.exception(f"Error reading PDF file with pypdf {file_path}: {e}")
            return None
            
    except Exception as e:
        logger.exception(f"Error reading PDF file {file_path}: {e}")
        return None

def extract_context_from_files(file_paths: List[str]) -> str:
    """
    Extract and combine content from multiple files.
    
    Args:
        file_paths: List of file paths to process
        
    Returns:
        str: Combined content from all files
    """
    combined_content = []
    
    for file_path in file_paths:
        content = read_file_content(file_path)
        if content:
            file_name = os.path.basename(file_path)
            combined_content.append(f"--- Content from {file_name} ---")
            combined_content.append(content)
            
    if not combined_content:
        return ""
        
    return "\n\n".join(combined_content) 