from google.genai import types
import google.generativeai as genai
from PIL import Image
import re
from utils import parse_output_to_dict
import ai_init

def generate_persona_and_situation_from_image(image_data: Image.Image):
    """
    画像データから、対話可能な「人間」のキャラクターのペルソナ情報と、
    そのキャラクターが置かれている「状況」をAIに生成させる関数。
    該当するキャラクターがいない場合は、その旨を返す。
    """
    if ai_init.model is None:
        return "エラー：AIモデルが初期化されていません。"

    prompt = """この画像を見て、「指を指されているキャラクター」を特定してください。
もし、そのような「人間のキャラクター」が1体以上見つかった場合は、そのうちの最も目立つ1体について、以下の情報を抽出・推測し、子供向けの絵本のキャラクターとして設定してください。
以下の形式で、各項目を具体的に、子供にも分かりやすい言葉で記述してください。

--- キャラクター情報 ---
- 名前（もし推測できれば。難しければ「不明」または愛称を提案）：
- 性別（外見から判断して男性/女性/不明のいずれか）：
- 見た目の特徴（例：髪の色、服装、表情、年齢層など、人間としての特徴）：
- 性格（表情やポーズ、絵の雰囲気から推測）：
- 話しそうな口調や語尾（例：「～だよ！」「～かしら？」など）：
- 子供たちに対する役割や目的（例：一緒に遊ぶ友達、物語の案内役、お兄さん・お姉さんのような存在など）：

--- 現在の状況 ---
- 場所（例：森の中、部屋の中、公園など、絵から分かる範囲で）：
- 周囲にいる他の人物や動物、重要な物（もしあれば、誰が/何があって、どんな様子か簡潔に）：
- キャラクターの主な行動や状態（例：遊んでいる、何かを見つめている、困っている、楽しそうに笑っているなど）：
- 絵全体の雰囲気（例：明るく楽しい、静かで穏やか、少し不思議な感じなど）：

全体的に、子供が親しみやすく、ポジティブで、優しい印象を持つように記述してください。

もし、画像内に上記のような「主要な人間のキャラクター」が明確に見当たらない場合（例：動物のみ、風景のみ、無生物のオブジェクトのみ、人間以外のキャラクターのみ、抽象的な絵など）は、無理にキャラクター情報を生成せず、代わりに「人間のキャラクターなし」というキーワードを含む短いメッセージ（例：「この絵には、お話しできそうな人間のキャラクターは見当たらないみたいだね。」）を返してください。
"""
    try:
        print("AIに画像からのペルソナ及び状況生成（人間限定）をリクエストします...")
        response = ai_init.model.generate_content([prompt, image_data])
        generated_text = response.text
        print(f"AIによるペルソナ及び状況生成結果（人間限定）:\n{generated_text}") # ★ここで全体が出力されます
        persona_dict = parse_output_to_dict(generated_text)
        ai_init.current_persona_metadata = persona_dict
        return persona_dict

    except Exception as e:
        print(f"画像からのペルソナ及び状況生成（人間限定）中にエラー: {e}")
        return f"エラー：画像からキャラクター情報や状況を生成できませんでした。\n詳細: {e}"

def parse_output_to_dict(output_text: str) -> dict:
    """
    Geminiの出力テキスト（「- キー：値」形式）を辞書に変換する関数。
    """
    result = {}
    lines = output_text.splitlines()
    for line in lines:
        # 「- キー： 値」の形式を探す
        match = re.match(r"-\s*(.+?)\s*[:：]\s*(.*)", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            result[key] = value
    return result
