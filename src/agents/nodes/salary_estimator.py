"""
Salary Estimator Node

Wraps the SalaryEstimator tool in a LangGraph node.
"""


from src.tools import SalaryEstimator


def salary_estimator_node(state: dict) -> dict:
    """
    LangGraph node: Estimate salary ranges for candidates

    Provides compensation benchmarking for hiring decisions.
    """
    print("="*80)
    print("SALARY ESTIMATOR - COMPENSATION ANALYSIS")
    print("="*80 + "\n")

    estimator = SalaryEstimator()

    salary_estimates = {}

    for candidate_data in state["candidates"]:
        candidate_name = candidate_data.get("name", "Unknown")

        print(f"  Estimating salary for {candidate_name}...")

        estimate = estimator.estimate_salary(
            candidate_data,
            state["job_requirements"]
        )

        salary_estimates[candidate_name] = estimate

        median = estimate["adjusted_range"]["median"]
        print(f"  Median estimate: ${median:,}")

    print(f"\nSalary estimation complete for {len(salary_estimates)} candidates\n")

    return {
        "salary_estimates": salary_estimates,
        "current_step": "salary_estimation_complete"
    }


# Test
if __name__ == "__main__":
    print("Testing salary estimator node...")

    # Mock state
    state = {
        "candidates": [
            {
                "name": "Alice",
                "total_experience_years": 6,
                "technical_skills": ["Python", "TensorFlow"],
                "location": "San Francisco, CA",
                "education": [{"degree": "Master"}]
            }
        ],
        "job_requirements": {
            "job_title": "Senior ML Engineer",
            "job_description": "Build ML systems for fintech"
        }
    }

    result = salary_estimator_node(state)
    print("\nSalary estimation complete")

    for name, estimate in result["salary_estimates"].items():
        print(f"\n{name}:")
        print(f"  Range: ${estimate['adjusted_range']['min']:,} - ${estimate['adjusted_range']['max']:,}")
        print(f"  Confidence: {estimate['confidence']:.0%}")
