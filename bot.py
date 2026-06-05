"""
╔══════════════════════════════════════════════╗
║     BOT TELEGRAM TOKO PRODUK DIGITAL         ║
║     Dengan Bottom Keyboard + Inline Button   ║
╚══════════════════════════════════════════════╝

SETUP:
  1. pip install python-telegram-bot python-dotenv
  2. Isi BOT_TOKEN dan ADMIN_ID di bawah
  3. python bot.py
"""

import logging
import json
import os
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ══════════════════════════════════════════════
#  KONFIGURASI — EDIT BAGIAN INI
# ══════════════════════════════════════════════

BOT_TOKEN  = os.getenv("BOT_TOKEN",  "ISI_TOKEN_DISINI")
ADMIN_ID   = int(os.getenv("ADMIN_ID",   "0"))
STORE_NAME = os.getenv("STORE_NAME", "🛍️ Toko Digital")
BANK_INFO  = os.getenv("BANK_INFO",  "BCA • 1234567890 • a/n Nama Kamu")

# ══════════════════════════════════════════════
#  PRODUK — EDIT SESUAI DAGANGANMU
# ══════════════════════════════════════════════

PRODUCTS = {
    "P1": {
        "name": "📘 Ebook SEO Masterclass",
        "desc": "Panduan SEO lengkap dari nol sampai rank #1 Google. 150+ halaman, update 2025.",
        "price": 99_000,
        "category": "Ebook",
        "file_id": None,   # isi setelah upload file ke bot
    },
    "P2": {
        "name": "🎨 Pack Template Canva 50pcs",
        "desc": "50 template Canva premium siap pakai untuk feed Instagram & presentasi bisnis.",
        "price": 75_000,
        "category": "Template",
        "file_id": None,
    },
    "P3": {
        "name": "💻 Source Code Landing Page",
        "desc": "10 desain landing page HTML/CSS/JS modern & responsif. Siap upload ke hosting.",
        "price": 150_000,
        "category": "Source Code",
        "file_id": None,
    },
    "P4": {
        "name": "📊 Spreadsheet Keuangan UMKM",
        "desc": "Template Excel otomatis hitung laba-rugi, stok & arus kas untuk UMKM.",
        "price": 45_000,
        "category": "Template",
        "file_id": None,
    },
    "P5": {
        "name": "🚀 Video Kursus Digital Marketing",
        "desc": "8 jam video + modul PDF. Belajar ads, konten, & strategi dari nol sampai bisa.",
        "price": 199_000,
        "category": "Kursus",
        "file_id": None,
    },
}

# ══════════════════════════════════════════════
#  STATES
# ══════════════════════════════════════════════

AWAITING_PROOF, AWAITING_BROADCAST = range(2)

# ══════════════════════════════════════════════
#  DATABASE (JSON)
# ══════════════════════════════════════════════

DB = "db.json"

def db_load():
    if not os.path.exists(DB):
        return {"users": {}, "orders": {}, "n": 0}
    with open(DB) as f:
        return json.load(f)

