from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
from .models import ChatMessage
import json, os

# ================================
# 習熟度別プロンプト（SYSTEM）
# ================================
BEGINNER_PROMPT = """
あなたはプログラミング初心者向けの家庭教師です。
専門用語は極力避け、必ず噛み砕いた言葉を優先して説明してください。
初心者がつまずきやすいポイントを事前に察して補足説明を入れてください。

回答スタイル：
- 例え話や具体例を使う
- 用語には必ず簡単な説明を添える
- ステップごとに説明
- 優しく丁寧に
- 直接的な回答は提示しない
"""

INTERMEDIATE_PROMPT = """
あなたはプログラミング中級者向けのメンターです。
基礎知識がある前提で、効率的な書き方や改善ポイントを説明してください。

回答スタイル：
- 冗長な基礎説明は不要
- ベストプラクティスや代替案も提示
- コードは簡潔に
"""

ADVANCED_PROMPT = """
あなたはプロエンジニア向けの技術コンサルタントです。
高度な知識がある前提で回答してください。

回答スタイル：
- 基礎説明は省略
- 内部仕組み・アーキテクチャ・最適化に触れる
- 専門用語の使用OK
- 本質的な技術的分析を優先
"""

@csrf_exempt
def chat_with_ai(request):
    if request.method == "POST":
        data = json.loads(request.body)
        api_key = data.get("api_key")
        if not api_key:
            return JsonResponse({"error": "API key missing"}, status=400)
        problem = data.get("problem", "")
        question = data.get("question", "")
        code = data.get("code", "")
        session_id = data.get("session_id", "default")
        skill_level = data.get("skill_level", "beginner")
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.openai.iniad.org/api/v1",
        )

        # -----------------------
        # SYSTEM プロンプトを選択
        # -----------------------
        if skill_level == "beginner":
            system_prompt = BEGINNER_PROMPT
        elif skill_level == "intermediate":
            system_prompt = INTERMEDIATE_PROMPT
        else:
            system_prompt = ADVANCED_PROMPT

        # 💾 DBにユーザー発言を保存
        ChatMessage.objects.create(
            session_id = session_id,
            role="user",
            content=f"問題文:\n{problem}\n\n質問:\n{question}\n\nコード:\n{code}",
        )

        # 過去メッセージ取得（古い順）
        past_messages = ChatMessage.objects.filter(session_id=session_id).order_by("created_at")

        # 🧠 AIに渡すプロンプトを構造化
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"【問題文】\n{problem}\n\n"
                    f"【ユーザーの質問】\n{question}\n\n"
                    f"【現時点のコード】\n```python\n{code}\n```"
                ),
            },
        ]

        for msg in past_messages:
            messages.append({"role": msg.role, "content": msg.content})

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            ai_reply = response.choices[0].message.content

            # 💾 AIの返答も保存
            ChatMessage.objects.create(session_id=session_id, role="assistant", content=ai_reply)

            return JsonResponse({"reply": ai_reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


from django.views.decorators.http import require_GET

@require_GET
def get_history(request):
    messages = ChatMessage.objects.order_by("created_at")[:50]  # 最新50件
    data = [
        {"role": msg.role, "content": msg.content, "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M")}
        for msg in messages
    ]
    return JsonResponse({"history": data})

from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def delete_chat_history(request):
    """
    指定された session_id の会話履歴を削除
    """
    try:
        data = json.loads(request.body)
        session_id = data.get("session_id", "default")
        
        deleted_count, _ = ChatMessage.objects.filter(session_id=session_id).delete()
        return JsonResponse({"deleted": deleted_count})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

