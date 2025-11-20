class MockLLMClientExperiment:
    """
    This is a experiment class, I amtrying to test if I can replace an LLM call with simple heuristic functions
    to classify ticket description into summary, category and severity.
    """
    @staticmethod
    def _classify_category(description: str) -> str:
        """
        classify a ticket description into categories based on word heuristic
        """
        text = description.lower()

        # Category heuristic
        if any(w in text for w in ["charge", "billing", "invoice", "payment"]):
            category = "Billing"
        elif any(w in text for w in ["login", "signin", "sign-in", "password", "authentication"]):
            category = "Login"
        elif any(w in text for w in ["slow", "lag", "performance", "timeout"]):
            category = "Performance"
        elif any(w in text for w in ["how do i", "how to", "can i", "is it possible"]):
            category = "Question/How-To"
        elif any(w in text for w in ["crash", "error", "bug", "exception", "500", "404", "429"]):
            category = "Bug"
        else:
            category = "Other"

        return category
    
    @staticmethod
    def _classify_severity(description: str) -> str:
        """
        classify a ticket description into severity based on word heuristic
        """
        text = description.lower()

        # Severity heuristic
        if any(w in text for w in ["data loss", "security", "breach", "cannot access", "down", "unavailable"]):
            severity = "Critical"
        elif any(w in text for w in ["crash", "500", "not working", "fails", "error"]):
            severity = "High"
        elif any(w in text for w in ["slow", "sometimes", "intermittent", "occasionally"]):
            severity = "Medium"
        else:
            severity = "Low"

        return severity
    
    @staticmethod
    def _generate_summary(description: str) -> str:
        """
        generate a brief summary from the ticket description
        """
        summary = description.strip()
        if len(summary) > 120:
            summary = summary[:117].rsplit(" ", 1)[0] + "..."
        return summary

def mock_experiment():
    """
    A mock experiment function to classify ticket description into summary, category and severity.
    """
    descriptions = [
        "I am unable to login to my account since yesterday. It says incorrect password even though I am sure it's correct.",
        "My application crashes with a 500 error whenever I try to upload a file larger than 5MB.",
        "How do I change my billing information? I want to update my credit card details.",
        "The system is very slow and sometimes times out when I try to access my dashboard.",
        "I think there is a security breach in my account as I noticed some unauthorized transactions."
    ]
    
    for description in descriptions:
        summary = MockLLMClientExperiment._generate_summary(description)
        category = MockLLMClientExperiment._classify_category(description)
        severity = MockLLMClientExperiment._classify_severity(description)
        print(f"Description: {description}")
        print(f"Summary: {summary}")
        print(f"Category: {category}")
        print(f"Severity: {severity}")
        print("-" * 50, "\n")

if __name__ == "__main__":
    mock_experiment("")
    
"""
RESULT OF THE EXPERIMENT RUN:

Description: I am unable to login to my account since yesterday. It says incorrect password even though I am sure it's correct.
Summary: I am unable to login to my account since yesterday. It says incorrect password even though I am sure it's correct.
Category: Login
Severity: Low
-------------------------------------------------- 

Description: My application crashes with a 500 error whenever I try to upload a file larger than 5MB.
Summary: My application crashes with a 500 error whenever I try to upload a file larger than 5MB.
Category: Bug
Severity: High
-------------------------------------------------- 

Description: How do I change my billing information? I want to update my credit card details.
Summary: How do I change my billing information? I want to update my credit card details.
Category: Billing
Severity: Low
-------------------------------------------------- 

Description: The system is very slow and sometimes times out when I try to access my dashboard.
Summary: The system is very slow and sometimes times out when I try to access my dashboard.
Category: Performance
Severity: Medium
-------------------------------------------------- 

Description: I think there is a security breach in my account as I noticed some unauthorized transactions.
Summary: I think there is a security breach in my account as I noticed some unauthorized transactions.
Category: Other
Severity: Critical
-------------------------------------------------- 
"""