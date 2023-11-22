use serenity::{
    async_trait,
    model::{
        channel::{Message, ReactionType},
        event::ReactionAddEvent,
        gateway::Ready,
        id::{EmojiId, UserId},
        prelude::Reaction,
    },
    prelude::*,
};
use std::collections::HashMap;

struct Handler {
    active_votes: HashMap<String, u64>,
    task_list: Vec<String>,
}

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: Ready) {
        println!("Logged in as {}", ready.user.name);
    }

    async fn reaction_add(&self, ctx: Context, reaction: Reaction) {
        if reaction.user_id.unwrap() != ctx.cache.current_user_id() {
            return;
        }

        // Check if the reacted message contains "Statify"
        if let Ok(message) = reaction.message(&ctx.http).await {
            if message.content.contains("Statify") {
                // React with a heart emoji
                message
                    .react(&ctx.http, ReactionType::Unicode("❤".to_string()))
                    .await
                    .ok();
            }
        }
    }

    async fn message(&self, ctx: Context, msg: Message) {
        if msg.author.bot {
            return;
        }

        // Parse commands
        if msg.content.starts_with('!') {
            let content = msg.content.trim();
            let mut args = content.splitn(3, ' ');
            let command = args.next().unwrap_or_default();

            match command {
                "!vote" => {
                    // Handle vote commands
                    if let Some(subcommand) = args.next() {
                        match subcommand {
                            "-start" => {
                                // Start a new vote
                                let vote_id = format!("{}-{}", msg.timestamp.timestamp(), self.active_votes.len());
                                self.active_votes.insert(vote_id.clone(), 0);
                                msg.channel_id
                                    .say(&ctx.http, format!("New vote started! Vote ID: {}", vote_id))
                                    .await
                                    .ok();
                            }
                            "-end" => {
                                if let Some(vote_id) = args.next() {
                                    if let Some(vote_count) = self.active_votes.remove(vote_id) {
                                        msg.channel_id
                                            .say(&ctx.http, format!("Vote {} ended! Result: {}", vote_id, vote_count))
                                            .await
                                            .ok();
                                    } else {
                                        msg.channel_id
                                            .say(&ctx.http, "Invalid vote ID")
                                            .await
                                            .ok();
                                    }
                                } else {
                                    msg.channel_id
                                        .say(&ctx.http, "Please provide a vote ID to end the vote")
                                        .await
                                        .ok();
                                }
                            }
                            _ => {
                                msg.channel_id
                                    .say(&ctx.http, "Invalid vote command")
                                    .await
                                    .ok();
                            }
                        }
                    }
                }
                "!task" => {
                    // Handle task commands
                    if let Some(subcommand) = args.next() {
                        match subcommand {
                            "-add" => {
                                if let Some(task_description) = args.next() {
                                    self.task_list.push(task_description.to_string());
                                    msg.channel_id
                                        .say(&ctx.http, "Task added successfully")
                                        .await
                                        .ok();
                                } else {
                                    msg.channel_id
                                        .say(&ctx.http, "Please provide a task description")
                                        .await
                                        .ok();
                                }
                            }
                            "-list" => {
                                if !self.task_list.is_empty() {
                                    let mut list = String::new();
                                    for (index, task) in self.task_list.iter().enumerate() {
                                        list.push_str(&format!("{}. {}\n", index + 1, task));
                                    }
                                    msg.channel_id
                                        .say(&ctx.http, format!("Current tasks:\n{}", list))
                                        .await
                                        .ok();
                                } else {
                                    msg.channel_id
                                        .say(&ctx.http, "Task list is empty")
                                        .await
                                        .ok();
                                }
                            }
                            "-remove" => {
                                if let Some(task_index) = args.next() {
                                    if let Ok(index) = task_index.parse::<usize>() {
                                        if index > 0 && index <= self.task_list.len() {
                                            self.task_list.remove(index - 1);
                                            msg.channel_id
                                                .say(&ctx.http, "Task removed successfully")
                                                .await
                                                .ok();
                                        } else {
                                            msg.channel_id
                                                .say(&ctx.http, "Invalid task number")
                                                .await
                                                .ok();
                                        }
                                    } else {
                                        msg.channel_id
                                            .say(&ctx.http, "Invalid task number")
                                            .await
                                            .ok();
                                    }
                                } else {
                                    msg.channel_id
                                        .say(&ctx.http, "Please provide a task number to remove")
                                        .await
                                        .ok();
                                }
                            }
                            _ => {
                                msg.channel_id
                                    .say(&ctx.http, "Invalid task command")
                                    .await
                                    .ok();
                            }
                        }
                    }
                }
                "!server" => {
                    if let Some(guild_id) = msg.guild_id {
                        if let Ok(guild) = guild_id.to_partial_guild(&ctx.http).await {
                            let members = guild.members(&ctx.http).await.ok().unwrap().len();
                            let channels = guild.channels(&ctx.http).await.ok().unwrap().len();
                            let owner = guild.owner_id;

                            msg.channel_id
                                .say(
                                    &ctx.http,
                                    format!(
                                        "Server Statistics:\nMembers: {}\nChannels: {}\nOwner: {}",
                                        members,
                                        channels,
                                        owner.mention()
                                    ),
                                )
                                .await
                                .ok();
                        }
                    }
                }
                "!help" => {
                    // Handle help command
                    // Display a help message with available commands
                    let help_msg = "Available commands:\n\
                                    !vote -start: Start a new vote\n\
                                    !vote -end <vote_id>: End a vote and display results\n\
                                    !task -add <task_description>: Add a new task\n\
                                    !task -list: Display current task list\n\
                                    !task -remove <task_number>: Remove a task\n\
                                    !server: Display server statistics\n\
                                    !help: Display this help message";
                    msg.channel_id.say(&ctx.http, help_msg).await.ok();
                }
                _ => {}
            }
        }
    }
}

#[inline]
fn get_intents() -> GatewayIntents {
    let mut intents = GatewayIntents::empty();
    intents.insert(GatewayIntents::GUILDS);
    intents.insert(GatewayIntents::GUILD_MESSAGES);
    intents.insert(GatewayIntents::MESSAGE_CONTENT);
    intents.insert(GatewayIntents::DIRECT_MESSAGES);
    intents.insert(GatewayIntents::DIRECT_MESSAGE_REACTIONS);
    intents
}

#[tokio::main]
async fn main() {
    dotenv::dotenv().ok();
    let token = std::env::var("DISCORD_TOKEN").expect("Please specify a token");

    let handler = Handler {
        active_votes: HashMap::new(),
        task_list: Vec::new(),
    };

    let mut client = Client::builder(&token)
        .event_handler(handler)
        .await
        .expect("Error creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
