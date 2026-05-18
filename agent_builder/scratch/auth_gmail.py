import os
import sys
import urllib.parse
import json
import pickle
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from google.oauth2.credentials import Credentials

sys.path.append(os.path.abspath('/Users/apple/Downloads/team  quintsync/agent_builder'))

CLIENT_ID = "28793115317-24o8qhh8mj5cskhqc7k10sn2vi9af0g6.apps.googleusercontent.com"
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/oauth/gmail/callback"
SCOPE = "https://www.googleapis.com/auth/gmail.send"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/oauth/gmail/callback'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'error' in params:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<h1>Error!</h1><p>Auth denied.</p>")
                return
                
            code = params.get('code', [None])[0]
            if code:
                # Exchange code for token
                data = {
                    'code': code,
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'grant_type': 'authorization_code'
                }
                response = requests.post('https://oauth2.googleapis.com/token', data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    creds = Credentials(
                        token=token_data.get('access_token'),
                        refresh_token=token_data.get('refresh_token'),
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        scopes=[SCOPE]
                    )
                    with open('gmail_token.pickle', 'wb') as token:
                        pickle.dump(creds, token)
                        
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<h1>Success!</h1><p>Gmail is now authenticated. You can close this window.</p>")
                    print("\n\n✅ Gmail Auth Success! Token saved to gmail_token.pickle")
                    
                    # Run the test script
                    try:
                        import subprocess
                        print("\nRunning email test...")
                        subprocess.Popen([sys.executable, "scratch/auto_email_linkedin.py"])
                    except Exception as e:
                        print("Failed to run test:", e)
                        
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f"<h1>Error exchanging token</h1><p>{response.text}</p>".encode())
            
            # Shut down server
            def kill_me_please():
                self.server.server_close()
                sys.exit(0)
            import threading
            threading.Timer(1, kill_me_please).start()
            
def run_auth():
    if not CLIENT_SECRET:
        print("ERROR: GMAIL_CLIENT_SECRET not found in .env")
        return
        
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_type=code&scope={urllib.parse.quote(SCOPE)}&access_type=offline&prompt=consent"
    
    print("\n" + "="*80)
    print("👉 CLICK THIS URL TO AUTHORIZE:")
    print(auth_url)
    print("="*80 + "\n")
    print("Waiting for you to click the link and authorize...")
    
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    server.serve_forever()

if __name__ == '__main__':
    run_auth()
