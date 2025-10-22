from PIL import Image
import google.generativeai as genai
from persona_extractor import generate_persona_and_situation_from_image
from utils import format_persona_dict_for_display
import ai_init

def get_ai_response(user_prompt: str, image_data: Image.Image = None):
    """
    ユーザーのプロンプトと任意で画像データを受け取り、AIからの応答を返す関数。
    画像が提供された場合、新しいペルソナと状況を設定してチャットを開始する。
    """
    
    if ai_init.model is None:
        return "AIモデルが初期化されていません。まずAIを初期化してください。"

    new_persona_set_this_turn = False 

    if image_data:
        print(f"新しい画像 ({type(image_data)}) が提供されました。ペルソナと状況を評価します。")
        persona_dict = generate_persona_and_situation_from_image(image_data)  # dictを受け取る
        generated_persona_and_situation_text = format_persona_dict_for_display(persona_dict)  # 表示用文字列
        
        if "エラー：" in generated_persona_and_situation_text:
            ai_init.current_persona_and_situation_for_display = "キャラクター情報と状況を画像から取得できませんでした。"
            return f"画像からキャラクター情報や状況を取得できませんでした。AIは以前のキャラクター（またはデフォルト）として応答します。\n詳細: {generated_persona_and_situation_text}"
        
        elif "人間のキャラクターなし" in generated_persona_and_situation_text or "見当たらないみたいだね" in generated_persona_and_situation_text: 
            ai_init.current_persona_and_situation_for_display = "（この絵には人間がいません。状況のみ説明可能）" 
            print("画像から特定の人間キャラクターが見つからなかったため、デフォルトの応答モード（または状況説明モード）になります。")
            default_system_prompt = "あなたは親切でフレンドリーなAIアシスタントです。子供からのメッセージに、絵本のキャラクターになったつもりで楽しく応答してください。もしキャラクターがいなくても、絵の状況について話すことができます。常に優しく、子供の想像力を広げるような会話を心がけてください。"
            ai_init.chat_session = ai_init.model.start_chat(history=[
                {'role': 'user', 'parts': [default_system_prompt]},
                {'role': 'model', 'parts': ["はい、こんにちは！この絵にはお話しできる人間のキャラクターはいないみたいだけど、絵の中の様子について何かお話ししようか！"]}
            ])
            new_persona_set_this_turn = True
        
        else: 
            ai_init.current_persona_and_situation_for_display = generated_persona_and_situation_text
            
            # ★追加：AIが理解した「現在の状況」部分をターミナルに具体的に表示
            situation_text_start_keyword = "--- 現在の状況 ---"
            situation_info_for_log = "（状況情報は抽出されませんでした）" 
            if situation_text_start_keyword in generated_persona_and_situation_text:
                situation_info_for_log = generated_persona_and_situation_text.split(situation_text_start_keyword, 1)[1].strip()
            
            print("\n----------------------------------------------------")
            print("AIが現在の状況を以下のように理解（または設定）しました：")
            print(situation_info_for_log)
            print("----------------------------------------------------\n")

            system_instruction_for_chat = f"""あなたは、以下の情報に基づいて設定された絵本の「人間のキャラクター」です。
あなたは現在、記述されている「現在の状況」の中にいます。
子供からのメッセージに対して、このキャラクターになりきり、かつ現在の状況も踏まえて応答してください。
返答は1~3文程度に抑え、テンポよく会話してください。一貫性を保ち、子供が楽しめるような会話を心がけてください。常にポジティブで、優しく、子供の想像力を刺激するような言葉遣いをしてください。
例えば、もし周囲に他のキャラクター（人間以外も含む）がいるなら、そのキャラクターについて触れたり、一緒に行動していることを話したりできます。絵の中の場所や雰囲気も会話に取り入れてください。

--- あなたのキャラクター設定と現在の状況 ---
{generated_persona_and_situation_text} 
--- 設定と状況ここまで ---

それでは、子供からのメッセージに応答の準備をしてください。
子供が話しかけてきたら、このキャラクターとして、現在の状況も意識しながら自然に会話を始めてください。
"""
            ai_init.chat_session = ai_init.model.start_chat(history=[
                {'role': 'user', 'parts': [system_instruction_for_chat]},
                {'role': 'model', 'parts': ["はい、わかりました！このキャラクターになりきって、今の状況も考えながらお話しする準備ができました！"]}
            ])
            new_persona_set_this_turn = True
            # ★変更点：ターミナルログに表示する情報を増やす（状況も含むペルソナ全体）
            print(f"新しい「人間」ペルソナと状況でチャットセッションを開始しました。設定内容:\n{ai_init.current_persona_and_situation_for_display}\n---")

        if new_persona_set_this_turn and not user_prompt:
             first_greeting_prompt_after_setting = ""
             if "人間のキャラクターなし" not in ai_init.current_persona_and_situation_for_display and "エラー：" not in ai_init.current_persona_and_situation_for_display:
                 first_greeting_prompt_after_setting = f"（システム：{ai_init.current_persona_and_situation_for_display.splitlines()[0]} として挨拶してください）こんにちは！"
             else:
                 first_greeting_prompt_after_setting = "この絵について何かお話ししようか？"
             try:
                 print(f"ペルソナ/状況設定後の最初の挨拶を生成します: {first_greeting_prompt_after_setting}")
                 response = ai_init.chat_session.send_message(first_greeting_prompt_after_setting)
                 return response.text
             except Exception as e:
                 print(f"AIのペルソナ/状況設定後の挨拶生成中にエラー: {e}")
                 return f"AIの挨拶生成中にエラーが発生しました: {e}"
                 
    if ai_init.chat_session is None:
        print("チャットセッションが存在しないため、デフォルトのセッションを開始します。")
        default_system_prompt = "あなたは親切でフレンドリーなAIアシスタントです。子供からのメッセージに、絵本のキャラクターになったつもりで楽しく応答してください。特定のキャラクター設定はありませんが、常に優しく、子供の想像力を広げるような会話を心がけてください。"
        ai_init.chat_session = ai_init.model.start_chat(history=[
            {'role': 'user', 'parts': [default_system_prompt]},
            {'role': 'model', 'parts': ["はい、こんにちは！何でも聞いてね！一緒にお話しできるのを楽しみにしているよ。"]}
        ])
        ai_init.current_persona_and_situation_for_display = "フレンドリーなAIアシスタント（特定のキャラクターや状況設定なし）"
        print("デフォルトのチャットセッションを開始しました。")

    try:
        if not user_prompt:
            return "何かお話ししたいことを入力してね！"
        print(f"現在のチャットセッションにメッセージを送信します: '{user_prompt[:50]}...'")
        response = ai_init.chat_session.send_message(user_prompt)
        return response.text
    except Exception as e:
        print(f"AIからの応答取得中にエラーが発生しました: {e}")
        return f"AIからの応答取得中にエラーが発生しました: {e}"
    
def get_current_persona_and_situation_description():
    """UI表示用に現在のペルソナ・状況説明を返す関数"""
    return ai_init.current_persona_and_situation_for_display    
