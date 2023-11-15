import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

def extract_episode_number(filename):
    """Extracts the episode number from the filename."""
    match = re.search(r'\d+', filename)
    return int(match.group()) if match else None

def add_page_header_footer(canvas, episode_number, margins):
    """Add a header and footer to the page."""
    width, height = letter
    canvas.drawString(margins['left'], height - margins['top'], f"Episode {episode_number}")
    canvas.drawString(margins['left'], margins['bottom'], f"Episode {episode_number}")

def wrap_text(text, width, canvas, font_name, font_size):
    """Wrap text to fit within the specified width."""
    wrapped_lines = []
    lines = text.split('\n')
    for line in lines:
        if line.strip() == "":
            wrapped_lines.append(line)
            continue
        words = line.split()
        current_line = ""
        for word in words:
            if stringWidth(current_line + word, font_name, font_size) <= width:
                current_line += word + " "
            else:
                wrapped_lines.append(current_line)
                current_line = word + " "
        wrapped_lines.append(current_line)  # Add the last line
    return wrapped_lines

def get_processed_episodes(log_file_path):
    """Read the log file to get a list of processed episode numbers."""
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            return set(file.read().splitlines())
    return set()

def update_log_file(log_file_path, episode_number):
    """Update the log file with a new processed episode number."""
    with open(log_file_path, 'a') as file:
        file.write(f"{episode_number}\n")

def read_file_content(file_path):
    """Reads the content of a file with multiple encoding attempts."""
    print(f"Reading file: {file_path}")  # Debugging print statement
    encodings = ['utf-8', 'ISO-8859-1', 'windows-1252', 'utf-16']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                print(f"Read {len(content)} characters from file.")  # Debugging print statement
                return content
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {file_path} with any known encoding.")

def create_pdf(transcripts, output_filename, margins, log_file_path):
    """Create a PDF file with an index and each episode, handling multi-page content."""
    processed_episodes = get_processed_episodes(log_file_path)
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter

    # Create index
    c.setFont("Helvetica-Bold", 14)
    y_position = height - margins['top'] - 60
    c.drawString(margins['left'], y_position, "Index of Episodes")
    y_position -= 16  # Spacing after the index title

    c.setFont("Helvetica", 12)
    for episode_number, _ in transcripts:
        if y_position <= margins['bottom'] + 30:
            c.showPage()
            y_position = height - margins['top'] - 60
            add_page_header_footer(c, episode_number, margins)  # Add header/footer for new index page
        index_entry = f"Episode {episode_number}"
        c.drawString(margins['left'], y_position, index_entry)
        y_position -= 14  # Spacing between index entries

    # Add a page break after the index
    c.showPage()

    # Process each transcript
    for episode_number, text in transcripts:
        if str(episode_number) in processed_episodes:
            continue  # Skip already processed episodes

        # Add header/footer for the first page of each episode
        add_page_header_footer(c, episode_number, margins)

        # Episode title
        c.setFont("Helvetica-Bold", 14)
        y_position = height - margins['top'] - 60
        c.drawString(margins['left'], y_position, f"Episode {episode_number}")
        y_position -= 14  # Spacing after title

        # Transcript text
        c.setFont("Helvetica", 12)
        wrapped_text = wrap_text(text, width - margins['left'] - margins['right'], c, "Helvetica", 12)
        for line in wrapped_text:
            if y_position <= margins['bottom'] + 30:
                c.showPage()
                y_position = height - margins['top'] - 60
                add_page_header_footer(c, episode_number, margins)  # Add header/footer for new transcript page
            c.drawString(margins['left'], y_position, line)
            y_position -= 14  # Spacing between lines

        # Update log file and add a page break after each episode
        update_log_file(log_file_path, str(episode_number))
        c.showPage()

    c.save()

# Set up the path to the 'transcribe' directory on your Desktop
transcribe_directory = os.path.join(os.path.expanduser('~'), 'Desktop', 'transcribe')

# Define the path for the log file within the 'transcribe' directory
log_file_path = os.path.join(transcribe_directory, 'processed_episodes.log')

# Path for the output PDF file
output_pdf = os.path.join(transcribe_directory, 'transcripts.pdf')

# Margins (in points; 1 point = 1/72 inch)
margins = {'left': 50, 'top': 50, 'bottom': 50, 'right': 50}

# Prepare the transcript data
transcripts = []
for filename in sorted(os.listdir(transcribe_directory), key=lambda f: int(extract_episode_number(f) or 0)):
    if filename.endswith('.txt'):
        episode_number = extract_episode_number(filename)
        if str(episode_number) in get_processed_episodes(log_file_path):
            print(f"Skipping processed episode: {episode_number}")  # Debugging print statement
            continue

        file_path = os.path.join(transcribe_directory, filename)
        file_content = read_file_content(file_path)
        print(f"Adding episode {episode_number} to transcripts.")  # Debugging print statement
        transcripts.append((episode_number, file_content))

# Create the PDF
create_pdf(transcripts, output_pdf, margins, log_file_path)

print("PDF created at:", output_pdf)
