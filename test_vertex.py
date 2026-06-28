import google.auth
from google import genai

try:
    credentials, project = google.auth.default()
    print("Project:", project)
    client = genai.Client(vertexai=True, project=project, location='us-central1')
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents='Say hello world'
    )
    print("Vertex AI Response:", response.text)
except Exception as e:
    print("Error:", e)
