from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import PyPDF2  # For PDF processing
import io  # For handling file streams
from serpapi import GoogleSearch
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

# Initialize SerpAPI client
def get_serpapi_client():
    return GoogleSearch({
        "api_key": os.getenv('SERPAPI_KEY'),
        "engine": "google"
    })

# Create a global serpapi_client
serpapi_client = get_serpapi_client()

def create_career_coach_prompt(resume_text=None, cover_letter_text=None, user_query=None, context_type=None):
    base_prompt = """You are an experienced Career Coach and Professional Development Expert with over 15 years of experience helping professionals advance their careers. Your expertise includes resume writing, interview preparation, career transitions, skill development, and professional growth strategies.

Key Responsibilities:
1. Analyze resumes and cover letters to identify strengths, weaknesses, and areas for improvement
2. Provide actionable feedback for career development
3. Help identify skill gaps and recommend learning resources
4. Guide career transitions and professional growth
5. Offer interview preparation advice and industry insights

Communication Style:
- Professional yet approachable
- Clear and concise
- Provide specific, actionable feedback
- Balance constructive criticism with positive reinforcement
- Use concrete examples from the user's experience

Interview Coaching Capabilities:
1. Role-Specific Interview Preparation:
   - Analyze job requirements and generate relevant questions
   - Provide industry-specific technical questions
   - Offer behavioral question frameworks (STAR method)
   - Suggest role-appropriate portfolio/project discussions

2. Answer Structuring:
   - Guide on professional self-presentation
   - Teach the STAR method (Situation, Task, Action, Result)
   - Help craft compelling stories from past experiences
   - Provide templates for common questions

3. Interview Strategy:
   - Advise on pre-interview research
   - Guide salary negotiation approaches
   - Offer tips for virtual/in-person interviews
   - Suggest questions to ask interviewers

4. Technical Interview Preparation:
   - Role-specific technical concepts
   - Problem-solving approaches
   - System design discussions
   - Code review practices

5. Follow-up Guidance:
   - Thank you note templates
   - Post-interview communication
   - Negotiation strategies
   - Follow-up timeline advice"""

    if context_type == "interview_prep":
        base_prompt += """

When providing interview preparation:
1. First, ask about:
   - Specific role and company
   - Experience level (entry, mid, senior)
   - Interview stage and format
   - Any specific concerns

2. Then provide:
   - 3-5 most relevant practice questions
   - Structured answer frameworks
   - Role-specific preparation tips
   - Common pitfalls to avoid

3. For technical roles:
   - Include relevant technical concepts
   - Suggest practice problems
   - Provide system design discussion points
   - Recommend preparation resources"""

    if resume_text:
        base_prompt += "\nRESUME CONTENT:\n" + resume_text

    if cover_letter_text:
        base_prompt += "\nCOVER LETTER CONTENT:\n" + cover_letter_text

    if user_query:
        base_prompt += f"\nUSER QUERY: {user_query}"

    base_prompt += "\n\nPlease provide specific, actionable feedback based on the available information. Focus on concrete examples and clear recommendations for improvement."

    return base_prompt

def ask_openrouter(messages, max_tokens=500, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:1000",
        "X-Title": "AI Career Coach",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-3.5-turbo",  # Using a more reliable model
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        if 'choices' not in response_data or not response_data['choices']:
            print(f"OpenRouter API Response: {response_data}")  # Debug logging
            raise Exception("Invalid response format from OpenRouter API")
            
        return response_data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"OpenRouter API Error: {str(e)}")
        print(f"Full error details: {e.__dict__}")  # Debug logging
        return "I apologize, but I'm having trouble processing your request at the moment. Please try again."

