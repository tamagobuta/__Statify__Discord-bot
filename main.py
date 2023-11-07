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

# ユーザーごとのコメント数を記録
user_comment_counts = {}  # ユーザーごとのコメント数を記録する辞書

# 一日に作成されたタスクの番号をリセット
today = datetime.now().date()
task_number = 0

@client.event
async def on_ready():
    print('ログインしました')

@client.event
async def on_member_join(member):
    # "Uncertified" ロールを作成
    role = await member.guild.create_role(name="Uncertified")
    
    # 新規参加者に "Uncertified" ロールを付与
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

    # 認証ボタンのメッセージを送信
    auth_button_message = await member.send("ユーザー認証のために以下のボタンをクリックしてください。")
    auth_button = discord.ui.Button(style=discord.ButtonStyle.green, label="認証")
    auth_view = discord.ui.View()
    auth_view.add_item(auth_button)
    await auth_button_message.edit(content=auth_button_message.content, view=auth_view)

    def check(res):
        return res.user == member and res.component.label == "認証"

    try:
        res = await client.wait_for("button_click", check=check, timeout=600)  # ボタンのクリックを待機 (最大10分間)
        await res.message.delete()
        # "Uncertified" ロールを削除
        await member.remove_roles(role)
        await member.send("認証が完了しました！")
    except asyncio.TimeoutError:
        await member.send("認証がタイムアウトしました。")

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
    if user_id not in user_comment_counts:
        user_comment_counts[user_id] = 0

    user_comment_counts[user_id] += 1

    # レベルアップ通知
    if user_comment_counts[user_id] >= 100:
        # メインスピーカーロールの取得
        main_speaker_role = discord.utils.get(message.guild.roles, name="Main Speaker")
        if main_speaker_role and main_speaker_role not in message.author.roles:
            await message.author.add_roles(main_speaker_role)
            await message.reply(f"おめでとうございます、{message.author.mention} さん！ あなたは Main Speaker になりました！")

    # 投票機能
    if message.content.startswith("!vote -start"):
        vote_message = await message.channel.send("投票を開始します。")
        await vote_message.add_reaction("👍")
        await vote_message.add_reaction("👎")
        await vote_message.add_reaction("🤷")
        vote_id = f"{today.strftime('%Y%m%d')}-{len(votes) + 1}"
        votes[vote_id] = {"options": ["👍", "👎", "🤷"], "votes": {}}
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
            total_votes = 0
            max_votes = 0
            max_options = []
            other_votes = {}

            for option, count in vote_data["votes"].items():
                total_votes += count
                if count > max_votes:
                    max_votes = count
                    max_options = [option]
                elif count == max_votes:
                    max_options.append(option)
                else:
                    other_votes[option] = count

            if max_options:
                result += f"最多得票: {'/'.join(max_options)} ({max_votes}票)\n"
            result += "その他の得票:\n"
            for option, count in other_votes.items():
                result += f"{option}: {count}票\n"

            result += f"総投票数: {total_votes}票"
            await message.channel.send(result)
            del votes[vote_id]

    # タスク管理機能
    if message.content.startswith("!task -add"):
        task_description = message.content.split("!task -add ")[1]
        task_id = f"{today.strftime('%Y%m%d')}-{task_number + 1}"
        task_number += 1
        tasks.append({"description": task_description, "id": task_id})
        await message.channel.send(f"新しいタスクを追加しました. タスク番号: {task_id}")

    elif message.content == "!task -list":
        if not tasks:
            await message.channel.send("現在のタスクリストは空です.")
        else:
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

    # サーバー統計情報表示コマンド
    if message.content == "!server":
        server = message.guild
        total_members = len(server.members)
        online_members = len([member for member in server.members if member.status != discord.Status.offline])
        text_channels = len(server.text_channels)
        voice_channels = len(server.voice_channels)
        server_info = f"サーバー名: {server.name}\n"
        server_info += f"サーバー ID: {server.id}\n"
        server_info += f"メンバー数: {total_members}\n"
        server_info += f"オンラインメンバー数: {online_members}\n"
        server_info += f"テキストチャンネル数: {text_channels}\n"
        server_info += f"ボイスチャンネル数: {voice_channels}\n"
        await message.channel.send(server_info)

    # ヘルプコマンド
    if message.content == "!help":
        help_message = "コマンドの使い方:\n"
        help_message += "!vote -start: 新しい投票を開始します。\n"
        help_message += "!vote -end <投票番号>: 投票を終了し、結果を表示します。\n"
        help_message += "!task -add <タスクの説明>: 新しいタスクを追加します.\n"
        help_message += "!task -list: 現在のタスクリストを表示します.\n"
        help_message += "!task -remove <タスク番号>: 指定されたタスクを削除します.\n"
        help_message += "!server: サーバーの統計情報を表示します.\n"
        help_message += "!help: このヘルプメッセージを表示します.\n"
        await message.channel.send(help_message)

@client.event
async def on_reaction_add(reaction, user):
    if not user.bot and reaction.message.id in votes:
        vote_data = votes[reaction.message.id]
        if reaction.emoji in vote_data["options"]:
            if user.id not in vote_data["votes"]:
                vote_data["votes"][user.id] = reaction.emoji

# Web サーバーの立ち上げ
keep_alive()

client.run(TOKEN)
