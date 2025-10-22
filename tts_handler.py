import os
import base64
import wave
from google import genai
from google.genai import types
import ai_init

def synthesize_speech_with_gemini_to_wav(text: str, filename: str = "out.wav", voice_name: str = "Charon") -> str:
    """
    Gemini TTSモデルで音声を生成し、WAV形式で保存。
    :param text: 音声に変換するテキスト
    :param filename: 保存先ファイル名（.wav）
    :return: 保存されたファイルパス
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("APIキーが見つかりません。.envファイルに 'GEMINI_API_KEY' を設定してください。")

        client = genai.Client(api_key=api_key)

        gender = ai_init.current_persona_metadata.get("性別", "不明")

        if gender == "男性":
            voice_name = "Charon"
        elif gender == "女性":
            voice_name = "Sulafat"
        else:
            voice_name = "Fenrir"  # 不明の場合や中性的な声を使う

        response = client.models.generate_content(
            model="models/gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name  # 他に 'Breeze', 'Wave' など
                        )
                    )
                )
            )
        )

        # 音声データをbase64からデコード
        raw_data = response.candidates[0].content.parts[0].inline_data.data
        pcm_bytes = base64.b64decode(raw_data)

        # WAVファイルに書き出す（24000Hz, 16bit, モノラル）
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16bit = 2bytes
            wf.setframerate(24000)
            wf.writeframes(pcm_bytes)

        return filename

    except Exception as e:
        print(f"❌ 音声生成エラー: {e}")
        return None
