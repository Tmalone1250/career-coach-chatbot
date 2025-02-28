# AI Career Coach Chatbot

An intelligent career coaching assistant that provides personalized guidance, job search assistance, and professional development support.

## Features

### 1. Career Path Guidance
- Personalized career path suggestions based on interests and skills
- Skill gap analysis and development recommendations
- Industry insights and trends
- Professional growth strategies

### 2. Job Search Assistance
- Real-time job listings from Google Jobs
- Location-based job search
- Salary information and job type filtering
- Application advice tailored to specific job postings
- Job description previews with highlights

### 3. Resume & Cover Letter Support
- Resume analysis and improvement suggestions
- Cover letter customization tips
- ATS optimization recommendations
- Skills and achievements highlighting

### 4. Interview Preparation
- Industry-specific interview questions
- Answer frameworks and examples
- Company research guidance
- Interview strategy tips

## Technology Stack

- **Backend**: Python with Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI Integration**: OpenRouter API for intelligent responses
- **Job Search**: SerpAPI (Google Jobs integration)
- **UI Framework**: Custom responsive design

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/career-coach-chatbot.git
cd career-coach-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
FLASK_SECRET_KEY="your_secret_key"
FLASK_APP="app.py"
SERPAPI_KEY="your_serpapi_key"
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Keys Required

- **SerpAPI Key**: Required for job search functionality. Get it from [SerpAPI](https://serpapi.com/)
- **OpenRouter API Key**: Required for AI responses. Get it from [OpenRouter](https://openrouter.ai/)

## Usage

1. **Career Guidance**:
   - Enter your interests and skills
   - Receive personalized career path suggestions
   - Get skill development recommendations

2. **Job Search**:
   - Enter job role, location, and preferences
   - View relevant job listings with detailed information
   - Receive tailored application advice

3. **Resume Upload**:
   - Upload your resume for analysis
   - Get personalized improvement suggestions
   - Receive ATS optimization tips

4. **Interview Prep**:
   - Select industry and role
   - Get customized interview questions
   - Receive detailed answer guidelines

## Project Structure

```
career-coach-chatbot/
├── app.py              # Main Flask application
├── static/
│   ├── script.js      # Frontend JavaScript
│   └── styles.css     # CSS styles
├── templates/
│   └── index.html     # Main HTML template
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenRouter API for AI capabilities
- SerpAPI for job search integration
- Flask community for the web framework
- Contributors and testers