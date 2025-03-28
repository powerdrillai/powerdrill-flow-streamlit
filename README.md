# Powerdrill Flow - Streamlit

A Streamlit application for AI data analysis using the [Powerdrill API](https://docs.powerdrill.ai/api-reference/v2/overview).

## Features

- Beautiful, clean, and modern UI
- File uploading with support for multiple file formats
- Dataset and data source management
- AI-powered data analysis with streaming responses
- Suggested questions for data exploration
- Chat-like interface for interactions

## Supported File Formats

- CSV (.csv)
- TSV (.tsv)
- Markdown (.md, .mdx)
- JSON (.json)
- Text (.txt)
- PDF (.pdf)
- PowerPoint (.pptx)
- Word (.docx)
- Excel (.xls, .xlsx)

## Getting Started

### Prerequisites

- Python 3.8 or newer
- PowerDrill account with API access

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/powerdrill-flow-streamlit.git
   cd powerdrill-flow-streamlit
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```
   cp .env.template .env
   ```

### Running the Application

Start the Streamlit application:
```
streamlit run app.py
```

The application will be available at http://localhost:8501

## Usage

1. Enter your PowerDrill User ID and API Key to authenticate
2. Upload files or select an existing dataset
3. Wait for data processing to complete
4. Start asking questions about your data
5. Explore suggested questions or ask your own

## Directory Structure

```
powerdrill-flow-streamlit/
├── app.py                # Main application file
├── components/
│   ├── auth.py           # Authentication component
│   ├── chat_interface.py # Chat interface component
│   └── data_manager.py   # Data management component
├── utils/
│   ├── api_client.py     # PowerDrill API client
│   └── file_uploader.py  # File upload utility
├── .env                  # Environment variables (create from .env.template)
├── .env.template         # Environment variables template
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## License

This project is licensed under the Apache License - see the LICENSE file for details. 