def db_save(d):
    with open(DB, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def db_save_user(uid, username, name):
    d = db_load()
    d["users"][str(uid)] = {"uid": uid, "username": username, "name": name, "at": now()}
    db_save(d)

def db_new_order(uid, username, cart, total):
    d = db_load()
    d["n"] += 1
    oid = f"ORD{d['n']:05d}"
    d["orders"][oid] = {
        "oid": oid, "uid": uid, "username": username,
        "cart": cart, "total": total,
        "status": "pending", "at": now()
    }
    db_save(d)
    return oid

def db_update(oid, status):
    d = db_load()
    if oid in d["orders"]:
        d["orders"][oid]["status"] = status
    db_save(d)

def db_get_order(oid):
    return db_load()["orders"].get(oid)

def db_user_orders(uid):
    return [o for o in db_load()["orders"].values() if o["uid"] == uid]

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════

def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def rp(n):
    return f"Rp {n:,}".replace(",", ".")

def cart(ctx):
    return ctx.user_data.setdefault("cart", {})

def cart_total(c):
    return sum(PRODUCTS[p]["price"] * q for p, q in c.items() if p in PRODUCTS)

def cart_text(c):
    if not c:
        return "🛒 Keranjang kosong."
    rows = [f"• {PRODUCTS[p]['name']} x{q} = {rp(PRODUCTS[p]['price']*q)}"
            for p, q in c.items() if p in PRODUCTS]
    rows.append(f"\n💰 *Total: {rp(cart_total(c))}*")
    return "\n".join(rows)

# ══════════════════════════════════════════════
#  KEYBOARD BOTTOM
# ══════════════════════════════════════════════

def kb_main(uid=0):
    rows = [
        [KeyboardButton("🛍️ Produk"),    KeyboardButton("🛒 Keranjang")],
        [KeyboardButton("📋 Pesananku"), KeyboardButton("📞 Hubungi Kami")],
    ]
    if uid == ADMIN_ID:
        rows.append([KeyboardButton("⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# ══════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db_save_user(u.id, u.username or "", u.full_name)

    teks = (
        f"Halo *{u.first_name}* 👋\n\n"
        f"Selamat datang di *{STORE_NAME}*!\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Kami jual produk digital berkualitas:\n"
        "📘 Ebook  •  🎨 Template\n"
        "💻 Source Code  •  🚀 Kursus\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "Gunakan tombol di bawah untuk mulai belanja 👇"
    )
    await update.message.reply_text(teks, parse_mode="Markdown",
                                    reply_markup=kb_main(u.id))

# ══════════════════════════════════════════════
#  PRODUK
# ══════════════════════════════════════════════

async def show_produk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cats = sorted(set(p["category"] for p in PRODUCTS.values()))
    btns = [[InlineKeyboardButton(f"📂 {c}", callback_data=f"cat:{c}")] for c in cats]
    btns.append([InlineKeyboardButton("📦 Semua Produk", callback_data="cat:SEMUA")])
    await update.message.reply_text(
        "🛍️ *Pilih Kategori:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(btns)
    )

async def cb_kategori(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    cat = q.data.split(":", 1)[1]
    prods = {k: v for k, v in PRODUCTS.items()
             if cat == "SEMUA" or v["category"] == cat}
    btns = [
        [InlineKeyboardButton(f"{v['name']}  —  {rp(v['price'])}", callback_data=f"prod:{k}")]
        for k, v in prods.items()
    ]
    btns.append([InlineKeyboardButton("« Kembali", callback_data="back:cat")])
    await q.edit_message_text(
        f"📂 *{cat}* — pilih produk:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(btns)
    )

async def cb_produk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    pid = q.data.split(":", 1)[1]
    p = PRODUCTS.get(pid)
    if not p:
        await q.edit_message_text("Produk tidak ditemukan.")
        return
    teks = (
        f"*{p['name']}*\n"
        f"📂 {p['category']}  |  💰 {rp(p['price'])}\n\n"
        f"📝 {p['desc']}"
    )
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Tambah ke Keranjang", callback_data=f"add:{pid}")],
        [InlineKeyboardButton("« Kembali", callback_data=f"cat:{p['category']}")],
    ])
    await q.edit_message_text(teks, parse_mode="Markdown", reply_markup=btns)

async def cb_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    pid = q.data.split(":", 1)[1]
    c = cart(ctx)
    c[pid] = c.get(pid, 0) + 1
    await q.answer(f"✅ Ditambahkan! Keranjang: {sum(c.values())} item", show_alert=False)

async def cb_back_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    cats = sorted(set(p["category"] for p in PRODUCTS.values()))
    btns = [[InlineKeyboardButton(f"📂 {c}", callback_data=f"cat:{c}")] for c in cats]
    btns.append([InlineKeyboardButton("📦 Semua Produk", callback_data="cat:SEMUA")])
    await q.edit_message_text("🛍️ *Pilih Kategori:*", parse_mode="Markdown",
                               reply_markup=InlineKeyboardMarkup(btns))

# ══════════════════════════════════════════════
#  KERANJANG
# ══════════════════════════════════════════════

async def show_keranjang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    c = cart(ctx)
    btns = []
    if c:
        btns = [
            [InlineKeyboardButton("✅ Checkout Sekarang", callback_data="checkout")],
            [InlineKeyboardButton("🗑️ Kosongkan", callback_data="clear")],
        ]
    await update.message.reply_text(
        f"🛒 *Keranjang Belanja*\n\n{cart_text(c)}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(btns) if btns else None
    )

async def cb_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data["cart"] = {}
    await q.edit_message_text("🗑️ Keranjang dikosongkan.")

# ══════════════════════════════════════════════
#  CHECKOUT → BUKTI BAYAR
# ══════════════════════════════════════════════

async def cb_checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    c = dict(cart(ctx))
    if not c:
        await q.edit_message_text("Keranjang kosong.")
        return

    u = q.from_user
    total = cart_total(c)
    oid = db_new_order(u.id, u.username or u.full_name, c, total)
    ctx.user_data["pending_order"] = oid
    ctx.user_data["cart"] = {}

    teks = (
        f"📋 *Ringkasan Order*\n\n"
        f"{cart_text(c)}\n\n"
        f"🆔 Order ID: `{oid}`\n"
        f"💰 Total: *{rp(total)}*\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💳 *Transfer ke:*\n"
        f"`{BANK_INFO}`\n"
        f"Nominal tepat: *{rp(total)}*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📸 Setelah transfer, kirim *foto/screenshot* bukti di sini."
    )
    await q.edit_message_text(teks, parse_mode="Markdown")
    return AWAITING_PROOF

async def terima_bukti(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    oid = ctx.user_data.get("pending_order")
    if not oid:
        await update.message.reply_text("Tidak ada order aktif. Ketuk /start")
        return ConversationHandler.END

    u = update.effective_user
    order = db_get_order(oid)
    db_update(oid, "verifying")

    caption = (
        f"🔔 *BUKTI BAYAR MASUK*\n\n"
        f"🆔 {oid}\n"
        f"👤 {u.full_name} (@{u.username or '-'})\n"
        f"💰 {rp(order['total'])}\n"
        f"🕐 {now()}"
    )
    tombol = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ACC", callback_data=f"acc:{oid}:{u.id}"),
        InlineKeyboardButton("❌ Tolak", callback_data=f"tolak:{oid}:{u.id}"),
    ]])

    if update.message.photo:
        await ctx.bot.send_photo(ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=caption, parse_mode="Markdown", reply_markup=tombol)
    elif update.message.document:
        await ctx.bot.send_document(ADMIN_ID,
            document=update.message.document.file_id,
            caption=caption, parse_mode="Markdown", reply_markup=tombol)
    else:
        await update.message.reply_text("⚠️ Kirim *foto* atau *file* bukti transfer ya.")
        return AWAITING_PROOF

    await update.message.reply_text(
        f"✅ *Bukti diterima!*\n\n"
        f"🆔 Order: `{oid}`\n"
        f"⏳ Sedang diverifikasi admin (5–15 menit).\n"
        f"Produk langsung dikirim setelah konfirmasi! 🎉",
        parse_mode="Markdown",
        reply_markup=kb_main(u.id)
    )
    return ConversationHandler.END

# ══════════════════════════════════════════════
#  ADMIN: ACC / TOLAK
# ══════════════════════════════════════════════

async def cb_acc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("Bukan admin!", show_alert=True); return
    await q.answer()
    _, oid, uid_str = q.data.split(":")
    uid = int(uid_str)
    order = db_get_order(oid)
    if not order:
        await q.edit_message_caption("Order tidak ada."); return
    db_update(oid, "paid")

    # kirim produk otomatis
    for pid in order["cart"]:
        p = PRODUCTS.get(pid)
        if p and p.get("file_id"):
            await ctx.bot.send_document(uid, document=p["file_id"],
                caption=f"🎉 *{p['name']}*\nTerima kasih sudah belanja di {STORE_NAME}!",
                parse_mode="Markdown")

    await ctx.bot.send_message(uid,
        f"✅ *Pembayaran Dikonfirmasi!*\n\n"
        f"🆔 Order: `{oid}`\n"
        f"💰 Total: {rp(order['total'])}\n\n"
        f"📦 Produkmu segera dikirimkan.\n"
        f"Terima kasih sudah belanja! 🙏",
        parse_mode="Markdown")

    cap = (q.message.caption or "") + "\n\n✅ *SUDAH DI-ACC*"
    await q.edit_message_caption(cap, parse_mode="Markdown")

async def cb_tolak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("Bukan admin!", show_alert=True); return
    await q.answer()
    _, oid, uid_str = q.data.split(":")
    uid = int(uid_str)
    db_update(oid, "rejected")
    await ctx.bot.send_message(uid,
        f"❌ *Pembayaran Ditolak*\n\n"
        f"🆔 Order: `{oid}`\n\n"
        f"Bukti tidak valid atau nominal tidak sesuai.\n"
        f"Hubungi admin untuk bantuan.",
        parse_mode="Markdown")
    cap = (q.message.caption or "") + "\n\n❌ *DITOLAK*"
    await q.edit_message_caption(cap, parse_mode="Markdown")

# ══════════════════════════════════════════════
#  PESANANKU
# ══════════════════════════════════════════════

async def show_pesanan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    orders = sorted(db_user_orders(update.effective_user.id),
                    key=lambda x: x["at"], reverse=True)
    if not orders:
        await update.message.reply_text("📋 Belum ada pesanan."); return

    icon = {"pending":"⏳","verifying":"🔍","paid":"✅","rejected":"❌"}
    teks = "📋 *Riwayat Pesananmu:*\n\n"
    for o in orders[:8]:
        teks += f"{icon.get(o['status'],'❓')} `{o['oid']}` — {rp(o['total'])} [{o['status']}]\n"
    await update.message.reply_text(teks, parse_mode="Markdown")

# ══════════════════════════════════════════════
#  HUBUNGI KAMI
# ══════════════════════════════════════════════

async def show_kontak(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 *Hubungi Kami*\n\n"
        f"Admin: @admin_username\n"
        f"Jam: 08.00 – 22.00 WIB\n\n"
        f"💳 *Rekening Pembayaran:*\n"
        f"`{BANK_INFO}`",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════
#  ADMIN PANEL
# ══════════════════════════════════════════════

async def show_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Akses ditolak."); return
    d = db_load()
    paid = [o for o in d["orders"].values() if o["status"] == "paid"]
    pending = [o for o in d["orders"].values() if o["status"] in ("pending","verifying")]
    rev = sum(o["total"] for o in paid)
    teks = (
        f"⚙️ *Admin Panel*\n\n"
        f"👥 Total User : {len(d['users'])}\n"
        f"📦 Total Order: {len(d['orders'])}\n"
        f"✅ Selesai    : {len(paid)}\n"
        f"⏳ Pending    : {len(pending)}\n"
        f"💰 Pendapatan : {rp(rev)}"
    )
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Lihat Semua Order", callback_data="adm:orders")],
        [InlineKeyboardButton("📢 Broadcast Pesan",   callback_data="adm:broadcast")],
    ])
    await update.message.reply_text(teks, parse_mode="Markdown", reply_markup=btns)

