import asyncio
import json
import os
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
import anthropic

# === SOZLAMALAR ===
API_ID = 39769373
API_HASH = "f35d8e48ba73c38261d66d9a0449dd93"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# So'nggi N soat ichidagi xabarlarni tahlil qilish
TAHLIL_SOAT = 24

app = Client("loyiha_manager", api_id=API_ID, api_hash=API_HASH)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Guruhlardan yig'ilgan xabarlar
guruh_xabarlari: dict[str, list[str]] = {}


async def guruhlarni_olish():
    """Barcha guruh va superguruhlarni qaytaradi."""
    guruhlar = []
    async for dialog in app.get_dialogs():
        if dialog.chat.type.name in ("GROUP", "SUPERGROUP"):
            guruhlar.append(dialog.chat)
    return guruhlar


async def xabarlarni_yigish(chat_id: int, chat_title: str):
    """Guruhdan so'nggi 24 soat xabarlarini yig'adi."""
    chegara = datetime.now() - timedelta(hours=TAHLIL_SOAT)
    xabarlar = []
    async for msg in app.get_chat_history(chat_id, limit=100):
        if msg.date < chegara:
            break
        if msg.text:
            sender = msg.from_user.first_name if msg.from_user else "Noma'lum"
            xabarlar.append(f"{sender}: {msg.text}")
    return list(reversed(xabarlar))


async def claude_tahlil(guruh_nomi: str, xabarlar: list[str]) -> str:
    """Claude AI orqali guruh xabarlarini tahlil qiladi."""
    if not xabarlar:
        return "So'nggi 24 soatda xabar yo'q."

    matn = "\n".join(xabarlar[-50:])  # Oxirgi 50 xabar

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""Quyidagi Telegram guruh xabarlarini tahlil qil va qisqa hisobot ber:
Guruh: {guruh_nomi}

Xabarlar:
{matn}

Hisobotda quyidagilarni ko'rsat:
1. Asosiy mavzu / nima muhokama qilindi
2. Muhim qarorlar yoki topshiriqlar
3. Hal etilmagan muammolar
4. Umumiy holat (faol / sustlashgan / muammoli)

Qisqa va aniq yoz (5-8 qator)."""
        }]
    )
    return response.content[0].text


async def hisobot_chiqar():
    """Barcha guruhlar bo'yicha hisobot yaratadi."""
    print("\n" + "="*60)
    print(f"LOYIHALAR HISOBOTI — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("="*60)

    guruhlar = await guruhlarni_olish()
    print(f"\nJami {len(guruhlar)} ta guruh topildi.\n")

    for guruh in guruhlar:
        print(f"\n{'─'*50}")
        print(f"📁 {guruh.title}")
        print(f"{'─'*50}")
        try:
            xabarlar = await xabarlarni_yigish(guruh.id, guruh.title)
            tahlil = await claude_tahlil(guruh.title, xabarlar)
            print(tahlil)
        except Exception as e:
            print(f"Xatolik: {e}")
        await asyncio.sleep(1)  # Rate limit uchun

    print("\n" + "="*60)
    print("HISOBOT TUGADI")
    print("="*60)


async def guruhlar_royxati():
    """Faqat guruhlar ro'yxatini chiqaradi."""
    guruhlar = await guruhlarni_olish()
    print(f"\nSizning {len(guruhlar)} ta guruhingiz:\n")
    for i, g in enumerate(guruhlar, 1):
        print(f"{i:2}. {g.title}")


async def main():
    async with app:
        print("Nima qilmoqchisiz?")
        print("1 — Barcha guruhlar ro'yxati")
        print("2 — Barcha guruhlar hisoboti (Claude AI tahlil)")
        tanlov = input("\nTanlang (1/2): ").strip()

        if tanlov == "1":
            await guruhlar_royxati()
        elif tanlov == "2":
            await hisobot_chiqar()
        else:
            print("Noto'g'ri tanlov.")


if __name__ == "__main__":
    asyncio.run(main())
