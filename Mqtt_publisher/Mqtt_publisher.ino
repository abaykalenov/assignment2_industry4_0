#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

const char* ssid = "#";
const char* password = "11110000";

const char* mqtt_server = "147.30.56.87";
const int   mqtt_port   = 1883;            
const char* mqtt_user   = "alyabe";
const char* mqtt_pass   = "abai0405";
const char* topic       = "sensor/data";  


#define DHTPIN 4        
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

#define MQ135_PIN 34   


WiFiClient espClient;
PubSubClient client(espClient);


void setup_wifi() {
  delay(100);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  pinMode(MQ135_PIN, INPUT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int mq135_raw = analogRead(MQ135_PIN);


  float co2_ppm = map(mq135_raw, 0, 4095, 400, 5000);

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  char msg[100];
  snprintf(msg, sizeof(msg), "(%.2f, %.2f, %.2f)", temperature, humidity, co2_ppm);

  if (client.publish(topic, msg)) {
    Serial.print("Data published: ");
    Serial.println(msg);
  } else {
    Serial.println("MQTT publish failed");
  }

  delay(3000);  

}  
