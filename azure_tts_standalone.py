"""
Standalone Azure TTS Server - Run directly on Windows (no Docker needed)
Install: pip install fastapi uvicorn azure-cognitiveservices-speech
Run: python azure_tts_standalone.py
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import azure.cognitiveservices.speech as speechsdk
import os
import base64
import uvicorn

# Load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

app = FastAPI(title="Azure Lithuanian TTS")

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
    """Synthesize Lithuanian speech from text"""
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
                detail="AZURE_SPEECH_KEY not set. Set it with: $env:AZURE_SPEECH_KEY='your-key'"
            )
        
        # Configure speech
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        
        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )
        
        # Create SSML
        ssml = f"""
        <speak version='1.0' xml:lang='lt-LT'>
            <voice name='{request.voice}'>
                <prosody rate='{request.rate}' pitch='{request.pitch}'>
                    {request.text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Synthesize
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
            print(f"✅ Successfully synthesized {len(result.audio_data)} bytes")
            
            return {
                "success": True,
                "audio_base64": audio_base64,
                "format": "mp3",
                "sample_rate": 16000,
                "voice": request.voice
            }
        else:
            cancellation = result.cancellation_details
            error_msg = f"Speech synthesis canceled: {cancellation.reason}"
            if cancellation.error_details:
                error_msg += f" - {cancellation.error_details}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.get("/voices")
async def get_available_voices():
    """Get available Lithuanian voices"""
    return {
        "voices": [
            {
                "name": "lt-LT-LeonasNeural",
                "gender": "Male",
                "language": "Lithuanian"
            },
            {
                "name": "lt-LT-OnaNeural",
                "gender": "Female",
                "language": "Lithuanian"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    return {
        "status": "healthy",
        "azure_configured": bool(speech_key)
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🎤 Azure Lithuanian TTS Server")
    print("="*60)
    
    # Check environment
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
    
    if key:
        masked = key[:8] + "..." + key[-4:]
        print(f"✅ API Key: {masked}")
        print(f"✅ Region: {region}")
    else:
        print("❌ AZURE_SPEECH_KEY not set!")
        print("\nSet it in PowerShell:")
        print('  $env:AZURE_SPEECH_KEY="your-key-here"')
        print('  $env:AZURE_SPEECH_REGION="westeurope"')
        print("\nOr create a .env file with:")
        print("  AZURE_SPEECH_KEY=your-key-here")
        print("  AZURE_SPEECH_REGION=westeurope")
    
    print("\nStarting server on http://localhost:5003")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5003)