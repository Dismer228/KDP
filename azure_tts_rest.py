"""
Azure TTS using REST API instead of SDK
This works perfectly in Docker without library issues!
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import base64
import uvicorn

app = FastAPI(title="Azure Lithuanian TTS - REST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "lt-LT-LeonasNeural"
    rate: str = "0%"
    pitch: str = "0%"

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize Lithuanian speech using Azure REST API
    No SDK required - works perfectly in Docker!
    """
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
        
        print(f"🔑 API Key present: {bool(speech_key)}")
        print(f"🌍 Region: {service_region}")
        print(f"🎤 Voice: {request.voice}")
        print(f"📝 Text: {request.text}")
        
        if not speech_key:
            raise HTTPException(
                status_code=500,
                detail="AZURE_SPEECH_KEY not configured"
            )
        
        # Azure TTS REST API endpoint
        endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        
        # Prepare headers
        headers = {
            "Ocp-Apim-Subscription-Key": speech_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
            "User-Agent": "Lithuanian-TTS-Service"
        }
        
        # Create SSML
        ssml = f"""<speak version='1.0' xml:lang='lt-LT'>
            <voice name='{request.voice}'>
                <prosody rate='{request.rate}' pitch='{request.pitch}'>
                    {request.text}
                </prosody>
            </voice>
        </speak>"""
        
        print(f"📡 Calling Azure API: {endpoint}")
        
        # Call Azure REST API
        response = requests.post(
            endpoint,
            headers=headers,
            data=ssml.encode('utf-8'),
            timeout=30
        )
        
        if response.status_code == 200:
            # Convert audio to base64
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            
            print(f"✅ Successfully synthesized {len(response.content)} bytes of audio")
            
            return {
                "success": True,
                "audio_base64": audio_base64,
                "format": "mp3",
                "sample_rate": 16000,
                "voice": request.voice
            }
        else:
            error_msg = f"Azure API error {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=response.status_code, detail=error_msg)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/voices")
async def get_available_voices():
    """Get available Lithuanian voices"""
    return {
        "voices": [
            {
                "name": "lt-LT-LeonasNeural",
                "gender": "Male",
                "language": "Lithuanian",
                "description": "Natural-sounding male Lithuanian voice"
            },
            {
                "name": "lt-LT-OnaNeural",
                "gender": "Female",
                "language": "Lithuanian",
                "description": "Natural-sounding female Lithuanian voice"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    return {
        "status": "healthy",
        "azure_configured": bool(speech_key),
        "method": "REST API (no SDK)"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🎤 Azure Lithuanian TTS - REST API Version")
    print("="*60)
    
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
    
    if key:
        masked = key[:8] + "..." + key[-4:]
        print(f"✅ API Key: {masked}")
        print(f"✅ Region: {region}")
        print(f"✅ Method: REST API (SDK-free)")
    else:
        print("❌ AZURE_SPEECH_KEY not set!")
    
    print("\nStarting server on http://localhost:5003")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5003)