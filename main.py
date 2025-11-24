
import logging, sqlite3, requests, os, time
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
QUEEN_BG = "https://files.catbox.moe/3i0v8u.png"
logging.basicConfig(level=logging.INFO)

def fetch(q):
    q = q.lstrip('$').upper()
    url = f"https://api.dexscreener.com/latest/dex/tokens/{q}" if len(q)>30 else f"https://api.dexscreener.com/latest/dex/search?q={q}"
    try:
        pair = max([p for p in requests.get(url,timeout=10).json()["pairs"] if p["chainId"]=="solana"], key=lambda x:x["liquidity"]["usd"])
        base = pair["baseToken"]
        holders = requests.get(f"https://public-api.solscan.io/token/holders?tokenAddress={base['address']}&limit=1").json().get("total",0)
        return {
            "symbol":base["symbol"],"ca":base["address"],"price":float(pair["priceUsd"]or 0),
            "mc":pair.get("fdv")or pair.get("marketCap",0),"txns24":sum(pair["txns"]["h24"].values()),
            "change24":pair["priceChange"]["h24"],"dex_url":pair["url"],"holders":f"{holders:,}"
        }
    except: return None

def make_card(d,s):
    fig,ax=plt.subplots(figsize=(10,16),facecolor="#0a001f");ax.axis('off')
    try:ax.imshow(mpimg.imread(BytesIO(requests.get(QUEEN_BG).content)),alpha=0.35,extent=(0,10,0,16))
    except:pass
    ax.text(5,15,"👑 WHISPERS ON 👑",ha='center',fontsize=30,color="#ff00ff",fontweight='bold')
    ax.text(5,14,f"${d['symbol']}",ha='center',fontsize=50,color="white")
    ax.barh(12,s,height=1.5,color="#ff00ff"if s>=4 else"#00ffff",left=5-s)
    ax.text(5,12,f"{s}/5",ha='center',fontsize=45,color="white")
    y=10.8
    for t in [f"MC ${d['mc']:,.0f}",f"Txns 24h {d['txns24']:,}",f"Price ${d['price']:.8f} ({d['change24']:+.2f}%)",f"Holders {d['holders']}"]:
        ax.text(0.5,y,"• "+t,fontsize=18,color="white");y-=0.8
    ax.text(5,1,f"CA: `{d['ca']}`",ha='center',fontsize=11,color="#00ff88")
    buf=BytesIO();plt.savefig(buf,format='png',bbox_inches='tight',dpi=200,facecolor='#0a001f')
    plt.close();buf.seek(0);return InputFile(buf,"queen.png")

async def alert(u:Update,c:ContextTypes):
    if not c.args:return await u.message.reply_text("Usage: /alert $TICKER")
    d=fetch(" ".join(c.args))
    if not d:return await u.message.reply_text("Not found")
    score=5 if d["txns24"]>5000 else 4 if d["txns24"]>2000 else 3 if d["txns24"]>800 else 2
    await u.message.reply_photo(make_card(d,score),caption=f"*${d['symbol']}* 👑",parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("DexScreener",url=d['dex_url'])]]))

async def start(u:Update,c:ContextTypes):
    await u.message.reply_photo(QUEEN_BG,caption="*Meme Queen AI* 👑\nThe most beautiful Solana tracker\nTry /alert $BONK",parse_mode="Markdown")

app=Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("alert",alert))
app.run_polling()