def extract_text_from_pdf(file):
    """
    Extracts text from a PDF file.
    """
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_skill_recommendations(query):
    try:
        # Prepare the search query
        search_query = f"{query} courses tutorials books"
        
        # Set up the search parameters
        params = {
            "api_key": os.getenv('SERPAPI_KEY'),
            "engine": "google",
            "q": search_query,
            "num": 5  # Number of results to return
        }
        
        # Perform the search
        search = serpapi_client.search(params)
        results = search.get_dict()
        
        # Extract and format the recommendations
        recommendations = []
        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                recommendations.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        return recommendations
    except Exception as e:
        print(f"Error in get_skill_recommendations: {str(e)}")
        return []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Get the stored document texts from the session
        resume_text = session.get('resume_text', '')
        cover_letter_text = session.get('cover_letter_text', '')
        
        # Detect if this is an interview-related query
        interview_keywords = ['interview', 'interviewing', 'interviewer', 'hiring', 'recruit', 'meeting', 'technical question', 'behavioral question']
        is_interview_related = any(keyword in user_message.lower() for keyword in interview_keywords)
        
        # Create the career coach prompt with context
        prompt = create_career_coach_prompt(
            resume_text, 
            cover_letter_text, 
            user_message,
            context_type="interview_prep" if is_interview_related else None
        )
        
        # Store the role information if provided
        if is_interview_related and 'role' in user_message.lower():
            session['interview_role'] = user_message
        
        # Add role context if available
        if is_interview_related and 'interview_role' in session:
            prompt += f"\nPreviously mentioned interview role/context: {session.get('interview_role')}"
        
        response = ask_openrouter([
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ])
        
        ai_response = response
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"Error in /ask route: {str(e)}")
        return jsonify({"error": "Failed to get response"}), 500

@app.route("/upload", methods=["POST"])
def upload():
    try:
        resume_text = ""
        cover_letter_text = ""
        
        if 'resume' in request.files:
            resume_file = request.files['resume']
            resume_text = extract_text_from_pdf(resume_file)
            session['resume_text'] = resume_text
            
        if 'coverLetter' in request.files:
            cover_letter_file = request.files['coverLetter']
            cover_letter_text = extract_text_from_pdf(cover_letter_file)
            session['cover_letter_text'] = cover_letter_text
            
        # Create initial analysis prompt
        analysis_prompt = """Please provide an initial analysis of the submitted documents. Focus on:
1. Overall structure and presentation
2. Key strengths identified
3. Potential areas for improvement
4. Alignment with current job market trends
5. Specific recommendations for enhancement

If both resume and cover letter are provided, also comment on their consistency and complementary nature."""

        prompt = create_career_coach_prompt(resume_text, cover_letter_text, analysis_prompt)
        
        response = ask_openrouter([
            {"role": "system", "content": prompt},
            {"role": "user", "content": analysis_prompt}
        ])
        
        ai_response = response
        return jsonify({"response": ai_response})
    except Exception as e:
        print(f"Error in /upload route: {str(e)}")
        return jsonify({"error": "Failed to process documents"}), 500

@app.route("/prepare_interview", methods=["POST"])
def prepare_interview():
    try:
        data = request.get_json()
        role_info = data.get('role', '')
        interview_stage = data.get('stage', '')
        experience_level = data.get('experience', '')
        
        # Get any stored resume for context
        resume_text = session.get('resume_text', '')
        
        interview_prompt = f"""Based on the following information, provide a detailed interview preparation plan:

Role: {role_info}
Interview Stage: {interview_stage}
Experience Level: {experience_level}

Please provide:
1. A set of 5 most relevant interview questions for this role and stage, including:
   - Behavioral questions
   - Technical questions (if applicable)
   - Role-specific scenarios

2. For each question:
   - Explanation of why this question is important
   - Key points to cover in the answer
   - Example answer structure using the STAR method
   - Common pitfalls to avoid

3. Preparation checklist:
   - Key technical concepts to review
   - Industry knowledge to research
   - Company-specific preparation
   - Questions to ask the interviewer

4. Interview success tips:
   - Communication strategies
   - Body language and presentation
   - Virtual interview considerations (if applicable)
   - Follow-up protocol
"""

        # Add resume context if available
        if resume_text:
            interview_prompt += f"\nCandidate's Resume Context:\n{resume_text}"

        response = ask_openrouter([
            {"role": "system", "content": create_career_coach_prompt(context_type="interview_prep")},
            {"role": "user", "content": interview_prompt}
        ])
        
        ai_response = response
        
        # Store interview context for future reference
        session['interview_context'] = {
            'role': role_info,
            'stage': interview_stage,
            'experience': experience_level
        }
        
        return jsonify({
            "response": ai_response,
            "interview_context": session['interview_context']
        })
        
    except Exception as e:
        print(f"Error in /prepare_interview route: {str(e)}")
        return jsonify({"error": "Failed to prepare interview guidance"}), 500

