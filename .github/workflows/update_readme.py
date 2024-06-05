from openai import OpenAI
from dotenv import load_dotenv
import instructor
from pydantic import BaseModel
import os
from typing import List
from datetime import datetime


load_dotenv()

# Variables
model = "gpt-3.5-turbo"
md_output = "README.md"
directory = '.'


# Pydantic Classes for structured data
class MarkdownSummary(BaseModel):
    title: str
    description: str
    tags: List[str]


class FullMarkdownSummary(MarkdownSummary):
    path: str


# Functions
def list_markdown_files(directory):
    """Lists all markdown files in the given directory, excluding README.md."""
    markdown_files = [f for f in os.listdir(directory) if f.endswith('.md') and f != 'README.md']
    return markdown_files


def read_markdown_file(file_path):
    """Reads the contents of a Markdown file and returns it as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    return ""


def generate_summary(markdown_content):
    client = instructor.from_openai(OpenAI())

    prompt = f"""
    Given the following content, extract the title and provide a 1-2 sentence summary of the content. Make sure it is easily understandble what somebody will find in the content.

    {markdown_content}

    Respond in JSON format with the fields:
    - "title": The title of the content.
    - "description": A brief 1-2 sentence summary of the content.
    - "tags": A list of relevant/generalized tags or keywords for the content, e.g. ["recipes", "vegan", "cooking"]. Make sure they are general enough to be useful for search purposes.
    """

    # Extract structured data from natural language
    response = client.chat.completions.create(
        model=model,
        response_model=MarkdownSummary,
        messages=[
                {"role": "system", "content": "You are knowledge management expert tasked with providing high quality summaries of content. Don't start with 'this content...' or 'in this file'... Formulate in active voice like 'Collection of recipes for vegan dishes, including X,Y,Z'."},
                {"role": "user", "content": prompt}
            ],
        max_tokens=150,
        temperature=0.5,
    )
    return response


def generate_markdown(summaries: List[FullMarkdownSummary], output_file: str):
    """Generate a formatted markdown file from a list of FullMarkdownSummary instances."""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("# Stuff worth Bookmarking\n\n")

        for summary in summaries:
            # Use the path to create a hyperlink for the title
            file.write(f"## [{summary.title}]({summary.path})\n\n")
            file.write(f"{summary.description}\n\n")
            if summary.tags:
                file.write("**Tags:** " + ", ".join(summary.tags) + "\n\n")
            file.write("---\n\n")

        # Add a disclaimer at the bottom
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write("---\n\n")
        file.write("**Disclaimer:**\n\n")
        file.write(f"This summary was automatically created by {model}. Last updated on {last_updated}.\n")

    print(f"Markdown file '{output_file}' has been created successfully at {last_updated}")


def main():
    # List all markdown files in the directory
    markdown_files = list_markdown_files(directory)
    summaries = []

    # Generate summaries for each markdown file
    for file in markdown_files:
        file_path = os.path.join(directory, file)
        markdown_content = read_markdown_file(file_path)
        if markdown_content:
            response = generate_summary(markdown_content)
            # Create FullMarkdownSummary instance with the file path
            full_summary = FullMarkdownSummary(
                **response.dict(),
                path=file_path
            )
            summaries.append(full_summary)

    # Generate a summary markdown file
    generate_markdown(summaries, md_output)


if __name__ == "__main__":
    main()
