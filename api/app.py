from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def convert(s):
    """Convert seconds to human readable format"""
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def get_bind_info(access_token):
    """Get bind information from Garena API"""
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    
    try:
        response = requests.get(url, params=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response
            email = data.get("email", "")
            email_to_be = data.get("email_to_be", "")
            countdown = data.get("request_exec_countdown", 0)
            
            result = {
                "status": "success",
                "status_code": response.status_code,
                "data": {
                    "current_email": email,
                    "pending_email": email_to_be,
                    "countdown_seconds": countdown,
                    "countdown_human": convert(countdown) if countdown > 0 else "0",
                    "raw_response": data
                },
                "summary": ""
            }
            
            # Create summary
            if email == "" and email_to_be != "":
                result["summary"] = f"Pending email confirmation: {email_to_be} - Confirms in: {convert(countdown)}"
            elif email != "" and email_to_be == "":
                result["summary"] = f"Email confirmed: {email}"
            elif email == "" and email_to_be == "":
                result["summary"] = "No recovery email set"
                
            return result
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "error": f"API returned status code: {response.status_code}",
                "response_text": response.text[:500] if response.text else "No response body"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "Request timeout (30 seconds)"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error": "Connection error - cannot reach Garena API"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": f"Request exception: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }

@app.route('/bind_info', methods=['GET'])
def bind_info_endpoint():
    """Endpoint to get bind information"""
    access_token = request.args.get('access_token')
    
    if not access_token:
        return jsonify({
            "status": "error",
            "error": "access_token parameter is required"
        }), 400
    
    result = get_bind_info(access_token)
    
    # Return appropriate status code based on result
    if result["status"] == "success":
        return jsonify(result), 200
    else:
        return jsonify(result), 400 if "status_code" in result and result["status_code"] == 400 else 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Garena Bind Info API",
        "version": "1.0"
    }), 200

@app.route('/')
def home():
    """Home page with API documentation"""
    return """
    <html>
        <head>
            <title>Garena Bind Info API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    border-bottom: 2px solid #4CAF50;
                    padding-bottom: 10px;
                }
                .endpoint {
                    background-color: #f9f9f9;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid #4CAF50;
                    border-radius: 4px;
                }
                code {
                    background-color: #eee;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: monospace;
                }
                .method {
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-weight: bold;
                    margin-right: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Garena Bind Info API</h1>
                <p>This API provides bind information for Garena accounts.</p>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <code>/bind_info</code></div>
                    <p><strong>Description:</strong> Get bind information for a Garena account</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>access_token</code> (required) - Garena access token</li>
                    </ul>
                    <p><strong>Example:</strong> <code>/bind_info?access_token=YOUR_ACCESS_TOKEN</code></p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> <code>/health</code></div>
                    <p><strong>Description:</strong> Health check endpoint</p>
                </div>
                
                <h2>Response Format</h2>
                <p>Successful response includes:</p>
                <ul>
                    <li><code>status</code>: "success" or "error"</li>
                    <li><code>data.current_email</code>: Current confirmed email</li>
                    <li><code>data.pending_email</code>: Pending email to be confirmed</li>
                    <li><code>data.countdown_seconds</code>: Countdown in seconds</li>
                    <li><code>data.countdown_human</code>: Human readable countdown</li>
                    <li><code>data.raw_response</code>: Raw API response from Garena</li>
                    <li><code>summary</code>: Human readable summary</li>
                </ul>
            </div>
        </body>
    </html>
    """, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)