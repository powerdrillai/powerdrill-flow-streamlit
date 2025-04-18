# Powerdrill Flow - Streamlit

A Streamlit application for AI data analysis using the Powerdrill API, please refer to the API document: https://docs.powerdrill.ai/api-reference/v2/overview.

## Features

- Clean, and modern UI based on Streamlit
- File uploading with support for multiple file formats
- Dataset and data source management
- AI-powered data analysis with streaming responses
- Suggested questions for data exploration
- Chat-like interface for interactions

## Demo

Watch this demo to see Powerdrill Flow Streamlit in action:

[![Powerdrill Flow Streamlit Demo](https://img.youtube.com/vi/dTlJTmCTRiQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=dTlJTmCTRiQ)

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
- Powerdrill account with API access (basically, you need **User ID** and **Project API Key**)

### Getting Powerdrill Credentials

To use this application, you'll need a Powerdrill account with valid API credentials (**User ID** and **API Key**). Here's how to obtain them:

1. Sign up for a Powerdrill Team account if you haven't already
2. Navigate to your account settings
3. Look for the API section where you'll find your:
   - User ID: A unique identifier for your account
   - API Key: Your authentication token for API access

First, watch this video tutorial on how to create your Powerdrill Team:

[![Create Powerdrill Team Tutorial](https://img.youtube.com/vi/I-0yGD9HeDw/maxresdefault.jpg)](https://www.youtube.com/watch?v=I-0yGD9HeDw)

Then, follow this video tutorial for setting up your API credentials:

[![Powerdrill API Setup Tutorial](https://img.youtube.com/vi/qs-GsUgjb1g/maxresdefault.jpg)](https://www.youtube.com/watch?v=qs-GsUgjb1g)

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

1. Enter your Powerdrill User ID and API Key to authenticate
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
│   ├── api_client.py     # Powerdrill API client
│   └── file_uploader.py  # File upload utility
├── .env                  # Environment variables (create from .env.template)
├── .env.template         # Environment variables template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.