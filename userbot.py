import asyncio
import os
from datetime import datetime, timedelta
from pyrogram import Client
import anthropic
from dotenv import load_dotenv

load_dotenv()

# === SOZLAMALAR ===
API_ID = 39769373
API_HASH = "f35d8e48ba73c38261d66d9a0449dd93"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# So'nggi necha soat xabarlarini tahlil qilish
TAHLIL_SOAT = 24

# Qaysi chat turlarini tahlil qilish
CHAT_TURLARI = {
    "PRIVATE": "Shaxsiy chat",
    "BOT": "Bot",
    "GROUP": "Guruh",
    "SUPERGROUP": "Superguruh",
    "CHANNEL": "Kanal",
}

app = Client("loyiha_manager", api_id=API_ID, api_hash=API_HASH)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def barcha_chatlarni_olish(turlar: list[str]) -> list:
    """Tanlangan turlardagi barcha chatlarni qaytaradi."""
    chatlar = []
    async for dialog in app.get_dialogs():
        if dialog.chat.type.name in turlar:
            chatlar.append(dialog.chat)
    return chatlar


async def xabarlarni_yigish(chat_id: int) -> list[str]:
    """Chatdan so'nggi TAHLIL_SOAT soat xabarlarini yig'adi."""
    chegara = datetime.now() - timedelta(hours=TAHLIL_SOAT)
    xabarlar = []
    async for msg in app.get_chat_history(chat_id, limit=100):
        if msg.date < chegara:
            break
        if msg.text:
            sender = "Men"
            if msg.from_user:
                sender = msg.from_user.first_name or msg.from_user.username or "Noma'lum"
            xabarlar.append(f"{sender}: {msg.text}")
    return list(reversed(xabarlar))


async def claude_tahlil(chat_nomi: str, chat_tur: str, xabarlar: list[str]) -> str:
    """Claude AI orqali xabarlarni tahlil qiladi."""
    if not xabarlar:
        return "So'nggi 24 soatda xabar yo'q."

    matn = "\n".join(xabarlar[-60:])

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": f"""Quyidagi Telegram {chat_tur} xabarlarini tahlil qil:
Chat nomi: {chat_nomi}

Xabarlar:
{matn}

Qisqa hisobot ber (6-10 qator):
1. Asosiy mavzu — nima muhokama qilindi
2. Muhim qarorlar yoki topshiriqlar (agar bo'lsa)
3. Hal etilmagan muammolar (agar bo'lsa)
4. Holat: Faol / Sustlashgan / Muammoli / Oddiy suhbat"""
        }]
    )
    return response.content[0].text


def tur_belgisi(tur: str) -> str:
    return {
        "PRIVATE": "👤",
        "BOT": "🤖",
        "GROUP": "👥",
        "SUPERGROUP": "👥",
        "CHANNEL": "📢",
    }.get(tur, "💬")


async def royxat_chiqar(turlar: list[str]):
    """Chatlar ro'yxatini chiqaradi."""
    chatlar = await barcha_chatlarni_olish(turlar)
    print(f"\nJami {len(chatlar)} ta chat topildi:\n")
    for i, c in enumerate(chatlar, 1):
        belgi = tur_belgisi(c.type.name)
        nom = c.title or c.first_name or c.username or "Nomsiz"
        print(f"{i:3}. {belgi} {nom}")


async def hisobot_chiqar(turlar: list[str]):
    """Barcha chatlar bo'yicha Claude AI hisobot yaratadi."""
    chatlar = await barcha_chatlarni_olish(turlar)

    print("\n" + "=" * 60)
    print(f"  HISOBOT — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Jami {len(chatlar)} ta chat tahlil qilinadi")
    print("=" * 60)

    muvaffaqiyat = 0
    xato = 0

    for i, chat in enumerate(chatlar, 1):
        nom = chat.title or chat.first_name or chat.username or "Nomsiz"
        tur = CHAT_TURLARI.get(chat.type.name, chat.type.name)
        belgi = tur_belgisi(chat.type.name)

        print(f"\n[{i}/{len(chatlar)}] {belgi} {nom} ({tur})")
        print("─" * 50)

        try:
            xabarlar = await xabarlarni_yigish(chat.id)
            tahlil = await claude_tahlil(nom, tur, xabarlar)
            print(tahlil)
            muvaffaqiyat += 1
        except Exception as e:
            print(f"⚠️  O'tkazib yuborildi: {e}")
            xato += 1

        await asyncio.sleep(0.8)

    print("\n" + "=" * 60)
    print(f"  TUGADI — ✅ {muvaffaqiyat} ta tahlil qilindi, ⚠️ {xato} ta o'tkazib yuborildi")
    print("=" * 60)


async def main():
    async with app:
        print("\n" + "=" * 50)
        print("  TELEGRAM LOYIHA MANAGER — Claude AI")
        print("=" * 50)

        print("\nQaysi chatlarni tahlil qilish kerak?")
        print("1 — Faqat guruhlar (GROUP + SUPERGROUP)")
        print("2 — Guruhlar + Kanallar")
        print("3 — Hammasi (shaxsiy + guruh + kanal + bot)")
        print("4 — Faqat ro'yxat ko'rish (tahlilsiz)")
        tanlov = input("\nTanlang (1/2/3/4): ").strip()

        tur_map = {
            "1": ["GROUP", "SUPERGROUP"],
            "2": ["GROUP", "SUPERGROUP", "CHANNEL"],
            "3": ["PRIVATE", "BOT", "GROUP", "SUPERGROUP", "CHANNEL"],
            "4": ["GROUP", "SUPERGROUP", "CHANNEL", "PRIVATE"],
        }

        if tanlov not in tur_map:
            print("Noto'g'ri tanlov.")
            return

        turlar = tur_map[tanlov]

        if tanlov == "4":
            await royxat_chiqar(turlar)
        else:
            await hisobot_chiqar(turlar)


if __name__ == "__main__":
    asyncio.run(main())
