import sys
import os
from monitoring.position_reporter import webapp


def main(argv):
    del argv
    port = int(os.environ.get("POS_REP_PORT", "8097"))
    webapp.setup()
    webapp.run(host="localhost", port=port)


if __name__ == "__main__":
    main(sys.argv)
