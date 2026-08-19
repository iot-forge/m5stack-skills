# Units catalog

Peripheral/accessory boards that plug into a Controller (I2C, GPIO, or Grove)
rather than running their own application — see the `new-device-skill` skill
in `.claude/skills/` for how these skills differ from Controller skills
(lighter: usually just one `SKILL.md`).

Seeded from the docs.m5stack.com product index, August 2026, grouped by
family. **This category is the least complete of the three catalogs** — the
Wireless subcategory in particular was cut off mid-list during the seed
research pass, and 150+ SKUs across categories this size are unlikely to all
be captured perfectly on a first pass. Treat every row as provisional; add
missing units and fix groupings as they come up, especially whenever a user
asks about a specific unit that isn't listed here yet.

No Unit skills exist yet, so no `units` plugin exists either — the first one
built will need a new plugin entry in `.claude-plugin/marketplace.json`.

## Sensor

| Family | Includes | Status | Skill |
|---|---|---|---|
| Fingerprint2 | — | not started | |
| MQ | gas sensor | not started | |
| INA226 | 10A, 1A | not started | |
| Gateway H2 | — | not started | |
| ASR | speech recognition | not started | |
| Ultrasonic | I2C, IO | not started | |
| ToF | — | not started | |
| ToF4M | — | not started | |
| Mini ToF-90° | — | not started | |
| Limit | — | not started | |
| PIR | — | not started | |
| TMOS PIR | — | not started | |
| OP90 / OP180 | — | not started | |
| Weight | — | not started | |
| Weight-I2C | — | not started | |
| Mini Scales | — | not started | |
| Scales | — | not started | |
| Gesture | — | not started | |
| Color | — | not started | |
| Thermal | incl. Thermal2 | not started | |
| NCIR | incl. NCIR2 | not started | |
| Light | incl. DLight | not started | |
| AMeter / VMeter | — | not started | |
| Heart | — | not started | |
| Finger | — | not started | |
| Mini IMU | — | not started | |
| Accel | — | not started | |
| ENV | III, Pro | not started | |
| CO2 | incl. CO2L | not started | |
| Mini TVOC/eCO2 | — | not started | |
| Earth | — | not started | |
| Watering | — | not started | |
| Tube Pressure | — | not started | |
| Hall | — | not started | |
| MIC | incl. Mini PDM | not started | |
| Mini BPS | v1.1 | not started | |
| KMeter-ISO | — | not started | |
| AIN4-20mA | — | not started | |
| AC Measure | — | not started | |
| Reflective IR | — | not started | |
| Grove to Grove | — | not started | |
| ExtEncoder | — | not started | |
| ADC | v1.1 | not started | |
| DAC2 | — | not started | |

## Actuator

| Family | Includes | Status | Skill |
|---|---|---|---|
| Buzzer | — | not started | |
| Vibrator | — | not started | |
| Fan | — | not started | |
| FlashLight | — | not started | |
| Roller485 | incl. Lite | not started | |
| RollerCAN | incl. Lite | not started | |
| 4Relay | — | not started | |
| 2Relay | — | not started | |
| Relay | — | not started | |
| SSR | incl. ACSSR, DCSSR | not started | |
| DDS | — | not started | |
| IR | transmit | not started | |
| RF433 | T, R | not started | |
| Laser | RX, TX | not started | |

## Extension

| Family | Includes | Status | Skill |
|---|---|---|---|
| ChainBus | — | not started | |
| Mini CAN | — | not started | |
| EXT.IO2 | — | not started | |
| Hub | — | not started | |
| PaHub | v2.0, v2.1 | not started | |
| PbHub | v1.1 | not started | |
| 3.96 | — | not started | |
| TypeC to Grove | — | not started | |
| RS485 | incl. ISO | not started | |
| CAN | — | not started | |
| DMX | — | not started | |

## Driver

| Family | Includes | Status | Skill |
|---|---|---|---|
| HBridge | v1.1 | not started | |
| 8Servos | — | not started | |
| BLDC Driver | — | not started | |

## HMI

| Family | Includes | Status | Skill |
|---|---|---|---|
| CardKB | incl. CardKB2, v1.1 | not started | |
| Step16 | — | not started | |
| OLED | incl. Mini OLED | not started | |
| LCD | — | not started | |
| DigiClock | — | not started | |
| Glass | incl. Glass2 | not started | |
| RGB | incl. RGB LED, RGB LED Strip | not started | |
| NeoHEX / HEX | — | not started | |
| Neco | — | not started | |
| Scroll | — | not started | |
| Joystick2 | v1.1 | not started | |
| Puzzle | — | not started | |
| Angle | incl. 8Angle | not started | |
| Encoder | incl. 8Encoder | not started | |
| Fader | — | not started | |
| Key | — | not started | |
| Button | incl. Dual Button | not started | |
| ByteButton | — | not started | |
| ByteSwitch | — | not started | |

## Audio

| Family | Includes | Status | Skill |
|---|---|---|---|
| Synth | — | not started | |
| AudioPlayer | — | not started | |
| MIDI | — | not started | |
| RCA | — | not started | |

## Cameras

| Family | Includes | Status | Skill |
|---|---|---|---|
| TimerCamera | X, F | not started | |
| M5Camera | X, Battery | not started | |
| Unit CamS3-5MP | — | not started | |
| UnitV2 | incl. M12, USB | not started | |
| UnitV | OV7740, M12 | not started | |
| Unit PoE CAM-W | v1.1 | not started | |

## Wireless (incomplete — see note above)

| Family | Includes | Status | Skill |
|---|---|---|---|
| NFC | — | not started | |
| Cat1-CN | — | not started | |
| C6L | — | not started | |
| LoRaWAN | CN470, AS923, EU868 | not started | |

---

**Totals**: ~120 families captured, 0 done. Known incomplete: Wireless.
