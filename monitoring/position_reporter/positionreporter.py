import sys
from monitoring.position_reporter import webapp


def main(argv):
    del argv
    webapp.setup()
    webapp.run(host="localhost", port=5000)


if __name__ == "__main__":
    main(sys.argv)
