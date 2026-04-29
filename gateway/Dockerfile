FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /workspace

COPY . .
RUN mvn clean package -DskipTests -q

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

COPY --from=build /workspace/gateway-server/target/gateway-server-*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
