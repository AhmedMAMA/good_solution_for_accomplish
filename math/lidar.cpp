#include <SoftwareSerial.h>

// A0 = RX Arduino, A1 = TX Arduino
SoftwareSerial lidar(A0, A1);

int dist;
int strength;
float temperature;
int check;
int uart[9];

const int HEADER = 0x59;

void setup()
{
  Serial.begin(9600);     // Moniteur série PC
  lidar.begin(115200);    // LiDAR

  Serial.println("Lecture distance LiDAR...");
}

void loop()
{
  if (lidar.available() >= 9)
  {
    if (lidar.read() == HEADER)
    {
      uart[0] = HEADER;

      if (lidar.read() == HEADER)
      {
        uart[1] = HEADER;

        for (int i = 2; i < 9; i++)
        {
          uart[i] = lidar.read();
        }

        check = 0;
        for (int i = 0; i < 8; i++)
        {
          check += uart[i];
        }

        if (uart[8] == (check & 0xFF))
        {
          dist = uart[2] + uart[3] * 256;
          strength = uart[4] + uart[5] * 256;

          temperature = uart[6] + uart[7] * 256;
          temperature = temperature / 8 - 256;

          Serial.print("Distance = ");
          Serial.print(dist);
          Serial.print(" cm");

          Serial.print("\tSignal = ");
          Serial.print(strength);

          Serial.print("\tTemperature = ");
          Serial.print(temperature);
          Serial.println(" °C");
        }
      }
    }
  }
}