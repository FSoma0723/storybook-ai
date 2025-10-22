import re

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

def format_persona_dict_for_display(persona_dict: dict) -> str:
    """
    辞書型のキャラクター情報を人間が読める形式に変換
    """
    if not isinstance(persona_dict, dict):
        return str(persona_dict)
    lines = []
    for key, value in persona_dict.items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)
