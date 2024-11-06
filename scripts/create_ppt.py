import win32com.client

def create_presentation():
    # Start PowerPoint application
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True

    # Create a new presentation
    presentation = powerpoint.Presentations.Add()

    # Add a slide
    slide = presentation.Slides.Add(1, 1)  # 1 = ppLayoutText

    # Add title and subtitle
    slide.Shapes.Title.TextFrame.TextRange.Text = "Hello, PowerPoint!"
    slide.Shapes.Placeholders(2).TextFrame.TextRange.Text = "This is a subtitle."

    # Save the presentation
    presentation.SaveAs(r"C:\path\to\your\new_presentation.pptx")

if __name__ == "__main__":
    create_presentation()
