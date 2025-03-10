# Document Analysis Thread

## Overview
`AnalysisThread` is a specialized QThread implementation for asynchronous analysis of PDF documents using AI services. The class handles reading, chunking, processing, and summarizing PDF content to generate comprehensive document analyses without blocking the main application UI.

## Key Features
- **Asynchronous Processing**: Runs as a separate thread to prevent UI freezing
- **PDF Handling**: Uses PyMuPDF to extract text from PDF documents
- **Intelligent Text Chunking**: Splits documents into manageable chunks based on token limits
- **Progressive Analysis**: Processes document chunks sequentially with contextual awareness
- **Chunk-aware AI Prompting**: Provides context to AI about chunk position in the document
- **Summary Generation**: Creates final summaries from multiple chunk analyses
- **Robust Error Handling**: Manages various file access and processing errors

## Signal System
- `progress_updated`: Emits progress percentage as analysis proceeds
- `analysis_completed`: Emits file name and final analysis results when complete
- `error_occurred`: Emits file name and error message when errors occur
- `status_updated`: Provides status messages during processing

## Text Processing Logic
1. **Token Estimation**: Calculates approximate token counts (English words × 1.3, Chinese characters × 2)
2. **Smart Chunking**: 
   - Primary split by paragraphs
   - Secondary split by sentences if paragraphs exceed token limits
   - Maintains context across chunk boundaries
3. **Contextual Analysis**: Each chunk is analyzed with awareness of its position in the document

## Analysis Workflow
1. Read and extract text content from PDF
2. Split text into optimally sized chunks
3. Process each chunk with the AI service, providing sequential context
4. For multi-chunk documents, generate a final summary analysis
5. Return comprehensive analysis results

## Error Management
- File not found errors
- Permission errors
- PDF format/corruption errors
- Empty document handling
- AI service connection/processing errors

## Usage
The thread requires three parameters:
- `file_path`: Path to the PDF file
- `ai_service`: AI service instance to use for analysis
- `instruction`: Analysis instructions/prompts for the AI service

Implement handlers for the emitted signals to receive progress updates and results.

## Example
```python
# Create and start an analysis thread
analysis_thread = AnalysisThread(
    file_path="path/to/document.pdf",
    ai_service=my_ai_service,
    instruction="Analyze this paper and identify its key contributions"
)

# Connect signals
analysis_thread.progress_updated.connect(self.update_progress_bar)
analysis_thread.status_updated.connect(self.update_status_label)
analysis_thread.analysis_completed.connect(self.handle_analysis_result)
analysis_thread.error_occurred.connect(self.handle_error)

# Start processing
analysis_thread.start()