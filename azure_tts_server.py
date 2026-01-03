"""
Azure TTS Server for Lithuanian Language
Provides high-quality Lithuanian text-to-speech
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import azure.cognitiveservices.speech as speechsdk
import os
import base64
import uvicorn

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
    voice: str = "lt-LT-LeonasNeural"  # Male voice
    # Alternative: "lt-LT-OnaNeural" for female voice
    rate: str = "0%"  # Speech rate: -50% to +100%
    pitch: str = "0%"  # Pitch: -50% to +50%

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize Lithuanian speech from text
    
    Available Lithuanian voices:
    - lt-LT-LeonasNeural (Male)
    - lt-LT-OnaNeural (Female)
    """
    try:
        # Get Azure credentials from environment
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        service_region = os.getenv("AZURE_SPEECH_REGION", "westeurope")
        
        print(f"🔑 API Key present: {bool(speech_key)}")
        print(f"🌍 Region: {service_region}")
        print(f"🎤 Voice: {request.voice}")
        print(f"📝 Text length: {len(request.text)} chars")
        
        if not speech_key:
            print("❌ ERROR: Azure Speech Key not configured!")
            raise HTTPException(
                status_code=500,
                detail="Azure Speech Key not configured. Please set AZURE_SPEECH_KEY in .env file"
            )
        
        # Configure speech synthesis
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region
        )
        
        # Set output format
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        
        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )
        
        # Create SSML for better control
        ssml = f"""
        <speak version='1.0' xml:lang='lt-LT'>
            <voice name='{request.voice}'>
                <prosody rate='{request.rate}' pitch='{request.pitch}'>
                    {request.text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Synthesize speech
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Convert audio to base64
            audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
            
            print(f"✅ Successfully synthesized {len(result.audio_data)} bytes of audio")
            
            return {
                "success": True,
                "audio_base64": audio_base64,
                "format": "mp3",
                "sample_rate": 16000,
                "voice": request.voice
            }
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech synthesis canceled: {cancellation.reason}"
            if cancellation.error_details:
                error_msg += f" - Details: {cancellation.error_details}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ TTS error: {str(e)}")
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
    """Health check"""
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    return {
        "status": "healthy",
        "azure_configured": bool(speech_key)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)