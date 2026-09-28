#include <M5Unified.h>

void setup() {
    M5.begin();
    M5.Display.println("hello");
}

void loop() {
    M5.update();
}