async def cb_adm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ADMIN_ID:
        await q.answer("Akses ditolak!", show_alert=True); return
    await q.answer()
    action = q.data.split(":", 1)[1]

    if action == "orders":
        d = db_load()
        orders = sorted(d["orders"].values(), key=lambda x: x["at"], reverse=True)[:15]
        icon = {"pending":"⏳","verifying":"🔍","paid":"✅","rejected":"❌"}
        teks = "📋 *15 Order Terbaru:*\n\n"
        for o in orders:
            teks += f"{icon.get(o['status'],'❓')} `{o['oid']}` @{o['username'] or '-'} {rp(o['total'])}\n"
        await q.edit_message_text(teks, parse_mode="Markdown")

    elif action == "broadcast":
        await q.edit_message_text("📢 Kirim pesan broadcast ke semua user:")
        return AWAITING_BROADCAST

async def do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    d = db_load()
    msg = update.message.text
    ok = 0
    for uid in d["users"]:
        try:
            await ctx.bot.send_message(int(uid),
                f"📢 *Info dari {STORE_NAME}:*\n\n{msg}", parse_mode="Markdown")
            ok += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast terkirim ke {ok} user.",
                                    reply_markup=kb_main(ADMIN_ID))
    return ConversationHandler.END

# ══════════════════════════════════════════════
#  UPLOAD PRODUK (admin kirim file → dapat file_id)
# ══════════════════════════════════════════════

