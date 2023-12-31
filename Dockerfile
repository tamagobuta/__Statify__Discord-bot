FROM rust:1.55.0 as builder
# ★1.a
#RUN USER=root cargo new --bin app
WORKDIR /app

# Install dependencies first for cache ★1.b
COPY ./Cargo.lock ./Cargo.lock
COPY ./Cargo.toml ./Cargo.toml
COPY ./src ./src
RUN rustup component add rustfmt
RUN cargo build --release
RUN rm src/*.rs

# Build my app ★1.c
#COPY ./proto ./proto
# ★2.b
#RUN cargo install --locked --path .

# ★2.a
FROM debian:buster-slim
RUN apt-get update && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/cargo/bin/identity .
CMD ["./identity"]