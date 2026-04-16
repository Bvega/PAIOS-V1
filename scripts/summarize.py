def summarize_text(content, max_lines=3):
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    if not lines:
        return "No content available for summary."

    summary_lines = lines[:max_lines]
    return "\n".join(summary_lines)