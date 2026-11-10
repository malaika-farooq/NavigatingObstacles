"""Confirmed wiring only; paper-design geometry is not calibration."""

COLOR_PORT = "1"  # User correction, November 10, 2026; verified on brick.
# Bench reference measured with the mounted sensor over the white tabletop.
COLOR_WHITE_REFLECTION_PCT = 50.8
COLOR_WHITE_RGB = (224.25, 216.45, 144.25)
FAN_PORT = "D"
FAN_ENABLED = False  # Explicit user hold: wait for permission to run the fan.

# User confirmed input 4 is the front bumper.
# Other motor/sensor assignments must be confirmed before behavior integration.
BUMPER_PORT = "4"
FEELER_PORT = None
ULTRASONIC_PORT = "3"
LEFT_MOTOR_PORT = None
RIGHT_MOTOR_PORT = None
WHEEL_DIAMETER_M = 0.056  # Nominal kit dimension, not rolling calibration.
TRACK_WIDTH_M = None

SAMPLE_INTERVAL_S = 0.1
SAMPLE_COUNT = 100
