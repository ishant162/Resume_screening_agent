# Job Analysis Prompt
JOB_ANALYSIS_PROMPT = """
    You are an expert recruiter analyzing a job description.

    Job Description:
    {job_description}

    Extract and structure the following information:
    1. Job title and basic details
    2. Required technical skills (categorize as must-have vs nice-to-have)
    3. Experience requirements (years, domains, role types)
    4. Education requirements
    5. Soft skills
    6. Certifications (if any)
    7. Key responsibilities

    Return a structured JSON matching this format:
    {{
        "job_title": "...",
        "technical_skills": [
            {{"name": "Python", "priority": "must_have", "years_required": 3}},
            {{"name": "React", "priority": "nice_to_have"}}
        ],
        "experience": {{
            "minimum_years": 3,
            "preferred_years": 5,
            "specific_domains": ["AI", "Machine Learning"]
        }},
        "education": {{
            "minimum_degree": "Bachelor",
            "fields_of_study": ["Computer Science", "Related Field"]
        }},
        "soft_skills": ["communication", "teamwork"],
        "responsibilities": ["...", "..."]
    }}

    Be precise and thorough.
"""

# Resume Parsing Prompt
RESUME_PARSING_PROMPT = """
    You are an expert at parsing resumes.

    Resume Text:
    {resume_text}

    Extract and structure the following information:
    1. Personal information (name, email, phone, LinkedIn, GitHub)
    2. Professional summary
    3. Technical skills (list all programming languages, frameworks, tools)
    4. Work experience (company, position, dates, responsibilities,
        technologies used)
    5. Education (institution, degree, field, dates)
    6. Projects (name, description, technologies)
    7. Certifications

    Return structured JSON matching this format:
    {{
        "name": "...",
        "email": "...",
        "phone": "...",
        "technical_skills": ["Python", "TensorFlow", "..."],
        "work_experience": [
            {{
                "company": "...",
                "position": "...",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",  // null if current
                "responsibilities": ["...", "..."],
                "technologies": ["Python", "AWS"]
            }}
        ],
        "education": [
            {{
                "institution": "...",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "end_year": 2019
            }}
        ]
    }}

    Be thorough and accurate.
"""

# Skill Matching Prompt
SKILL_MATCHING_PROMPT = """
    You are an expert technical recruiter with deep knowledge of software engineering skills, their equivalents, and transferability.

    **Job Required Skills:**

    Must-Have Skills: {must_have_skills}
    Nice-to-Have Skills: {nice_to_have_skills}

    **Candidate Profile:**
    Name: {candidate_name}
    Skills: {candidate_skills}
    Total Experience: {total_experience} years
    Recent Projects: {recent_projects}

    **Your Task:**
    Perform an intelligent skill match analysis. Consider:
    1. Exact skill matches
    2. Similar/equivalent technologies (e.g., PyTorch ≈ TensorFlow, React ≈ Vue, PostgreSQL ≈ MySQL)
    3. Transferable skills (e.g., Java developer can pick up Kotlin easily)
    4. Depth of experience vs requirements
    5. Project context that demonstrates practical skill application

    **Analysis Required:**

    1. **Matched Must-Have Skills**: Which required must-have skills does the candidate possess? Include equivalent/similar skills (e.g., if job needs TensorFlow but candidate has PyTorch, that's a match with a note).

    2. **Missing Must-Have Skills**: Which critical must-have skills are they lacking? No equivalents found.

    3. **Matched Nice-to-Have Skills**: Which bonus skills do they have from the nice-to-have list?

    4. **Missing Nice-to-Have Skills**: Which nice-to-have skills are missing?

    5. **Additional Skills**: What relevant skills do they bring that weren't in the job description but add value?

    6. **Match Percentages**: 
    - Calculate must-have match percentage (0-100): (matched / total must-have) * 100
    - Calculate nice-to-have match percentage (0-100): (matched / total nice-to-have) * 100
    - Calculate overall skill score: (must_have_pct * 0.8) + (nice_to_have_pct * 0.2)

    7. **Skill Gap Analysis** (3-4 sentences): Provide detailed analysis covering:
    - Their strongest technical areas relative to this specific job
    - Most critical skill gaps and potential impact on job performance
    - Transferable skills or related experience that could help bridge gaps
    - Overall technical readiness assessment and learning curve estimate

    **Important**: Be fair and recognize skill equivalents. Don't penalize candidates for having PyTorch when TensorFlow was requested, or React when Vue was listed.

    Return ONLY a JSON object in this exact format (no markdown, no extra text):
    {{
        "matched_must_have": ["skill1", "skill2"],
        "missing_must_have": ["skill3"],
        "matched_nice_to_have": ["skill4"],
        "missing_nice_to_have": ["skill5"],
        "additional_skills": ["skill6", "skill7"],
        "must_have_match_percentage": 85.5,
        "nice_to_have_match_percentage": 60.0,
        "overall_skill_score": 79.4,
        "skill_gap_analysis": "Detailed 3-4 sentence analysis here covering strengths, gaps, transferability, and readiness..."
    }}
"""

