import streamlit as st
from ai_init import initialize_ai
from chat_manager import get_ai_response, get_current_persona_and_situation_description
from tts_handler import synthesize_speech_with_gemini_to_wav
from PIL import Image
import io
import os
import tempfile
import whisper
from audio_recorder_streamlit import audio_recorder
import ast

# --- AIの初期化 ---
if "ai_initialized" not in st.session_state:
    st.session_state.ai_initialized = False

if not st.session_state.ai_initialized:
    if initialize_ai():
        st.session_state.ai_initialized = True
    else:
        st.error("AIの初期化に失敗しました。環境変数 'GEMINI_API_KEY' やAPIキーの有効性を確認してください。")
        st.stop()

# --- StreamlitアプリのUI設定 ---
st.title("絵本キャラクターAIチャット")
st.caption("画像をアップロードすると、AIがその絵の「人間」のキャラクターになりきり、状況も理解してお話しします。")

if "intro_played" not in st.session_state:
    st.session_state.intro_played = False

if not st.session_state.intro_played:
    with open("narration/intro_narration.wav", "rb") as f:
        audio_bytes = f.read()
    st.audio(audio_bytes, format="audio/wav", autoplay=True)
    st.session_state.intro_played = True

# --- 会話履歴の管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 送信待ちの画像（Pillow Imageオブジェクト）の状態管理 ---
if "image_to_process_on_send" not in st.session_state:
    st.session_state.image_to_process_on_send = None 
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "uploader_key_suffix" not in st.session_state:
    st.session_state.uploader_key_suffix = 0
if "camera_key_suffix" not in st.session_state:
    st.session_state.camera_key_suffix = 0

# --- 画像アップロードとプレビューエリア ---
# --- 画像アップロード or カメラ撮影エリア ---
with st.container():
    st.markdown("##### ステップ1: キャラクターになってほしい「人間」と「その状況」が描かれた絵本のページを選択")
    
    uploaded_file_obj = st.file_uploader("画像ファイルを選択（任意）", type=["jpg", "jpeg", "png"],key=f"file_uploader_{st.session_state.get('uploader_key_suffix', 0)}"
)
    camera_image_obj = st.camera_input("またはカメラで撮影",
    key=f"camera_input_{st.session_state.camera_key_suffix}")

    pil_image = None
    file_name = None

    if uploaded_file_obj is not None:
        try:
            image_bytes = uploaded_file_obj.getvalue()
            pil_image = Image.open(io.BytesIO(image_bytes))
            file_name = uploaded_file_obj.name
            
            if "mic_guide_played" not in st.session_state:
                with open("narration/mic_guide_narration.wav", "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/wav", autoplay=True)
                st.session_state.mic_guide_played = True
                
        except Exception as e:
            st.error(f"アップロード画像の読み込みに失敗しました: {e}")

    elif camera_image_obj is not None:
        try:
            image_bytes = camera_image_obj.getvalue()
            pil_image = Image.open(io.BytesIO(image_bytes))
            file_name = "captured_from_camera.jpg"
            
            if "mic_guide_played" not in st.session_state:
                with open("narration/mic_guide_narration.wav", "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/wav", autoplay=True)
                st.session_state.mic_guide_played = True
        except Exception as e:
            st.error(f"カメラ画像の読み込みに失敗しました: {e}")

    if pil_image:
        st.session_state.image_to_process_on_send = pil_image
        st.session_state.uploaded_file_name = file_name
        st.success(f"画像「{file_name}」が選択されました。下のチャット欄から話しかけてみましょう！")

        col1_img, col2_btn = st.columns([0.8, 0.2])
        with col1_img:
            st.image(pil_image, caption=f"選択中の画像: {file_name}", width=200)
        with col2_btn:
            if st.button("この画像をクリア", key="clear_image_button_main"):
                st.session_state.image_to_process_on_send = None
                st.session_state.uploaded_file_name = None
                st.session_state.uploader_key_suffix = st.session_state.get('uploader_key_suffix', 0) + 1
                st.session_state.camera_key_suffix = st.session_state.camera_key_suffix + 1
                st.rerun()

st.divider()

# --- 現在のAIキャラクター・状況表示 ---
current_persona_info_for_ui = get_current_persona_and_situation_description()
if current_persona_info_for_ui:
    lines = current_persona_info_for_ui.splitlines()
    display_text = lines[0] 
    situation_summary = ""
    for line in lines:
        if "場所：" in line or "雰囲気：" in line: 
            situation_summary += f" ({line.split('：', 1)[1].strip()})" if '：' in line else f" ({line.strip()})"
            break 
    
    if "エラー：" in display_text or "（" in display_text: 
        st.info(f"AIの現在の状態: {display_text}")
    else:
        char_name_part = display_text.split("名前：",1)[-1].splitlines()[0].strip() if "名前：" in display_text else display_text.strip()
        st.info(f"AIは現在「{char_name_part}」として応答しようとしています。{situation_summary}")


