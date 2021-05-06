import sys
import unittest


class TestPumpBase(unittest.TestCase):
    SERIAL_PORT = "COM3"

    def test_open(self) -> None:

        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        TestPumpBase.SERIAL_PORT = sys.argv.pop()
    unittest.main()
