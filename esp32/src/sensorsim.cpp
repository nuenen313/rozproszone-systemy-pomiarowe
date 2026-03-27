#include <Arduino.h>
#include "sensorsim.h"
#include <math.h>

extern "C" uint8_t temprature_sens_read();
// #TODO: add some noise to the measurements

float sinsim(float avr, float ampl, float period) {
    return avr + ampl * sin(2 * PI * millis() * 0.001/ period);
}

float getSimAzimuth() {
    return sinsim(180, 180, 30);
}

float getSimTemperature() {
    return sinsim(20, 10, 60);
}

float getSimHumidity() {
    return sinsim(50, 20, 45);
}

float getRealCoreTemperature() {
    return (temprature_sens_read() - 32) / 1.8;
}