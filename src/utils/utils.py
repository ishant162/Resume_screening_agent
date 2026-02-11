def extract_response_text(response):
    """
    Cleans and extracts the usable text content from a response object.
    Steps performed:
      - Strip whitespace
      - Remove markdown code fences: ```json ... ``` or generic ```
      - Return the cleaned text
    """
    response_text = response.content.strip()

    # Remove markdown code block with json
    if "```json" in response_text:
        # Split by ```json then split by next ```
        try:
            response_text = (
                response_text.split("```json", 1)[1].split("```", 1)[0].strip()
            )
        except IndexError:
            pass  # Leave original text if split fails

    # Remove generic code blocks
    elif "```" in response_text:
        try:
            response_text = response_text.split("```", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            pass

    return response_text.strip()
