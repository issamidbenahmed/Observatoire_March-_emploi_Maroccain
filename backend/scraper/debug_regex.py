import re

markdown = """
- [![Agent Commercial](https://www.marocannonces.com/user_images/309/5194336.jpg)\\ 
\\
**Agent Commercial** Casablanca](https://www.marocannonces.com/categorie/309/Offres-emploi/annonce/10287843/Agent-Commercial.html "Agent Commercial")
"""

# We want to match the whole thing as one job link.
# Pattern: [ ![alt](img) **Title** City ](URL)
# Note that [ ![alt](img) is two [ [.
pattern = r'\[\s*!\[.*?\]\(.*?\).*?(\*\*.*?\*\*.*?)\s*\]\((.*?/annonce/.*?)\)'

match = re.search(pattern, markdown, re.DOTALL)
if match:
    print(f"Match found!")
    print(f"Title Part: {match.group(1)}")
    print(f"URL: {match.group(2)}")
else:
    print("No match found.")
