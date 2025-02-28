document.addEventListener("DOMContentLoaded", function() {
    // DOM Elements
    const chatBox = document.querySelector(".chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const recommendBtn = document.getElementById("recommend-btn");
    const themeToggleBtn = document.getElementById("theme-toggle-btn");

    // Theme handling
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    themeToggleBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    });

    // Global variables for file handling
    let resumeFile = null;
    let coverLetterFile = null;

    function addMessage(message, type) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", type === "user" ? "user-message" : "ai-message");
        
        // Create a text node instead of using innerHTML or textContent
        const textNode = document.createTextNode(message);
        messageDiv.appendChild(textNode);
        
        // Preserve newlines by adding <br> elements
        messageDiv.style.whiteSpace = "pre-wrap";
        
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, "user");
        userInput.value = "";

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            addMessage(data.response, "ai");
        } catch (error) {
            console.error("Error:", error);
            addMessage("Sorry, there was an error processing your request.", "ai");
        }
    }

    async function getRecommendations() {
        const message = userInput.value.trim();
        if (!message) {
            addMessage("Please enter a skill or topic to get recommendations.", "ai");
            return;
        }

        addMessage(`Getting recommendations for: ${message}`, "user");
        userInput.value = "";

        try {
            const response = await fetch("/recommend", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query: message }),
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            addRecommendations(data.recommendations);
        } catch (error) {
            console.error("Error:", error);
            addMessage("Sorry, there was an error getting recommendations.", "ai");
        }
    }

    function addRecommendations(recommendations) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", "ai-message", "recommendations");
        messageDiv.style.whiteSpace = "pre-wrap";
        
        let content = "Here are some resources to help you develop your skills:\n\n";
        recommendations.forEach((rec, index) => {
            content += `${index + 1}. ${rec.title}\n`;
            if (rec.link) {
                content += `   Link: ${rec.link}\n`;
            }
            if (rec.snippet) {
                content += `   ${rec.snippet.trim()}\n`;
            }
            content += '\n';
        });
        
        const textNode = document.createTextNode(content);
        messageDiv.appendChild(textNode);
        
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function handleFileSelect(fileInput, previewId, fileType) {
        const file = fileInput.files[0];
        const preview = document.getElementById(previewId);
        
        if (file) {
            preview.textContent = `Selected ${fileType}: ${file.name}`;
            preview.classList.add('active');
            if (fileType === 'Resume') {
                resumeFile = file;
            } else {
                coverLetterFile = file;
            }
        } else {
            preview.textContent = '';
            preview.classList.remove('active');
            if (fileType === 'Resume') {
                resumeFile = null;
            } else {
                coverLetterFile = null;
            }
        }
        
        // Enable submit button if at least one file is selected
        document.getElementById('submitDocuments').disabled = !(resumeFile || coverLetterFile);
    }

    async function submitDocuments() {
        const formData = new FormData();
        if (resumeFile) formData.append('resume', resumeFile);
        if (coverLetterFile) formData.append('coverLetter', coverLetterFile);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            addMessage(data.response, 'ai');

            // Clear the file inputs and previews
            if (resumeFile) {
                document.getElementById('resume').value = '';
                document.getElementById('resume-preview').classList.remove('active');
                resumeFile = null;
            }
            if (coverLetterFile) {
                document.getElementById('coverLetter').value = '';
                document.getElementById('coverLetter-preview').classList.remove('active');
                coverLetterFile = null;
            }
            document.getElementById('submitDocuments').disabled = true;

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your documents. Please try again.', 'ai');
        }
    }

    async function prepareInterview() {
        const jobRole = document.getElementById('jobRole').value.trim();
        const interviewStage = document.getElementById('interviewStage').value;
        const experienceLevel = document.getElementById('experienceLevel').value;
        
        if (!jobRole || !interviewStage || !experienceLevel) {
            addMessage("Please fill in all interview preparation fields.", "ai");
            return;
        }
        
        addMessage(`Preparing interview guidance for ${jobRole} position...`, "ai");
        
        try {
            const response = await fetch('/prepare_interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    role: jobRole,
                    stage: interviewStage,
                    experience: experienceLevel
                })
            });
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            addMessage(data.response, "ai");
            
            // Clear form after successful submission
            document.getElementById('jobRole').value = '';
            document.getElementById('interviewStage').value = '';
            document.getElementById('experienceLevel').value = '';
            
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error preparing your interview guidance. Please try again.', 'ai');
        }
    }

    async function searchJobs() {
        const role = document.getElementById('searchJobRole').value.trim();
        const location = document.getElementById('searchJobLocation').value.trim();
        const experience = document.getElementById('searchJobExperience').value;
        const jobType = document.getElementById('searchJobType').value;
        
        // Add debug logging
        console.log('Job Search Form Data:', {
            role,
            location,
            experience,
            jobType
        });
        
        if (!role) {
            addMessage("Please enter a job role to search for.", "ai");
            return;
        }
        
        addMessage(`Searching for ${role} positions...`, "ai");
        
        try {
            const response = await fetch('/search_jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    role: role,
                    location: location,
                    experience: experience,
                    jobType: jobType
                })
            });
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display job results
            const jobResults = document.getElementById('jobResults');
            jobResults.innerHTML = '';
            
            if (data.jobs && data.jobs.length > 0) {
                displayJobs(data.jobs);
                
                // Add the application advice after the job listings
                if (data.advice) {
                    addMessage(data.advice, "ai");
                }
            } else {
                jobResults.innerHTML = '<div class="no-jobs">No jobs found matching your criteria. Try adjusting your search.</div>';
                addMessage("No jobs found matching your criteria. Try broadening your search or using different keywords.", "ai");
            }
            
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error searching for jobs. Please try again.', 'ai');
            
            // Clear the job results area on error
            const jobResults = document.getElementById('jobResults');
            jobResults.innerHTML = '';
        }
    }

    function displayJobs(jobs) {
        const jobsContainer = document.getElementById('jobResults');
        jobsContainer.innerHTML = ''; // Clear previous results

        if (jobs.length === 0) {
            jobsContainer.innerHTML = '<p>No jobs found. Try adjusting your search criteria.</p>';
            return;
        }

        jobs.forEach(job => {
            const jobCard = document.createElement('div');
            jobCard.className = 'job-card';
            
            // Create highlights HTML if available
            let highlightsHtml = '';
            if (job.highlights && job.highlights.length > 0) {
                highlightsHtml = job.highlights.map(highlight => {
                    if (highlight.title && highlight.items) {
                        return `
                            <div class="job-highlight">
                                <h4>${highlight.title}</h4>
                                <ul>
                                    ${highlight.items.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                        `;
                    }
                    return '';
                }).join('');
            }

            jobCard.innerHTML = `
                <h3 class="job-title">${job.title}</h3>
                <div class="job-company">${job.company}</div>
                <div class="job-meta">
                    <span class="job-location">${job.location}</span>
                    <span class="job-type">${job.type}</span>
                    <span class="job-posted">${job.posted}</span>
                </div>
                ${job.salary ? `<div class="job-salary">${job.salary}</div>` : ''}
                <div class="job-description">${job.description}</div>
                ${highlightsHtml ? `<div class="job-highlights">${highlightsHtml}</div>` : ''}
                <div class="job-actions">
                    <a href="${job.link}" target="_blank" class="job-apply-btn">View Job →</a>
                </div>
            `;
            
            jobsContainer.appendChild(jobCard);
        });
    }

    // Tag Input System
    class TagInput {
        constructor(inputId, containerId) {
            this.input = document.getElementById(inputId);
            this.container = document.getElementById(containerId);
            this.tags = new Set();
            
            this.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addTag();
                }
            });
        }
        
        addTag() {
            const value = this.input.value.trim();
            if (value && !this.tags.has(value)) {
                this.tags.add(value);
                this.createTagElement(value);
                this.input.value = '';
            }
        }
        
        createTagElement(value) {
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.innerHTML = `${value}<span class="tag-remove">×</span>`;
            
            tag.querySelector('.tag-remove').addEventListener('click', () => {
                this.tags.delete(value);
                tag.remove();
            });
            
            this.container.appendChild(tag);
        }
        
        getTags() {
            return Array.from(this.tags);
        }
        
        clear() {
            this.tags.clear();
            this.container.innerHTML = '';
            this.input.value = '';
        }
    }

    // Initialize tag inputs
    const interestTags = new TagInput('interestInput', 'interestTags');
    const skillTags = new TagInput('skillInput', 'skillTags');

    async function getCareerGuidance() {
        const interests = interestTags.getTags();
        const skills = skillTags.getTags();
        const goals = document.getElementById('careerGoals').value.trim();
        const experience = document.getElementById('careerExperience').value;
        
        // Add debug logging
        console.log('Career Guidance Form Data:', {
            interests,
            skills,
            goals,
            experience
        });
        
        if (!goals || !experience) {
            addMessage("Please fill in your career goals and experience level.", "ai");
            return;
        }
        
        if (interests.length === 0) {
            addMessage("Please add at least one career interest.", "ai");
            return;
        }
        
        if (skills.length === 0) {
            addMessage("Please add at least one current skill.", "ai");
            return;
        }
        
        addMessage("Analyzing your profile and generating career guidance...", "ai");
        
        try {
            const response = await fetch('/career_guidance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    interests: interests,
                    skills: skills,
                    goals: goals,
                    experience: experience
                })
            });
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            addMessage(data.response, "ai");
            
            // Clear form after successful submission
            interestTags.clear();
            skillTags.clear();
            document.getElementById('careerGoals').value = '';
            document.getElementById('careerExperience').value = '';
            
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error generating career guidance. Please try again.', 'ai');
        }
    }

    // Event Listeners
    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter") sendMessage();
    });
    recommendBtn.addEventListener("click", getRecommendations);

    // File upload event listeners
    document.getElementById('resume').addEventListener('change', function() {
        handleFileSelect(this, 'resume-preview', 'Resume');
    });

    document.getElementById('coverLetter').addEventListener('change', function() {
        handleFileSelect(this, 'coverLetter-preview', 'Cover Letter');
    });

    document.getElementById('submitDocuments').addEventListener('click', submitDocuments);
    document.getElementById('prepareInterview').addEventListener('click', prepareInterview);
    document.getElementById('getCareerGuidance').addEventListener('click', getCareerGuidance);
    document.getElementById('searchJobs').addEventListener('click', searchJobs);
});