#include <M5Unified.h>

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);

  M5.Display.setRotation(1);
  M5.Display.setTextSize(2);
  M5.Display.println("Core2 ready");
}

void loop() {
  M5.update();   // call every loop iteration; drives touch/button state

  auto t = M5.Touch.getDetail();
  if (t.wasPressed()) {
    M5.Display.printf("Touch: %d,%d\n", t.x, t.y);
  }
}