@app.route("/recommend", methods=["POST"])
def recommend_skills():
    try:
        data = request.json
        query = data.get("query")
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Get recommendations from SerpAPI
        recommendations = get_skill_recommendations(query)
        
        if not recommendations:
            return jsonify({
                "error": "No recommendations found. Please try a different query."
            }), 404
        
        # Format the response
        response = {
            "recommendations": recommendations,
            "message": "Here are some resources to help you develop your skills:"
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/career_guidance", methods=["POST"])
def career_guidance():
    try:
        data = request.get_json()
        interests = data.get('interests', [])
        current_skills = data.get('skills', [])
        goals = data.get('goals', '')
        experience = data.get('experience', '')
        
        # Get stored resume for additional context
        resume_text = session.get('resume_text', '')
        
        guidance_prompt = f"""Based on the following information, provide detailed career path guidance:

User Profile:
Interests: {', '.join(interests)}
Current Skills: {', '.join(current_skills)}
Career Goals: {goals}
Experience Level: {experience}

Please provide:
1. Career Path Analysis:
   - Recommended career paths based on interests and skills
   - Growth potential and market demand
   - Typical career progression
   - Salary ranges and industry trends

2. For each recommended path:
   - Required skills and qualifications
   - Learning roadmap with specific milestones
   - Recommended certifications or education
   - Time estimates for career transitions

3. Skill Development Plan:
   - Core skills to develop
   - Advanced skills for specialization
   - Soft skills requirements
   - Learning resources and platforms

4. Action Items:
   - Immediate next steps
   - Short-term goals (3-6 months)
   - Medium-term goals (6-12 months)
   - Long-term career development (1-3 years)

5. Industry Insights:
   - Current market trends
   - Growing specializations
   - Industry challenges and opportunities
   - Networking recommendations
"""

        # Add resume context if available
        if resume_text:
            guidance_prompt += f"\nCandidate's Resume Context:\n{resume_text}"

        # Use SerpAPI to get relevant learning resources
        skills_to_search = interests + current_skills
        resources = []
        
        for skill in skills_to_search[:3]:  # Limit to top 3 skills to avoid rate limits
            try:
                search_results = serpapi_client.search({
                    "q": f"best {skill} courses certification learning resources",
                    "num": 5
                })
                
                if 'organic_results' in search_results:
                    resources.extend([{
                        'skill': skill,
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'snippet': result.get('snippet', '')
                    } for result in search_results['organic_results'][:2]])
            except Exception as e:
                print(f"Error fetching resources for {skill}: {str(e)}")

        # Add learning resources to the prompt
        if resources:
            guidance_prompt += "\n\nRelevant Learning Resources:\n"
            for resource in resources:
                guidance_prompt += f"\n{resource['skill']}:\n- {resource['title']}\n  {resource['link']}\n  {resource['snippet']}\n"

        response = ask_openrouter([
            {"role": "system", "content": create_career_coach_prompt(context_type="career_guidance")},
            {"role": "user", "content": guidance_prompt}
        ])
        
        ai_response = response
        
        # Store career guidance context for future reference
        session['career_context'] = {
            'interests': interests,
            'skills': current_skills,
            'goals': goals,
            'experience': experience
        }
        
        return jsonify({
            "response": ai_response,
            "career_context": session['career_context'],
            "resources": resources
        })
        
    except Exception as e:
        print(f"Error in /career_guidance route: {str(e)}")
        return jsonify({"error": "Failed to generate career guidance"}), 500

@app.route("/search_jobs", methods=["POST"])
def search_jobs():
    try:
        print("Starting job search...")  # Debug log
        data = request.get_json()
        role = data.get('role', '')
        location = data.get('location', '')
        experience = data.get('experience', '')
        job_type = data.get('jobType', '')
        
        print(f"Received search parameters: role={role}, location={location}, experience={experience}, job_type={job_type}")  # Debug log
        
        # Get stored resume for context
        resume_text = session.get('resume_text', '')
        
        # Construct search query
        search_query = f"{role} jobs"
        if location:
            search_query += f" in {location}"
        if experience:
            search_query += f" {experience} level"
        if job_type:
            search_query += f" {job_type}"
            
        print(f"Constructed search query: {search_query}")  # Debug log
        print(f"Using SerpAPI key: {os.getenv('SERPAPI_KEY')}")  # Debug log
            
        try:
            print("Initializing SerpAPI client...")  # Debug log
            client = GoogleSearch({
                "api_key": os.getenv('SERPAPI_KEY'),
                "engine": "google_jobs",  # Changed to google_jobs engine
                "q": search_query,
                "location": location if location else "United States",  # Added default location
                "chips": "date_posted:today",  # Show recent jobs
                "hl": "en"  # Set language to English
            })
            
            print("Executing search...")  # Debug log
            search_results = client.get_dict()
            print(f"Search results received: {json.dumps(search_results, indent=2)}")  # Debug log
            
            jobs = []
            if 'jobs_results' in search_results:  # Changed to jobs_results for google_jobs engine
                for result in search_results['jobs_results']:
                    jobs.append({
                        'title': result.get('title', ''),
                        'company': result.get('company_name', ''),
                        'location': result.get('location', ''),
                        'description': result.get('description', ''),
                        'link': result.get('link', ''),
                        'type': result.get('detected_extensions', {}).get('schedule_type', job_type) if job_type else 'Not specified',
                        'posted': result.get('detected_extensions', {}).get('posted_at', 'Recently'),
                        'salary': result.get('detected_extensions', {}).get('salary', 'Not specified'),
                        'highlights': result.get('job_highlights', [])
                    })

            print(f"Processed {len(jobs)} jobs")  # Debug log

            # Generate tailored application advice
            advice_prompt = f"""Based on the following job search results and user profile, provide tailored application advice:

Job Search: {search_query}
Number of Jobs Found: {len(jobs)}

Please provide:
1. Application Strategy:
   - Key points to emphasize in resume and cover letter
   - Skills alignment and how to demonstrate them
   - Company research tips
   - Application timeline recommendations

2. Resume Tailoring Tips:
   - Keywords to include
   - Relevant achievements to highlight
   - Format and structure suggestions
   - ATS optimization tips

3. Cover Letter Guidance:
   - Key points to address
   - Company-specific approaches
   - Value proposition examples
   - Follow-up strategies"""

            if resume_text:
                advice_prompt += f"\n\nCandidate's Resume Context:\n{resume_text}"

            print("Generating AI response...")  # Debug log
            response = ask_openrouter([
                {"role": "system", "content": create_career_coach_prompt(context_type="job_search")},
                {"role": "user", "content": advice_prompt}
            ])
            
            ai_response = response
            
            print("Sending response back to client...")  # Debug log
            return jsonify({
                "jobs": jobs,
                "advice": ai_response,
                "query": search_query
            })
            
        except Exception as e:
            print(f"SerpAPI Error: {str(e)}")
            print(f"Error details: {type(e).__name__}")  # Print error type
            import traceback
            print(f"Traceback: {traceback.format_exc()}")  # Print full traceback
            return jsonify({"error": f"Failed to fetch job listings: {str(e)}"}), 500
            
    except Exception as e:
        print(f"Error in /search_jobs route: {str(e)}")
        print(f"Error details: {type(e).__name__}")  # Print error type
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Print full traceback
        return jsonify({"error": f"Failed to process job search request: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=1000)