# --- ★修正点②: これまでの会話履歴を画面に表示（音声も含む） ---
st.subheader("ステップ2: 会話してみよう！")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image_data_for_ui"): 
            st.image(message["image_data_for_ui"], width=200, caption="あなたが送信した画像")
        if message.get("text_content"):
            st.markdown(message["text_content"])
        # ★追加: メッセージに音声データがあれば再生ボタンを表示
        if message.get("audio_data"):
            st.audio(message["audio_data"], format="audio/wav", autoplay=True)
st.markdown("---")


# --- ユーザーからの新しいメッセージ入力を受け付け ---
user_input_text = st.chat_input("キャラクターに話しかけてみよう...", key="chat_input_main_text")

if user_input_text:
    # ユーザーのメッセージを履歴に追加
    user_message_data_for_ui = {"role": "user", "text_content": user_input_text}
    image_to_send_to_ai = st.session_state.get("image_to_process_on_send", None)
    
    if image_to_send_to_ai:
        user_message_data_for_ui["image_data_for_ui"] = image_to_send_to_ai
    
    st.session_state.messages.append(user_message_data_for_ui)
    
    # AIの応答を取得
    ai_response_text = get_ai_response(user_prompt=user_input_text, image_data=image_to_send_to_ai)

    # --- ★修正点①: AIの応答と音声を履歴に追加 ---
    assistant_message_data = {"role": "assistant", "text_content": ai_response_text}
  
    # 音声生成してファイルに保存
    wav_path = synthesize_speech_with_gemini_to_wav(ai_response_text, filename="latest_output.wav")
    
    # 音声ファイルが正常に生成されたら、その中身を読み込んでメッセージデータに追加
    if wav_path and os.path.exists(wav_path):
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()
        assistant_message_data["audio_data"] = audio_bytes

    # テキストと音声データを含むAIのメッセージを履歴に追加
    st.session_state.messages.append(assistant_message_data)
    
    # このターンでペルソナ設定に画像を使った場合、次のターンでは画像なしで会話を続けられるようにクリア
    if image_to_send_to_ai:
        st.session_state.image_to_process_on_send = None
        st.session_state.uploaded_file_name = None
        st.session_state.uploader_key_suffix = st.session_state.get('uploader_key_suffix', 0) + 1
        st.session_state.camera_key_suffix = st.session_state.camera_key_suffix + 1
    st.rerun()


# --- 🎤 音声入力で会話するエリア ---
# --- 🎤 マイクで話しかけるエリア ---
st.markdown("#### 🎤 マイクで話しかける")
# マイク録音ボタン（WAVデータが返る）
audio_bytes = audio_recorder()
if st.button("Save Recording"):
    if audio_bytes is None:
        st.error("まだ録音されていません。")
    else:
        with open("recorded_audio.wav", "wb") as f:
            f.write(audio_bytes)
        st.success("Recording saved!")
    model = whisper.load_model("small")
    result = model.transcribe("recorded_audio.wav")
    voice_input_text=(result["text"])

    # 👇 ここからはテキスト入力と同じ処理
    user_message_data_for_ui = {"role": "user", "text_content": voice_input_text}
    image_to_send_to_ai = st.session_state.get("image_to_process_on_send", None)

    if image_to_send_to_ai:
        user_message_data_for_ui["image_data_for_ui"] = image_to_send_to_ai

    st.session_state.messages.append(user_message_data_for_ui)

    ai_response_text = get_ai_response(user_prompt=voice_input_text, image_data=image_to_send_to_ai)

    assistant_message_data = {"role": "assistant", "text_content": ai_response_text}

    wav_path = synthesize_speech_with_gemini_to_wav(ai_response_text, filename="latest_output.wav")
    if wav_path and os.path.exists(wav_path):
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()
        assistant_message_data["audio_data"] = audio_bytes
        

    st.session_state.messages.append(assistant_message_data)

    if image_to_send_to_ai:
        st.session_state.image_to_process_on_send = None
        st.session_state.uploaded_file_name = None
        st.session_state.uploader_key_suffix = st.session_state.get('uploader_key_suffix', 0) + 1
        st.session_state.camera_key_suffix = st.session_state.camera_key_suffix + 1
    st.rerun()
