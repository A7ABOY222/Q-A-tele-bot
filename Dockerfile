FROM eclipse-temurin:21-jre-jammy

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /minecraft

# Download Paper MC 1.21.4 (build 232, latest stable)
RUN curl -fSL \
  "https://fill-data.papermc.io/v1/objects/5ee4f542f628a14c644410b08c94ea42e772ef4d29fe92973636b6813d4eaffc/paper-1.21.4-232.jar" \
  -o paper.jar

# Accept EULA
RUN echo "eula=true" > eula.txt

# Copy server config
COPY server.properties server.properties
COPY start.sh start.sh
RUN chmod +x start.sh

# Minecraft port
EXPOSE 25565

ENTRYPOINT ["./start.sh"]