# Interview Questions Prompt
INTERVIEW_QUESTIONS_PROMPT = """
    Generate personalized interview questions for this candidate.

    Candidate: {candidate_name}

    Job Requirements:
    {job_requirements}

    Candidate Profile:
    {candidate_profile}

    Generate 10-12 questions:
    1. 3-4 technical questions based on required skills
    2. 2-3 questions to probe skill gaps
    3. 2-3 behavioral questions based on their experience
    4. 2-3 questions about specific projects/achievements

    Make questions specific and practical.
"""

WORK_EXPERIENCE_RELEVANCE_PROMPT = """
    You are an expert recruiter analyzing work experience relevance.

    **Target Role:** {job_title}

    **Role Requirements:**
    - Required domains: {required_domains}
    - Role types: {role_types}
    - Key responsibilities: {key_responsibilities}

    **Candidate Work History:**
    {work_summary}

    **Total Experience:** {total_experience_years} years

    **Task:**
    Analyze how much of this experience is **directly relevant** to the target role.

    Consider:
    1. Direct domain matches (same industry/field)
    2. Transferable experience (similar responsibilities, adjacent domains)
    3. Technology/skill overlap
    4. Role level and complexity

    Return your analysis in this JSON format:
    {{
        "relevant_years": <float: estimated years of relevant experience>,
        "domain_match": <boolean: true if worked in similar domains>,
        "relevant_domains": [<list of relevant domain names from their history>],
        "relevance_reasoning": "<2-3 sentence explanation of what makes their experience relevant or not>"
    }}

    Be realistic but fair. Give credit for transferable skills.
"""

CAREER_PROGRESSION_ANALYSIS_PROMPT = """
    You are an expert career counselor analyzing career progression.

    **Target Role:** {job_title} (seeking this role)

    **Candidate's Career History (chronological):**
    {work_summary}

    **Task:**
    Analyze this person's career trajectory and progression.

    Consider:
    1. Role level progression (junior → mid → senior → lead/principal)
    2. Increasing scope of responsibility
    3. Skill development and specialization
    4. Industry/domain moves (pivots or deepening)
    5. Trajectory alignment with target role

    Return your analysis in JSON format:
    {{
        "has_progression": <boolean: true if clear upward/positive trajectory>,
        "trajectory": "<one of: 'upward', 'lateral', 'specialist', 'pivot', 'early-career', 'stagnant'>",
        "progression_reasoning": "<3-4 sentences explaining the career pattern and how it positions them for the target role>",
        "readiness_for_role": "<assessment of whether their trajectory prepared them for this role>"
    }}

    Be insightful and constructive.
"""

EXPERIENCE_ASSESSMENT_PROMPT = """
    You are an expert recruiter writing an experience assessment for hiring managers.

    **Candidate:** {candidate_name}
    **Target Role:** {job_title}
    **Required Experience:** {required_years}+ years
    **Candidate's Total Experience:** {total_years} years

    **Relevance Analysis:**
    {relevance_reasoning}
    - Relevant Years: {relevant_years} years
    - Domain Match: {domain_match}

    **Career Progression Analysis:**
    {progression_reasoning}
    - Trajectory: {trajectory}
    - Readiness: {readiness_for_role}

    **Task:**
    Write a comprehensive 4-5 sentence experience assessment that:
    1. Summarizes their experience quantity and quality
    2. Highlights relevant experience and domain fit
    3. Discusses career progression and readiness
    4. Provides an honest bottom-line assessment

    Be professional, balanced, and specific. This will be read by hiring managers.

    **Assessment:**
"""

EDUCATION_VERIFICATION_PROMPT = """
    You are an expert education verifier for technical hiring.

    **Job Requirements:**
    - Minimum Degree: {minimum_degree}
    - Preferred Degree: {preferred_degree}
    - Field(s) of Study: {fields_of_study}
    - Required: {degree_required}

    **Candidate:** {candidate_name}
    **Total Experience:** {total_experience_years} years

    **Education:**
    {education_summary}

    **Certifications:**
    {cert_summary}

    **Task:**
    Verify if this candidate meets the education requirements with intelligent assessment.

    **Consider:**
    1. **Degree Equivalency:** BTech/BE = BS/Bachelor, MTech = MS/Master, etc.
    2. **Global Degrees:** Recognize international degrees (Indian BTech, UK Honours, etc.)
    3. **Field Relevance:** Is their field applicable? (e.g., Physics/Math for ML, EE for AI)
    4. **Alternative Qualifications:** Can strong certifications + experience compensate?
    5. **Experience Substitution:** Can 5+ years of experience substitute for missing degree?

    Return JSON:
    {{
        "meets_requirement": <boolean: true if requirements are met or reasonably satisfied>,
        "field_match": <boolean: true if field of study is relevant>,
        "degree_level_match": "<exact_match | equivalent | below | above>",
        "relevant_coursework": [<list any relevant coursework mentioned>],
        "compensating_factors": [<list factors that compensate for any gaps, like experience or certs>],
        "analysis": "<4-5 sentences providing nuanced assessment of their education qualifications>"
    }}

    Be fair and recognize that strong experience can sometimes compensate for formal education gaps, especially in tech.
"""

