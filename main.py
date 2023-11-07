import discord
import os
from keep_alive import keep_alive
from datetime import datetime, timedelta

intents = discord.Intents.all()

client = discord.Client(intents=intents)

# トークンを環境変数から取得
TOKEN = os.getenv("DISCORD_TOKEN")

# カスタマイズ可能なウェルカムメッセージ
WELCOME_MESSAGE = "ようこそ {user} さん！ ({server} へようこそ！)"

# ユーザーごとのBan/Kick回数を記録
ban_counts = {}
kick_counts = {}

# 投票機能の投票情報を保持
votes = {}

# タスク管理機能のタスクリスト
tasks = []

# ユーザーごとのコメント数とレベルを記録
user_levels = {}

# ユーザーごとの称号を記録
user_titles = {}

# 一日に作成されたタスクの番号をリセット
today = datetime.now().date()
task_number = 0

@client.event
async def on_ready():
    print('ログインしました')

@client.event
async def on_member_join(member):
    # 新規参加者にロールを付与
    role = member.guild.get_role(YOUR_ROLE_ID)
    if role:
        await member.add_roles(role)
    
    # ウェルカムチャンネルを取得または作成
    welcome_channel_name = "welcome"  # ウェルカムチャンネルの名前を指定
    welcome_channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
    if not welcome_channel:
        # ウェルカムチャンネルが存在しない場合、新しく作成
        welcome_channel = await member.guild.create_text_channel(welcome_channel_name)

    # カスタマイズ可能なウェルカムメッセージの送信
    welcome_message = WELCOME_MESSAGE.format(user=member.mention, server=member.guild.name)
    await welcome_channel.send(welcome_message)

@client.event
async def on_message(message):
    if message.author.bot:
        return  # ボットが送信したメッセージは無視

    # メッセージに "Statify" というキーワードが含まれている場合、ハートのリアクションを付ける
    if "Statify" in message.content:
        await message.add_reaction("❤️")

    # 荒らし行為判定
    if message.guild:
        guild = message.guild
        now = message.created_at
        five_seconds_ago = now - timedelta(seconds=5)
        users_banned = []
        users_kicked = []

        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, after=five_seconds_ago).limit(5):
            if entry.target != client.user:  # ボット自身は無視
                users_banned.append(entry.target)

        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, after=five_seconds_ago).limit(5):
            if entry.target != client.user:  # ボット自身は無視
                users_kicked.append(entry.target)

        # 荒らし行為を判定
        if len(users_banned) >= 5:
            for user in users_banned:
                if user not in users_kicked:
                    await user.ban(reason="Multiple Bans in 5 seconds")
                    ban_counts[user.id] = ban_counts.get(user.id, 0) + 1
        elif len(users_kicked) >= 5:
            for user in users_kicked:
                if user not in users_banned:
                    await user.kick(reason="Multiple Kicks in 5 seconds")
                    kick_counts[user.id] = kick_counts.get(user.id, 0) + 1

    # ユーザーごとのコメント数を記録
    user_id = message.author.id
    if user_id not in user_levels:
        user_levels[user_id] = 0

    user_levels[user_id] += 1

    # レベルアップ通知
    if user_id not in user_titles:
        user_titles[user_id] = []
    
    if user_levels[user_id] % 20 == 0 and "Main Speaker" not in user_titles[user_id]:
        user_titles[user_id].append("Main Speaker")
        await message.reply(f"おめでとうございます、{message.author.mention} さん！ あなたは Main Speaker になりました！")

    # 投票機能
    if message.content.startswith("!vote -start"):
        vote_message = await message.channel.send("投票を開始します。")
        await vote_message.add_reaction("👍")
        await vote_message.add_reaction("👎")
        await vote_message.add_reaction("🤷")
        vote_id = f"{today.strftime('%Y%m%d')}-{len(votes) + 1}"
        votes[vote_id] = {"options": ["👍", "👎", "🤷"], "count": 0, "votes": {"👍": 0, "👎": 0, "🤷": 0}}
        help_message = "投票機能の使い方:\n"
        help_message += "!vote -start: 新しい投票を開始します。\n"
        help_message += "!vote -end <投票番号>: 投票を終了し、結果を表示します。\n"
        help_message += "リアクションをつけて投票してください。自分の意見に対応するリアクションをつけてください。"
        await vote_message.edit(content=f"{vote_message.content}\n{help_message}\n投票番号: {vote_id}")

    elif message.content.startswith("!vote -end"):
        vote_id = message.content.split("!vote -end ")[1]
        if vote_id in votes:
            vote_data = votes[vote_id]
            result = "投票結果:\n"
            for option in vote_data["options"]:
                result += f"{option}: {vote_data['votes'][option]}票\n"
            await message.channel.send(result)
            del votes[vote_id]

    # タスク管理機能
    if message.content.startswith("!task -add"):
        task_description = message.content.split("!task -add ")[1]
        task_id = f"{today.strftime('%Y%m%d')}-{task_number + 1}"
        task_number += 1
        tasks.append({"description": task_description, "id": task_id})
        await message.channel.send(f"新しいタスクを追加しました. タスク番号: {task_id}")

    elif message.content.startswith("!task -list"):
        task_list = "現在のタスクリスト:\n"
        for task in tasks:
            task_list += f"{task['description']} (タスク番号: {task['id']})\n"
        await message.channel.send(task_list)

    elif message.content.startswith("!task -remove"):
        task_id = message.content.split("!task -remove ")[1]
        for task in tasks:
            if task["id"] == task_id:
                tasks.remove(task)
                await message.channel.send(f"タスクを削除しました. {task['description']} (タスク番号: {task_id})")
                break
        else:
            await message.channel.send("指定されたタスクが存在しません.")

    # ヘルプコマンド
    if message.content == "!vote -help":
        help_message = "投票機能の使い方:\n"
        help_message += "!vote -start: 新しい投票を開始します。\n"
        help_message += "!vote -end <投票番号>: 投票を終了し、結果を表示します。\n"
        help_message += "リアクションをつけて投票してください。自分の意見に対応するリアクションをつけてください。"
        await message.channel.send(help_message)

    if message.content == "!task -help":
        help_message = "タスク管理機能の使い方:\n"
        help_message += "!task -add <タスクの説明>: 新しいタスクを追加します。\n"
        help_message += "!task -list: 現在のタスクリストを表示します。\n"
        help_message += "!task -remove <タスク番号>: 指定されたタスクを削除します。\n"
        await message.channel.send(help_message)

# Web サーバーの立ち上げ
keep_alive()

client.run(TOKEN)

