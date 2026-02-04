"""
Bias Detector Node

Wraps the BiasDetector tool in a LangGraph node.
"""


from src.tools import BiasDetector


def bias_detector_node(state: dict) -> dict:
    """
    LangGraph node: Detect potential biases in screening

    Ensures fair and ethical hiring practices.
    """
    print("="*80)
    print("BIAS DETECTOR - FAIRNESS ANALYSIS")
    print("="*80 + "\n")

    detector = BiasDetector()

    bias_analysis = detector.analyze_bias(
        state["candidates"],
        state["ranked_candidates"],
        state["job_requirements"]
    )

    # Print summary
    print(f"Bias Score: {bias_analysis['bias_score']:.1f}/100 (lower is better)")
    print(f"Fairness Assessment: {bias_analysis['fairness_assessment']}")

    if bias_analysis['detected_biases']:
        print(f"\nDetected {len(bias_analysis['detected_biases'])} potential biases:")
        for bias in bias_analysis['detected_biases'][:3]:
            print(f"  - {bias['type']} (Severity: {bias['severity']})")
    else:
        print("\nNo significant biases detected")

    print()

    return {
        "bias_analysis": bias_analysis,
        "current_step": "bias_detection_complete"
    }


# Test
if __name__ == "__main__":
    print("Testing bias detector node...")

    # Mock state
    state = {
        "candidates": [
            {
                "name": "Alice",
                "total_experience_months": 72,
                "education": [{"institution": "MIT", "degree": "BS"}]
            }
        ],
        "ranked_candidates": [
            {
                "rank": 1,
                "candidate_score": {
                    "candidate_name": "Alice",
                    "total_score": 90,
                    "recommendation": "Strong Match"
                }
            }
        ],
        "job_requirements": {
            "job_title": "Engineer",
            "job_description": "Looking for energetic digital native",
            "experience": {"minimum_years": 5}
        }
    }

    result = bias_detector_node(state)
    print("\nBias analysis complete")
    print(f"Result keys: {list(result.keys())}")
