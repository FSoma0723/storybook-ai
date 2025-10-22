import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel

model = None
chat_session = None
current_persona_and_situation_for_display = "（まだキャラクター設定なし）"
current_persona_metadata = {}  # TTSの声種などで参照

def initialize_ai():
    """
    APIキーを読み込み、Geminiモデルを初期化する関数。
    アプリ起動時に一度だけ呼び出すことを想定。
    """
    global model
    load_dotenv() # .envファイルから環境変数を読み込む
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("APIキーが環境変数 'GEMINI_API_KEY' に見つかりません。")
        
        genai.configure(api_key=api_key)
        
        # 使用するGeminiモデルを準備 (例: 'gemini-2.0-flash')
        model = genai.GenerativeModel('gemini-2.0-flash') 
        print("Gemini AIモデルが正常に初期化されました。") # ターミナルでの確認用
        return True

    except Exception as e:
        print(f"Gemini AIの初期化中にエラーが発生しました: {e}") # ターミナルでの確認用
        model = None
        return False