FINAL_CANDIDATE_ASSESSMENT_PROMPT = """
    You are an expert recruiter providing a final holistic assessment of a candidate.

    **Position:** {job_title}

    **Candidate:** {candidate_name}
    **Overall Score:** {overall_score}/100

    **Component Scores:**
    - Skills: {skills_score}% (Weight: {skills_weight}%)
    - Must-have match: {must_have_match}%
    - Missing critical: {missing_must_have}
    
    - Experience: {experience_score}% (Weight: {experience_weight}%)
    - Years: {total_years} (Required: {required_years})
    - Trajectory: {career_trajectory}
    
    - Education: {education_score}% (Weight: {education_weight}%)
    - Degree: {highest_degree}
    - Meets req: {meets_education_requirement}

    **Individual Analyses:**

    Skills:
    {skill_gap_analysis}

    Experience:
    {experience_analysis}

    Education:
    {education_analysis}

    **Task:**
    Provide a comprehensive final assessment in JSON format:

    {{
        "strengths": [
            "<3-5 bullet points of key strengths>",
            "Be specific and reference concrete evidence"
        ],
        "concerns": [
            "<2-4 bullet points of concerns or gaps>",
            "Be honest but constructive"
        ],
        "red_flags": [
            "<0-2 bullet points of serious concerns that could disqualify>",
            "Only include if truly critical, otherwise empty list"
        ],
        "detailed_analysis": "<4-5 sentence executive summary synthesizing all aspects. Provide a clear hiring recommendation with reasoning.>"
    }}

    Be balanced, specific, and actionable. This will be read by hiring managers making final decisions.
"""

CANDIDATE_RANKING_EXPLANATION_PROMPT = """
    You are a recruiter explaining candidate rankings to a hiring manager.

    **This Candidate:** {candidate_name} (Rank #{rank} of {total_candidates})
    - Total Score: {total_score}%
    - Recommendation: {recommendation}
    - Key Strengths: {key_strengths}
    - Key Concerns: {key_concerns}

    **Nearby Rankings:**
    {context}

    **Task:**
    In 2-3 sentences, explain why this candidate ranks #{rank}. What specifically makes them stronger or weaker than nearby candidates? Be specific and comparative.

    **Comparative Analysis:**
"""

EXECUTIVE_CANDIDATE_SUMMARY_PROMPT = """
You are an executive recruiter writing a summary for hiring managers.

**Position:** {job_title}
**Candidates Screened:** {candidates_screened}

**Top 3 Candidates:**
{top_candidates_summary}

**Task:**
Write a 3-4 sentence executive summary that:
1. States how many candidates were screened
2. Highlights the quality of the top candidates
3. Notes any common strengths or concerns across the pool
4. Provides a bottom-line recommendation on next steps

Be concise, professional, and actionable.

**Executive Summary:**
"""

INTERVIEW_QUESTION_GENERATION_PROMPT = """
    You are an expert technical interviewer preparing questions for a candidate.

    **Position:** {job_title}

    **Candidate:** {candidate_name}

    **Candidate Profile:**
    - Skills: {candidate_skills}
    - Experience: {total_experience_years} years
    - Education: {highest_education}
    - Recent Work:
    {work_summary}

    **Assessment Results:**
    - Overall Score: {overall_score}%
    - Skills Match: {skills_match_score}%
    - Missing Critical Skills: {missing_critical_skills}
    - Career Trajectory: {career_trajectory}

    **Key Strengths:**
    {key_strengths}

    **Key Concerns:**
    {key_concerns}

    **Task:**
    Generate 12-15 personalized interview questions covering these categories:

    1. **Technical Skills (4-5 questions):**
    - Test their claimed skills with practical scenarios
    - Focus on skills critical to the role
    - Include at least one question about each must-have skill

    2. **Skill Gaps (2-3 questions):**
    - Assess missing skills without being harsh
    - Explore related/transferable skills
    - Ask how quickly they could learn gaps

    3. **Experience Deep-Dive (3-4 questions):**
    - Probe specific projects they mentioned
    - Understand their actual contributions
    - Assess problem-solving approach

    4. **Behavioral/Cultural Fit (2-3 questions):**
    - Based on their career trajectory
    - Team collaboration style
    - Learning agility

    Make questions:
    - Specific to THEIR background (reference their actual experience)
    - Open-ended (not yes/no)
    - Practical and scenario-based
    - Progressive in difficulty

    Return as a JSON list of strings:
    [
    "Question 1 text here",
    "Question 2 text here",
    ...
    ]
"""