async def admin_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.document:
        fid = update.message.document.file_id
        fn  = update.message.document.file_name
    elif update.message.photo:
        fid = update.message.photo[-1].file_id
        fn  = "photo"
    else:
        return
    await update.message.reply_text(
        f"📄 `{fn}`\n\n🆔 file_id:\n`{fid}`\n\n"
        f"Salin ke PRODUCTS → `file_id` di bot.py",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════════
#  TEXT ROUTER
# ══════════════════════════════════════════════

async def teks_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "🛍️ Produk":        await show_produk(update, ctx)
    elif t == "🛒 Keranjang":   await show_keranjang(update, ctx)
    elif t == "📋 Pesananku":   await show_pesanan(update, ctx)
    elif t == "📞 Hubungi Kami":await show_kontak(update, ctx)
    elif t == "⚙️ Admin Panel": await show_admin(update, ctx)

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")]
)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation: checkout → bukti bayar
    conv_checkout = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_checkout, pattern="^checkout$")],
        states={AWAITING_PROOF: [MessageHandler(filters.PHOTO | filters.Document.ALL, terima_bukti)]},
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    # Conversation: broadcast
    conv_broadcast = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_adm, pattern="^adm:")],
        states={AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)]},
        fallbacks=[CommandHandler("start", cmd_start)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv_checkout)
    app.add_handler(conv_broadcast)

    app.add_handler(CallbackQueryHandler(cb_kategori,  pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(cb_produk,    pattern="^prod:"))
    app.add_handler(CallbackQueryHandler(cb_add,       pattern="^add:"))
    app.add_handler(CallbackQueryHandler(cb_back_cat,  pattern="^back:cat$"))
    app.add_handler(CallbackQueryHandler(cb_clear,     pattern="^clear$"))
    app.add_handler(CallbackQueryHandler(cb_acc,       pattern="^acc:"))
    app.add_handler(CallbackQueryHandler(cb_tolak,     pattern="^tolak:"))
    app.add_handler(CallbackQueryHandler(cb_adm,       pattern="^adm:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, teks_handler))
    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO) & filters.User(ADMIN_ID), admin_file
    ))

    print(f"✅ Bot {STORE_NAME} aktif!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
