import discord
from discord.ext import commands
import random
import asyncio # Aynı anda birden fazla bot çalıştırmak için
import os # Ortam değişkenlerini okumak için
from flask import Flask # Replit'te botu 7/24 aktif tutmak için gerekli
from threading import Thread # Replit'te botu 7/24 aktif tutmak için gerekli

# bad_words.py dosyasından BAD_WORDS listesini içe aktarıyoruz
from bad_words import BAD_WORDS

# tokens.py dosyasından BOT_TOKENS listesini içe aktarıyoruz
from tokens import BOT_TOKENS

# --- Flask Web Sunucusu Kodu (Botu Replit'te 7/24 Aktif Tutmak İçin) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Alive!" # Botun çalıştığını gösteren basit bir mesaj

def run():
  app.run(host='0.0.0.0',port=8080) # Replit'in varsayılan portu 8080'dir

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Ayarları ---
# Botlarımızın kullanacağı intent'ler
# MESSAGE CONTENT INTENT ve SERVER MEMBERS INTENT Discord Developer Portal'dan açık olmalı!
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Hoş geldin mesajı gibi üye olayları için gerekli

# Botlarımızı bir listede tutacağız
all_bots = []

# --- Bot Fonksiyonları ve Event'leri ---
# Her bir bot için ayrı bir bot örneği oluşturma ve event/komutları ekleme fonksiyonu
def create_bot_instance(token):
    # Komutların ön ekini (prefix) buradan değiştirebilirsin
    bot = commands.Bot(command_prefix='!', intents=intents)

    # Bot hazır olduğunda konsola yazdırılacak mesaj
    @bot.event
    async def on_ready():
        print(f'Bot olarak giriş yapıldı: {bot.user.name} (ID: {bot.user.id})')
        print(f'Token: {token[:5]}...') # Güvenlik için token'ın sadece ilk 5 karakterini gösteririz
        print('--------------------')

    # Basit bir ping-pong komutu
    @bot.command()
    async def ping(ctx):
        await ctx.send('Pong!')

    # Yeni komut: !merhaba
    @bot.command()
    async def merhaba(ctx):
        await ctx.send(f'Selam {ctx.author.mention}! Nasılsın kanka? Ben {bot.user.name} botuyum.')

    # Yeni komut: !sayı (1 ile 100 arasında rastgele sayı verir)
    @bot.command()
    async def sayı(ctx):
        rastgele_sayı = random.randint(1, 100)
        await ctx.send(f'İşte sana rastgele bir sayı: {rastgele_sayı}')

    # --- Kötü Kelime Filtresi ---
    @bot.event
    async def on_message(message):
        # Botun kendi mesajlarını kontrol etmesini engelliyoruz, yoksa sonsuz döngüye girer
        if message.author == bot.user:
            return

        # Mesajı küçük harflere çevirip kontrol ediyoruz
        msg_content = message.content.lower()

        for word in BAD_WORDS: # BAD_WORDS listesi bad_words.py dosyasından geliyor
            if word in msg_content:
                try:
                    await message.delete() # Mesajı sil
                    # Kullanıcıya kanaldan uyarı gönder
                    await message.channel.send(f'{message.author.mention} Lütfen kötü kelime kullanmayın! Mesajınız silindi. (Bot: {bot.user.name})')
                    print(f'Kötü kelime tespit edildi ve silindi: "{message.content}" (Bot: {bot.user.name})')
                    return # Kötü kelime bulunduğunda diğer kelimeleri kontrol etmeye gerek yok
                except discord.Forbidden:
                    # Botun mesaj silme yetkisi yoksa bu hata oluşur
                    print(f'Hata: Bot ({bot.user.name}) mesaj silme yetkisine sahip değil. Lütfen "Manage Messages" yetkisini verin.')
                    await message.channel.send(f'Uyarı: Mesajı silemedim, yetkim yok. Lütfen botuma "Mesajları Yönet" yetkisi verin. (Bot: {bot.user.name})')
                except Exception as e:
                    print(f'Mesaj silinirken bir hata oluştu (Bot: {bot.user.name}): {e}')
                break # Kötü kelime bulunduğunda döngüden çık

        # Botun komutlarını da çalıştırması için bu satır önemli!
        await bot.process_commands(message)

    # --- Hoş Geldin Mesajı ---
    @bot.event
    async def on_member_join(member):
        # Bu event, bir üye sunucuya katıldığında tetiklenir
        # Hoş geldin mesajını göndereceğin kanalın ID'sini buraya yazmalısın.
        # Kanal ID'sini almak için Discord'da geliştirici modunu açıp kanala sağ tıkla ve "ID'yi Kopyala" de.
        # Her bot için farklı bir hoş geldin kanalı belirleyebilirsin.
        welcome_channel_id = 1388452486930497649 # <<< BURAYI KENDİ KANAL ID'NLE DEĞİŞTİR!!!

        channel = bot.get_channel(welcome_channel_id)
        if channel:
            await channel.send(f'Sunucumuza hoş geldin, {member.mention}! Aramıza katıldığın için çok mutluyuz kanka! Ben {bot.user.name} botuyum.')
            print(f'{member.name} kullanıcısı sunucuya katıldı ve hoş geldin mesajı gönderildi. (Bot: {bot.user.name})')

    return bot # Oluşturulan bot örneğini döndürürüz

# --- Botları Başlatma ---
# Ana fonksiyonumuz: Tüm botları paralel olarak başlatır
async def main():
    tasks = []
    # Eğer BOT_TOKENS listesi boşsa ve ortam değişkenlerinden token okumuyorsak, bot çalışmaz.
    if not BOT_TOKENS: # BOT_TOKENS listesi tokens.py dosyasından geliyor
        print("Hata: Hiç bot token'ı bulunamadı. Lütfen tokens.py dosyasını doldurun.")
        return # Fonksiyondan çık

    for token in BOT_TOKENS:
        # Her token için bir bot örneği oluştur
        current_bot = create_bot_instance(token)
        all_bots.append(current_bot) # Botları listeye ekle (isteğe bağlı)
        # Her botu çalıştırmak için bir task oluştur
        tasks.append(current_bot.start(token))

    # Tüm botları aynı anda başlat
    await asyncio.gather(*tasks)

# Programı başlat
if __name__ == '__main__':
    # Flask sunucusunu başlatarak botu Replit'te 7/24 aktif tutma mekanizmasını çalıştır
    keep_alive() # Bu satır çok önemli!

    # Eğer Windows kullanıyorsan ve asyncio ile ilgili bir hata alırsan, aşağıdaki satırı aktif et:
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
