use serenity::{
    async_trait,
    model::{
        channel::{Message, ReactionType},
        event::ReactionAddEvent,
        gateway::Ready,
        id::EmojiId, prelude::Reaction,
    },
    prelude::*,
};

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, _: Context, ready: Ready) {
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
    dotenvy::dotenv().ok();
    let token = std::env::var("DISCORD_TOKEN").expect("TOKENを指定してください");

    let mut client = Client::builder(&token, get_intents())
        .event_handler(Handler)
        .await
        .expect("Error creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
