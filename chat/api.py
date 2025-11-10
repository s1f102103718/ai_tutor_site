from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai
from .models import ChatMessage
import json, os

client = openai.OpenAI(

    api_key= os.getenv("OPENAI_API_KEY"),

    base_url="https://api.openai.iniad.org/api/v1",

)

@csrf_exempt
def chat_with_ai(request):
    if request.method == "POST":
        data = json.loads(request.body)
        problem = data.get("problem", "")
        question = data.get("question", "")
        code = data.get("code", "")
        session_id = data.get("session_id", "default")
        skill_level = data.get("skill_level", "beginner")

        if skill_level == "beginner":
            system_message = "あなたは初心者向けにわかりやすく、具体例を使って丁寧に説明してください。"
        elif skill_level == "intermediate":
            system_message = "あなたは中級者向けに適度な技術的詳細も交えて説明してください。"
        else:
            system_message = "あなたは上級者向けに効率的で専門的な内容で回答してください。"

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
                "content": (
                    "あなたは優秀なプログラミングチューターです。"
                    "ユーザーが解こうとしている課題（問題文）と、そのコードを理解した上で、"
                    "直接的な回答は用いずに"
                    "質問に対して段階的にステップを刻んで丁寧に答えてください。"
                    + system_message
                ),
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
