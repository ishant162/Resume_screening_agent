"""
Resume Screening Agent - LangGraph Workflow

This module defines the complete workflow for automated resume screening.
"""

from langgraph.graph import StateGraph, END
from src.state.state import AgentState
from src.agents.nodes import (
    job_analyzer_node,
    resume_parser_node,
    skill_matcher_node,
    experience_analyzer_node,
    education_verifier_node,
    scorer_node,
    report_generator_node,
    question_generator_node,
)


def create_screening_graph() -> StateGraph:
    """
    Create the resume screening workflow graph
    
    Workflow:
    1. Analyze job description
    2. Parse all resumes
    3. Match skills against requirements
    4. Analyze experience
    5. Verify education
    6. Score and rank candidates
    7. Generate comprehensive report
    8. Generate interview questions
    
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Initialize the graph with our state schema
    workflow = StateGraph(AgentState)
    
    # Add all nodes to the graph
    workflow.add_node("job_analyzer", job_analyzer_node)
    workflow.add_node("resume_parser", resume_parser_node)
    workflow.add_node("skill_matcher", skill_matcher_node)
    workflow.add_node("experience_analyzer", experience_analyzer_node)
    workflow.add_node("education_verifier", education_verifier_node)
    workflow.add_node("scorer", scorer_node)
    workflow.add_node("report_generator", report_generator_node)
    workflow.add_node("question_generator", question_generator_node)
    
    # Define the workflow edges (node → node connections)
    
    # Start with job analysis
    workflow.set_entry_point("job_analyzer")
    
    # Linear workflow
    workflow.add_edge("job_analyzer", "resume_parser")
    workflow.add_edge("resume_parser", "skill_matcher")
    workflow.add_edge("skill_matcher", "experience_analyzer")
    workflow.add_edge("experience_analyzer", "education_verifier")
    workflow.add_edge("education_verifier", "scorer")
    workflow.add_edge("scorer", "report_generator")
    workflow.add_edge("report_generator", "question_generator")
    
    # End after question generation
    workflow.add_edge("question_generator", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def visualize_graph(output_path: str = "workflow_diagram.png"):
    """
    Visualize the workflow graph (optional, requires graphviz)
    
    Args:
        output_path: Path to save the diagram
    """
    try:
        app = create_screening_graph()
        
        # Get the graph representation
        graph_image = app.get_graph().draw_mermaid_png()
        
        with open(output_path, "wb") as f:
            f.write(graph_image)
        
        print(f"✅ Graph visualization saved to {output_path}")
        
    except Exception as e:
        print(f"⚠️  Could not generate graph visualization: {e}")
        print("This is optional. Install graphviz if you want visualizations.")


# For testing: simple graph execution
if __name__ == "__main__":
    print("Creating resume screening graph...")
    
    app = create_screening_graph()
    
    print("✅ Graph created successfully!")
    print("\nGraph structure:")
    print("  START")
    print("    ↓")
    print("  1. Job Analyzer")
    print("    ↓")
    print("  2. Resume Parser")
    print("    ↓")
    print("  3. Skill Matcher")
    print("    ↓")
    print("  4. Experience Analyzer")
    print("    ↓")
    print("  5. Education Verifier")
    print("    ↓")
    print("  6. Scorer & Ranker")
    print("    ↓")
    print("  7. Report Generator")
    print("    ↓")
    print("  8. Question Generator")
    print("    ↓")
    print("  END")
    
    # Try to visualize
    print("\nAttempting to create workflow diagram...")
    visualize_graph()