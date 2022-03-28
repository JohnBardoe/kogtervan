import subprocess
from time import sleep

cmd = "python3 -u bot.py".split() #-u needed because of Python's output buffering

#run the bot and wait for output
def run_bot():
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        line = p.stdout.readline()
        if "Started" in line.decode("utf-8") and p.poll() is None:
            print("Bot started")
            exit(0)
        elif p.poll() is not None:
            print("Bot failed to start:", p.stderr.read().decode("utf-8"))
            exit(1)
        sleep(1)

if __name__ == "__main__":
    run_bot()
